"""Zero-cost proxy evaluator for MONAS architectures.

This module is a more realistic alternative to ``evaluation.py`` for proof of
concept experiments. It does not train models, but it does instantiate the
candidate architecture in PyTorch and measures:

- real parameter count
- hook-based forward FLOPs
- actual median forward latency on the selected device
- zero-cost quality proxies: NASWOT, SynFlow, and gradient norm

The returned ``accuracy`` field is a calibrated ``accuracy_proxy`` so the rest of
the MONAS objective code can consume it. Treat it as a ranking signal, not a
claim of trained validation accuracy.
"""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import math
import statistics
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .evaluation import ObjectiveWeights, dominates, objective_vector
from .initialization import architecture_signature, get_hardware_profile


MetricDict = Dict[str, float]


def hash_architecture(architecture: Dict[str, Any]) -> str:
    arch_str = repr(architecture_signature(architecture))
    return hashlib.md5(arch_str.encode("utf-8")).hexdigest()


@dataclass
class ZeroCostConfig:
    """Runtime knobs tuned for a laptop demo."""

    device: str = "auto"
    batch_size: int = 4
    latency_warmups: int = 2
    latency_repeats: int = 6
    max_cell_repeats: int = 3
    max_activation_features: int = 4096
    torch_threads: Optional[int] = 4
    input_shape: Tuple[int, int, int] = (3, 32, 32)


def _lazy_torch():
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    return torch, nn, F


def _activation(name: str):
    _, nn, _ = _lazy_torch()
    if name == "gelu":
        return nn.GELU()
    if name == "swish":
        return nn.SiLU(inplace=False)
    return nn.ReLU(inplace=False)


def _conv_bn_act(in_channels: int, out_channels: int, kernel: int, stride: int, activation: str, *, groups: int = 1, dilation: int = 1):
    _, nn, _ = _lazy_torch()
    padding = ((kernel - 1) // 2) * dilation
    return nn.Sequential(
        nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size=kernel,
            stride=stride,
            padding=padding,
            dilation=dilation,
            groups=groups,
            bias=False,
        ),
        nn.BatchNorm2d(out_channels),
        _activation(activation),
    )


def _make_block(layer: Dict[str, Any], in_channels: int):
    torch, nn, _ = _lazy_torch()
    op = layer.get("op", "conv3x3")
    out_channels = max(1, int(layer.get("channels", in_channels)))
    stride = max(1, int(layer.get("stride", 1)))
    repeat = max(1, int(layer.get("repeat", 1)))
    activation = layer.get("activation", "relu")
    blocks = []

    if op == "skip":
        if stride == 1 and in_channels == out_channels:
            blocks.append(nn.Identity())
        else:
            blocks.append(
                nn.Sequential(
                    nn.AvgPool2d(kernel_size=stride, stride=stride) if stride > 1 else nn.Identity(),
                    nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False),
                    nn.BatchNorm2d(out_channels),
                )
            )
    elif op in {"maxpool3x3", "avgpool3x3"}:
        pool = nn.MaxPool2d if op == "maxpool3x3" else nn.AvgPool2d
        blocks.append(
            nn.Sequential(
                pool(kernel_size=3, stride=stride, padding=1),
                nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False),
                nn.BatchNorm2d(out_channels),
                _activation(activation),
            )
        )
    elif op in {"sep_conv3x3", "sep_conv5x5"}:
        kernel = 5 if op.endswith("5x5") else 3
        blocks.append(
            nn.Sequential(
                _conv_bn_act(in_channels, in_channels, kernel, stride, activation, groups=in_channels),
                nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False),
                nn.BatchNorm2d(out_channels),
                _activation(activation),
            )
        )
    elif op == "bottleneck1x1":
        hidden = max(8, min(out_channels, max(in_channels, out_channels) // 2))
        blocks.append(
            nn.Sequential(
                _conv_bn_act(in_channels, hidden, 1, 1, activation),
                _conv_bn_act(hidden, out_channels, 1, stride, activation),
            )
        )
    else:
        kernel = 5 if op == "conv5x5" else 3
        dilation = 2 if op == "dil_conv3x3" else 1
        blocks.append(_conv_bn_act(in_channels, out_channels, kernel, stride, activation, dilation=dilation))

    for _ in range(repeat - 1):
        blocks.append(_conv_bn_act(out_channels, out_channels, 3, 1, activation))

    return nn.Sequential(*blocks), out_channels


class TinyMonasNet:
    """Factory wrapper to keep torch imports lazy."""

    @staticmethod
    def build(architecture: Dict[str, Any], config: ZeroCostConfig):
        _, nn, _ = _lazy_torch()

        class _Net(nn.Module):
            def __init__(self):
                super().__init__()
                input_shape = architecture.get("input_shape", config.input_shape)
                in_channels = int(input_shape[0])
                num_classes = int(architecture.get("num_classes", 10))
                layers = architecture.get("layers", [])
                cells = max(1, min(config.max_cell_repeats, int(architecture.get("cells", 1))))

                modules = []
                for _ in range(cells):
                    for layer in layers:
                        block, in_channels = _make_block(layer, in_channels)
                        modules.append(block)

                self.features = nn.Sequential(*modules)
                self.pool = nn.AdaptiveAvgPool2d(1)
                self.classifier = nn.Linear(in_channels, num_classes)

            def forward(self, x):
                x = self.features(x)
                x = self.pool(x).flatten(1)
                return self.classifier(x)

        return _Net()


@contextmanager
def _temporary_thread_count(thread_count: Optional[int]):
    torch, _, _ = _lazy_torch()
    if thread_count is None:
        yield
        return
    previous = torch.get_num_threads()
    torch.set_num_threads(max(1, int(thread_count)))
    try:
        yield
    finally:
        torch.set_num_threads(previous)


class ZeroCostEvaluator:
    """Evaluate architecture dictionaries with real PyTorch proxy measurements."""

    def __init__(self, hardware: Optional[str] = "cpu", config: Optional[ZeroCostConfig] = None):
        self.hardware = hardware or "cpu"
        self.profile = get_hardware_profile(hardware)
        self.config = config or ZeroCostConfig()
        self.cache: Dict[str, Dict[str, Any]] = {}

    def evaluate_architecture(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        arch_key = hash_architecture(architecture)
        if arch_key in self.cache:
            return deepcopy(self.cache[arch_key])

        torch, _, _ = _lazy_torch()
        device = self._resolve_device(torch)
        with _temporary_thread_count(self.config.torch_threads):
            torch.manual_seed(int(arch_key[:8], 16) % 2_147_483_647)
            model = TinyMonasNet.build(architecture, self.config).to(device)
            input_shape = tuple(architecture.get("input_shape", self.config.input_shape))
            dummy = torch.randn(self.config.batch_size, *input_shape, device=device)
            targets = torch.arange(self.config.batch_size, device=device) % int(architecture.get("num_classes", 10))

            params_m = count_parameters_m(model)
            flops_m = measure_flops_m(model, dummy)
            latency_ms = measure_latency_ms(
                model,
                dummy,
                warmups=self.config.latency_warmups,
                repeats=self.config.latency_repeats,
                device=device,
            )
            proxies = measure_zero_cost_proxies(model, dummy, targets, self.config)
            accuracy_proxy = calibrate_accuracy_proxy(proxies)

        result: Dict[str, Any] = {
            "accuracy": round(accuracy_proxy, 6),
            "accuracy_proxy": round(accuracy_proxy, 6),
            "latency": round(latency_ms, 4),
            "params": round(params_m, 4),
            "flops": round(flops_m, 4),
            "zero_cost": {key: round(float(value), 6) for key, value in proxies.items()},
            "evaluation_mode": "zero_cost_proxy",
            "device": str(device),
        }
        self.cache[arch_key] = deepcopy(result)
        return result

    def _resolve_device(self, torch):
        requested = (self.config.device or "auto").lower()
        if requested == "auto":
            requested = "cuda" if torch.cuda.is_available() else "cpu"
        if requested == "cuda" and not torch.cuda.is_available():
            requested = "cpu"
        return torch.device(requested)

    def constraint_violations(
        self,
        metrics: Dict[str, Any],
        hardware_constraints: Optional[Dict[str, float]] = None,
    ) -> Dict[str, float]:
        constraints = dict(self.profile)
        if hardware_constraints:
            constraints.update({k: v for k, v in hardware_constraints.items() if v not in (None, "")})

        violations = {}
        for metric, constraint_key in (
            ("flops", "max_flops"),
            ("params", "max_params"),
            ("latency", "max_latency"),
        ):
            limit = constraints.get(constraint_key)
            if limit is None:
                continue
            overage = max(0.0, float(metrics[metric]) - float(limit))
            if overage > 0:
                violations[metric] = overage
        return violations

    def compute_fitness(
        self,
        metrics: Dict[str, Any],
        objectives: Optional[Dict[str, float]] = None,
        hardware_constraints: Optional[Dict[str, float]] = None,
    ) -> float:
        weights = ObjectiveWeights.from_mapping(objectives).as_dict() if objectives else ObjectiveWeights().as_dict()
        profile = dict(self.profile)
        if hardware_constraints:
            profile.update({k: v for k, v in hardware_constraints.items() if v not in (None, "")})

        accuracy_score = float(metrics["accuracy_proxy"])
        latency_score = 1.0 / (1.0 + float(metrics["latency"]) / max(1.0, float(profile["max_latency"])))
        params_score = 1.0 / (1.0 + float(metrics["params"]) / max(0.1, float(profile["max_params"])))
        flops_score = 1.0 / (1.0 + float(metrics["flops"]) / max(1.0, float(profile["max_flops"])))

        score = (
            weights["accuracy"] * accuracy_score
            + weights["latency"] * latency_score
            + weights["params"] * params_score
            + weights["flops"] * flops_score
        )

        violations = self.constraint_violations(metrics, hardware_constraints)
        if violations:
            score -= sum(violations.values()) / 1000.0
        return round(score, 6)


def count_parameters_m(model) -> float:
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad) / 1_000_000


def measure_flops_m(model, dummy_input) -> float:
    torch, nn, _ = _lazy_torch()
    total_flops = 0.0
    hooks = []

    def conv_hook(module, inputs, output):
        nonlocal total_flops
        batch = output.shape[0]
        out_channels = output.shape[1]
        out_h = output.shape[2]
        out_w = output.shape[3]
        kernel_h, kernel_w = module.kernel_size
        in_channels = module.in_channels
        groups = module.groups
        total_flops += batch * out_channels * out_h * out_w * (in_channels / groups) * kernel_h * kernel_w * 2

    def linear_hook(module, inputs, output):
        nonlocal total_flops
        batch = output.shape[0] if output.dim() > 1 else 1
        total_flops += batch * module.in_features * module.out_features * 2

    def batchnorm_hook(module, inputs, output):
        nonlocal total_flops
        total_flops += output.numel() * 2

    for module in model.modules():
        if isinstance(module, nn.Conv2d):
            hooks.append(module.register_forward_hook(conv_hook))
        elif isinstance(module, nn.Linear):
            hooks.append(module.register_forward_hook(linear_hook))
        elif isinstance(module, (nn.BatchNorm1d, nn.BatchNorm2d)):
            hooks.append(module.register_forward_hook(batchnorm_hook))

    model.eval()
    with torch.no_grad():
        model(dummy_input)

    for hook in hooks:
        hook.remove()
    return float(total_flops / 1_000_000)


def measure_latency_ms(model, dummy_input, *, warmups: int, repeats: int, device) -> float:
    torch, _, _ = _lazy_torch()
    model.eval()

    with torch.no_grad():
        for _ in range(max(0, warmups)):
            model(dummy_input)
        if device.type == "cuda":
            torch.cuda.synchronize()

        timings = []
        for _ in range(max(1, repeats)):
            start = time.perf_counter()
            model(dummy_input)
            if device.type == "cuda":
                torch.cuda.synchronize()
            timings.append((time.perf_counter() - start) * 1000.0)

    return float(statistics.median(timings))


def measure_zero_cost_proxies(model, dummy_input, targets, config: ZeroCostConfig) -> Dict[str, float]:
    return {
        "naswot": naswot_score(model, dummy_input, config.max_activation_features),
        "synflow": synflow_score(model, tuple(dummy_input.shape)),
        "grad_norm": grad_norm_score(model, dummy_input, targets),
    }


def naswot_score(model, dummy_input, max_features: int) -> float:
    torch, nn, _ = _lazy_torch()
    activations = []
    hooks = []

    def hook(_, __, output):
        if output.dim() < 2:
            return
        flat = (output.detach() > 0).flatten(1).float()
        if flat.shape[1] > max_features:
            step = max(1, flat.shape[1] // max_features)
            flat = flat[:, ::step][:, :max_features]
        activations.append(flat.cpu())

    for module in model.modules():
        if isinstance(module, (nn.ReLU, nn.GELU, nn.SiLU)):
            hooks.append(module.register_forward_hook(hook))

    model.eval()
    with torch.no_grad():
        model(dummy_input)

    for registered_hook in hooks:
        registered_hook.remove()

    if not activations:
        return 0.0

    binary = torch.cat(activations, dim=1)
    if binary.shape[1] > max_features:
        binary = binary[:, :max_features]
    kernel = binary @ binary.t() + (1.0 - binary) @ (1.0 - binary).t()
    kernel = kernel + torch.eye(kernel.shape[0]) * 1e-6
    sign, logdet = torch.linalg.slogdet(kernel)
    if sign <= 0:
        return 0.0
    return float(logdet.item())


def synflow_score(model, input_shape: Tuple[int, ...]) -> float:
    torch, _, _ = _lazy_torch()
    signs = {}

    model.zero_grad(set_to_none=True)
    model.eval()
    for name, parameter in model.named_parameters():
        signs[name] = torch.sign(parameter.data)
        parameter.data.abs_()

    ones = torch.ones(input_shape, device=next(model.parameters()).device)
    output = model(ones)
    torch.sum(output).backward()

    score = 0.0
    for name, parameter in model.named_parameters():
        if parameter.grad is not None:
            score += torch.sum(torch.abs(parameter.grad * parameter)).item()
        parameter.data.mul_(signs[name])

    model.zero_grad(set_to_none=True)
    return float(score)


def grad_norm_score(model, dummy_input, targets) -> float:
    torch, _, F = _lazy_torch()
    model.zero_grad(set_to_none=True)
    model.train()
    logits = model(dummy_input)
    loss = F.cross_entropy(logits, targets)
    loss.backward()
    score = 0.0
    for parameter in model.parameters():
        if parameter.grad is not None:
            score += torch.linalg.vector_norm(parameter.grad.detach()).item()
    model.zero_grad(set_to_none=True)
    return float(score)


def calibrate_accuracy_proxy(proxies: Dict[str, float]) -> float:
    """Map zero-cost values to a frontend-compatible 0-1 ranking score."""

    naswot = math.tanh(math.log1p(max(0.0, proxies.get("naswot", 0.0))) / 6.0)
    synflow = math.tanh(math.log10(1.0 + max(0.0, proxies.get("synflow", 0.0))) / 8.0)
    grad_norm = math.tanh(math.log10(1.0 + max(0.0, proxies.get("grad_norm", 0.0))) / 3.0)
    proxy_quality = 0.45 * naswot + 0.35 * synflow + 0.20 * grad_norm
    return max(0.50, min(0.985, 0.50 + 0.45 * proxy_quality))


def pareto_mask(items: Iterable[Dict[str, Any]]) -> List[bool]:
    population = list(items)
    mask = []
    for idx, candidate in enumerate(population):
        dominated = False
        for jdx, other in enumerate(population):
            if idx == jdx:
                continue
            if dominates(other["metrics"], candidate["metrics"]):
                dominated = True
                break
        mask.append(not dominated)
    return mask


def evaluate_population(
    architectures: Iterable[Dict[str, Any]],
    *,
    hardware: Optional[str] = "cpu",
    config: Optional[ZeroCostConfig] = None,
) -> List[Dict[str, Any]]:
    evaluator = ZeroCostEvaluator(hardware=hardware, config=config)
    results = []
    for architecture in architectures:
        metrics = evaluator.evaluate_architecture(architecture)
        results.append({"architecture": architecture, "metrics": metrics})
    return results


def objective_vector_zero_cost(metrics: Dict[str, Any]) -> tuple:
    return objective_vector(metrics)

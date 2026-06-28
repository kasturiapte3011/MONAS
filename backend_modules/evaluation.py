"""Multi-objective architecture evaluation.

The evaluator provides deterministic surrogate metrics for accuracy, latency, parameter count, and FLOPs. That keeps the search fast and runnable in a local demo while preserving the objective directions used by a real NASBench-backed evaluator.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Any, Dict, Iterable, List, Optional

from .initialization import OPERATION_SPECS, architecture_signature, get_hardware_profile


MetricDict = Dict[str, float]


def hash_architecture(architecture: Dict[str, Any]) -> str:
    arch_str = repr(architecture_signature(architecture))
    return hashlib.md5(arch_str.encode("utf-8")).hexdigest()


def _stable_noise(key: str, scale: float) -> float:
    raw = int(hashlib.sha1(key.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF
    return (raw - 0.5) * scale


@dataclass
class ObjectiveWeights:
    accuracy: float = 0.5
    latency: float = 0.2
    params: float = 0.15
    flops: float = 0.15

    @classmethod
    def from_name(cls, objective: Optional[str]) -> "ObjectiveWeights":
        objective = (objective or "balanced").lower()
        if objective == "accuracy":
            return cls(accuracy=0.72, latency=0.10, params=0.08, flops=0.10)
        if objective == "efficiency":
            return cls(accuracy=0.34, latency=0.22, params=0.17, flops=0.27)
        if objective == "latency":
            return cls(accuracy=0.32, latency=0.42, params=0.10, flops=0.16)
        if objective == "size":
            return cls(accuracy=0.30, latency=0.16, params=0.38, flops=0.16)
        return cls()

    @classmethod
    def from_mapping(cls, values: Optional[Dict[str, float]]) -> "ObjectiveWeights":
        if not values:
            return cls()
        weights = cls()
        for key in ("accuracy", "latency", "params", "flops"):
            if key in values:
                setattr(weights, key, max(0.0, float(values[key])))
        return weights.normalized()

    def normalized(self) -> "ObjectiveWeights":
        total = self.accuracy + self.latency + self.params + self.flops
        if total <= 0:
            return ObjectiveWeights()
        return ObjectiveWeights(
            accuracy=self.accuracy / total,
            latency=self.latency / total,
            params=self.params / total,
            flops=self.flops / total,
        )

    def as_dict(self) -> Dict[str, float]:
        normalized = self.normalized()
        return {
            "accuracy": normalized.accuracy,
            "latency": normalized.latency,
            "params": normalized.params,
            "flops": normalized.flops,
        }


class SurrogateEvaluator:
    """GA-friendly deterministic architecture evaluator."""

    def __init__(self, hardware: Optional[str] = "gpu"):
        self.hardware = hardware
        self.profile = get_hardware_profile(hardware)
        self.cache: Dict[str, MetricDict] = {}

    def evaluate_architecture(self, architecture: Dict[str, Any]) -> MetricDict:
        arch_key = hash_architecture(architecture)
        if arch_key in self.cache:
            return dict(self.cache[arch_key])

        metrics = self._estimate_metrics(architecture, arch_key)
        self.cache[arch_key] = metrics
        return dict(metrics)

    def _estimate_metrics(self, architecture: Dict[str, Any], arch_key: str) -> MetricDict:
        input_channels, resolution, _ = architecture.get("input_shape", [3, 32, 32])
        spatial = float(resolution)
        in_channels = int(input_channels)

        params_m = 0.0
        flops_m = 0.0
        op_accuracy = 0.0
        skip_count = 0
        downsample_count = 0
        activation_bonus = 0.0

        for layer in architecture.get("layers", []):
            op = layer.get("op", "conv3x3")
            spec = OPERATION_SPECS.get(op, OPERATION_SPECS["conv3x3"])
            out_channels = max(1, int(layer.get("channels", in_channels)))
            repeat = max(1, int(layer.get("repeat", 1)))
            stride = max(1, int(layer.get("stride", 1)))

            kernel = spec["kernel"]
            base_params = in_channels * out_channels * kernel * kernel / 1_000_000
            base_flops = spatial * spatial * in_channels * out_channels * kernel * kernel / 1_000_000

            params_m += base_params * spec["param_factor"] * repeat
            flops_m += base_flops * spec["flop_factor"] * repeat
            op_accuracy += spec["accuracy"] * math.sqrt(repeat)

            if op == "skip":
                skip_count += 1
            if stride > 1:
                downsample_count += 1
                spatial = max(4.0, spatial / stride)

            activation = layer.get("activation", "relu")
            if activation == "swish":
                activation_bonus += 0.0025
            elif activation == "gelu":
                activation_bonus += 0.0018

            in_channels = out_channels

        class_head_params = in_channels * int(architecture.get("num_classes", 10)) / 1_000_000
        params_m += class_head_params

        connection_count = len(architecture.get("connections", []))
        layer_count = len(architecture.get("layers", []))
        cells = int(architecture.get("cells", 1))

        params_m = max(0.01, params_m * cells)
        flops_m = max(1.0, flops_m * cells)

        depth_term = 0.10 * (1.0 - math.exp(-layer_count / 8.0))
        width_term = 0.06 * (1.0 - math.exp(-max(1, in_channels) / 96.0))
        connection_term = min(0.035, 0.004 * skip_count + 0.0015 * connection_count)
        compute_term = 0.07 * (1.0 - math.exp(-flops_m / 260.0))
        oversize_penalty = max(0.0, params_m - self.profile["max_params"] * 1.15) * 0.004
        latency_penalty = max(0.0, flops_m - self.profile["max_flops"] * 1.2) * 0.00008

        accuracy = (
            0.485
            + depth_term
            + width_term
            + min(0.09, op_accuracy / max(1.0, layer_count / 5.0))
            + connection_term
            + compute_term
            + min(0.025, activation_bonus)
            - 0.004 * max(0, downsample_count - 3)
            - oversize_penalty
            - latency_penalty
            + _stable_noise(arch_key, 0.012)
        )
        accuracy = max(0.55, min(0.822, accuracy))

        op_latency_factor = 1.0 + 0.015 * layer_count + 0.010 * connection_count
        latency_ms = (flops_m / max(0.1, self.profile["throughput"])) * op_latency_factor
        latency_ms += params_m * 0.28 + _stable_noise(arch_key + "latency", 1.2)
        latency_ms = max(1.0, latency_ms)

        return {
            "accuracy": round(accuracy, 6),
            "latency": round(latency_ms, 4),
            "params": round(params_m, 4),
            "flops": round(flops_m, 4),
        }

    def constraint_violations(
        self,
        metrics: MetricDict,
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
        metrics: MetricDict,
        objectives: Optional[Dict[str, float]] = None,
        hardware_constraints: Optional[Dict[str, float]] = None,
    ) -> float:
        weights = ObjectiveWeights.from_mapping(objectives).as_dict() if objectives else ObjectiveWeights().as_dict()
        profile = dict(self.profile)
        if hardware_constraints:
            profile.update({k: v for k, v in hardware_constraints.items() if v not in (None, "")})

        accuracy_score = float(metrics["accuracy"])
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
            penalty = sum(violations.values()) / 1000.0
            score -= penalty
        return round(score, 6)


def objective_vector(metrics: MetricDict) -> tuple:
    """Vector minimized by NSGA-II: negative accuracy, latency, params, FLOPs."""

    return (-metrics["accuracy"], metrics["latency"], metrics["params"], metrics["flops"])


def dominates(left: MetricDict, right: MetricDict) -> bool:
    left_vector = objective_vector(left)
    right_vector = objective_vector(right)
    return all(a <= b for a, b in zip(left_vector, right_vector)) and any(
        a < b for a, b in zip(left_vector, right_vector)
    )


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

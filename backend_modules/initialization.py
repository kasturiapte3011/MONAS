"""Population initialization for the MONAS search space.

The search space is intentionally lightweight and deterministic so the API can
run locally without requiring a NASBench data download. NASBench-backed sampling
can still be added behind this module later because the rest of the backend only
depends on the architecture dictionary returned here.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import random
from typing import Any, Dict, Iterable, List, Optional


OPERATION_SPECS: Dict[str, Dict[str, float]] = {
    "conv3x3": {"kernel": 3, "param_factor": 1.0, "flop_factor": 1.0, "accuracy": 0.020},
    "conv5x5": {"kernel": 5, "param_factor": 2.35, "flop_factor": 2.20, "accuracy": 0.026},
    "sep_conv3x3": {"kernel": 3, "param_factor": 0.28, "flop_factor": 0.32, "accuracy": 0.018},
    "sep_conv5x5": {"kernel": 5, "param_factor": 0.42, "flop_factor": 0.50, "accuracy": 0.021},
    "dil_conv3x3": {"kernel": 3, "param_factor": 1.15, "flop_factor": 1.08, "accuracy": 0.023},
    "bottleneck1x1": {"kernel": 1, "param_factor": 0.45, "flop_factor": 0.40, "accuracy": 0.014},
    "maxpool3x3": {"kernel": 3, "param_factor": 0.03, "flop_factor": 0.08, "accuracy": 0.009},
    "avgpool3x3": {"kernel": 3, "param_factor": 0.03, "flop_factor": 0.07, "accuracy": 0.008},
    "skip": {"kernel": 1, "param_factor": 0.02, "flop_factor": 0.02, "accuracy": 0.006},
}

CHANNEL_OPTIONS = [16, 24, 32, 48, 64, 80, 96, 128, 160, 192]
REPEAT_OPTIONS = [1, 2, 3]
STRIDE_OPTIONS = [1, 1, 1, 2]
ACTIVATIONS = ["relu", "gelu", "swish"]


HARDWARE_PROFILES: Dict[str, Dict[str, Any]] = {
    "mobile": {
        "label": "Mobile (ARM)",
        "max_flops": 180.0,
        "max_params": 6.0,
        "max_latency": 60.0,
        "throughput": 4.8,
        "allowed_ops": ["sep_conv3x3", "sep_conv5x5", "bottleneck1x1", "avgpool3x3", "skip"],
    },
    "edge_cpu": {
        "label": "Edge CPU",
        "max_flops": 420.0,
        "max_params": 14.0,
        "max_latency": 95.0,
        "throughput": 7.5,
        "allowed_ops": ["conv3x3", "sep_conv3x3", "bottleneck1x1", "maxpool3x3", "avgpool3x3", "skip"],
    },
    "cpu": {
        "label": "CPU",
        "max_flops": 550.0,
        "max_params": 18.0,
        "max_latency": 120.0,
        "throughput": 8.5,
        "allowed_ops": ["conv3x3", "conv5x5", "sep_conv3x3", "bottleneck1x1", "maxpool3x3", "avgpool3x3", "skip"],
    },
    "gpu": {
        "label": "Cloud GPU",
        "max_flops": 1400.0,
        "max_params": 48.0,
        "max_latency": 45.0,
        "throughput": 46.0,
        "allowed_ops": list(OPERATION_SPECS.keys()),
    },
    "raspberry_pi": {
        "label": "Raspberry Pi",
        "max_flops": 95.0,
        "max_params": 4.0,
        "max_latency": 85.0,
        "throughput": 2.2,
        "allowed_ops": ["sep_conv3x3", "bottleneck1x1", "avgpool3x3", "skip"],
    },
}

HARDWARE_ALIASES = {
    "cloud gpu": "gpu",
    "gpu": "gpu",
    "edge cpu": "edge_cpu",
    "cpu": "cpu",
    "mobile": "mobile",
    "mobile (arm)": "mobile",
    "arm": "mobile",
    "raspberry pi": "raspberry_pi",
    "raspberry_pi": "raspberry_pi",
}


@dataclass(frozen=True)
class SearchSpace:
    """Bounded architecture search space used by initialization and mutation."""

    min_layers: int = 5
    max_layers: int = 14
    min_cells: int = 3
    max_cells: int = 6
    input_resolution: int = 32
    input_channels: int = 3
    num_classes: int = 10


def stable_id(payload: Any, prefix: str = "model") -> str:
    digest = hashlib.sha1(repr(payload).encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{digest}"


def normalize_hardware(hardware: Optional[str]) -> str:
    if not hardware:
        return "gpu"
    return HARDWARE_ALIASES.get(str(hardware).strip().lower(), str(hardware).strip().lower())


def get_hardware_profile(hardware: Optional[str]) -> Dict[str, Any]:
    key = normalize_hardware(hardware)
    if key not in HARDWARE_PROFILES:
        key = "gpu"
    profile = deepcopy(HARDWARE_PROFILES[key])
    profile["key"] = key
    return profile


def _rng(seed: Optional[int] = None) -> random.Random:
    return random.Random(seed if seed is not None else random.randrange(1, 10_000_000))


def _choose_operation(rng: random.Random, allowed_ops: Iterable[str], objective: str) -> str:
    ops = list(allowed_ops)
    if not ops:
        ops = list(OPERATION_SPECS.keys())

    efficient_ops = {"sep_conv3x3", "sep_conv5x5", "bottleneck1x1", "avgpool3x3", "skip"}
    accurate_ops = {"conv3x3", "conv5x5", "dil_conv3x3", "sep_conv5x5"}

    weighted = []
    for op in ops:
        weight = 1.0
        if objective in {"efficiency", "latency", "size"} and op in efficient_ops:
            weight += 1.4
        if objective == "accuracy" and op in accurate_ops:
            weight += 1.1
        if objective == "balanced" and op in {"sep_conv3x3", "conv3x3", "bottleneck1x1"}:
            weight += 0.8
        weighted.append(weight)
    return rng.choices(ops, weights=weighted, k=1)[0]


def sample_architecture(
    profile: Optional[Dict[str, Any]] = None,
    *,
    seed: Optional[int] = None,
    objective: str = "balanced",
    search_space: Optional[SearchSpace] = None,
) -> Dict[str, Any]:
    """Sample one architecture as a serializable DAG-like dictionary."""

    profile = profile or get_hardware_profile("gpu")
    space = search_space or SearchSpace()
    rng = _rng(seed)

    objective = objective or "balanced"
    if objective == "efficiency":
        layer_count = rng.randint(space.min_layers, max(space.min_layers + 2, space.max_layers - 4))
    elif objective == "accuracy":
        layer_count = rng.randint(max(space.min_layers + 3, 8), space.max_layers)
    else:
        layer_count = rng.randint(space.min_layers, space.max_layers)

    cells = rng.randint(space.min_cells, space.max_cells)
    allowed_ops = profile.get("allowed_ops", OPERATION_SPECS.keys())

    layers: List[Dict[str, Any]] = []
    current_channels = space.input_channels
    for idx in range(layer_count):
        op = _choose_operation(rng, allowed_ops, objective)
        stride = rng.choice(STRIDE_OPTIONS)
        if idx == 0:
            stride = 1
        if op in {"skip", "maxpool3x3", "avgpool3x3"}:
            out_channels = current_channels
        else:
            out_channels = rng.choice(CHANNEL_OPTIONS)
            if idx > 0 and rng.random() < 0.55:
                out_channels = max(current_channels, out_channels)

        layer = {
            "index": idx,
            "op": op,
            "channels": int(out_channels),
            "stride": int(stride),
            "repeat": int(rng.choice(REPEAT_OPTIONS)),
            "activation": rng.choice(ACTIVATIONS),
        }
        layers.append(layer)
        current_channels = int(out_channels)

    connections = []
    for idx, layer in enumerate(layers):
        connections.append({"from": max(0, idx), "to": idx + 1, "operation": layer["op"]})
        if idx > 1 and rng.random() < 0.35:
            connections.append({"from": rng.randint(0, idx - 1), "to": idx + 1, "operation": "skip"})

    arch = {
        "id": "",
        "cells": cells,
        "layers": layers,
        "connections": connections,
        "input_shape": [space.input_channels, space.input_resolution, space.input_resolution],
        "num_classes": space.num_classes,
    }
    arch["id"] = stable_id(architecture_signature(arch))
    return arch


def architecture_signature(architecture: Dict[str, Any]) -> tuple:
    """Return a stable, hashable signature for caching and model ids."""

    layers = tuple(
        (
            layer["op"],
            int(layer["channels"]),
            int(layer["stride"]),
            int(layer["repeat"]),
            layer.get("activation", "relu"),
        )
        for layer in architecture.get("layers", [])
    )
    connections = tuple(
        (int(conn["from"]), int(conn["to"]), conn["operation"])
        for conn in architecture.get("connections", [])
    )
    return (
        int(architecture.get("cells", 1)),
        tuple(architecture.get("input_shape", [3, 32, 32])),
        int(architecture.get("num_classes", 10)),
        layers,
        connections,
    )


def sample_architectures(
    n_samples: int,
    profile: Optional[Dict[str, Any]] = None,
    *,
    seed: Optional[int] = None,
    objective: str = "balanced",
) -> List[Dict[str, Any]]:
    """Sample a population of architectures."""

    if n_samples <= 0:
        return []

    profile = profile or get_hardware_profile("gpu")
    rng = _rng(seed)
    architectures = []
    seen = set()
    attempts = 0
    max_attempts = n_samples * 30

    while len(architectures) < n_samples and attempts < max_attempts:
        attempts += 1
        arch = sample_architecture(
            profile,
            seed=rng.randrange(1, 1_000_000_000),
            objective=objective,
        )
        signature = architecture_signature(arch)
        if signature in seen:
            continue
        seen.add(signature)
        architectures.append(arch)

    return architectures


def initialize_population(
    hardware: Optional[str],
    n_samples: int = 50,
    *,
    seed: Optional[int] = None,
    objective: str = "balanced",
) -> List[Dict[str, Any]]:
    """Full initialization pipeline wrapper used by the API and GA."""

    profile = get_hardware_profile(hardware)
    return sample_architectures(n_samples, profile, seed=seed, objective=objective)

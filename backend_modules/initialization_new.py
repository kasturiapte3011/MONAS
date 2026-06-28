"""Demo-safe initialization for zero-cost architecture evaluation.

This file intentionally lives beside ``initialization.py`` instead of replacing
it. The regular initializer can continue powering the fast UI demo, while this
module samples slightly smaller architectures that are practical to instantiate
and score with PyTorch zero-cost proxies on a laptop CPU.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

from .initialization import (
    OPERATION_SPECS,
    SearchSpace,
    architecture_signature,
    get_hardware_profile,
    sample_architecture,
    stable_id,
)


ZERO_COST_CHANNEL_OPTIONS = [16, 24, 32, 48, 64]
ZERO_COST_ALLOWED_OPS = [
    "conv3x3",
    "sep_conv3x3",
    "sep_conv5x5",
    "bottleneck1x1",
    "maxpool3x3",
    "avgpool3x3",
    "skip",
]

ZERO_COST_SEARCH_SPACE = SearchSpace(
    min_layers=4,
    max_layers=7,
    min_cells=1,
    max_cells=2,
    input_resolution=32,
    input_channels=3,
    num_classes=10,
)


def get_zero_cost_profile(hardware: Optional[str] = "cpu") -> Dict[str, Any]:
    """Return a profile trimmed for real PyTorch proxy evaluation."""

    profile = get_hardware_profile(hardware)
    profile["allowed_ops"] = [
        op for op in profile.get("allowed_ops", ZERO_COST_ALLOWED_OPS)
        if op in ZERO_COST_ALLOWED_OPS
    ] or list(ZERO_COST_ALLOWED_OPS)
    profile["max_flops"] = min(float(profile.get("max_flops", 220.0)), 220.0)
    profile["max_params"] = min(float(profile.get("max_params", 8.0)), 8.0)
    profile["max_latency"] = float(profile.get("max_latency", 120.0))
    return profile


def make_zero_cost_safe(architecture: Dict[str, Any]) -> Dict[str, Any]:
    """Cap architecture size while preserving the original schema."""

    safe = deepcopy(architecture)
    safe["cells"] = max(1, min(2, int(safe.get("cells", 1))))
    safe["input_shape"] = [3, 32, 32]
    safe["num_classes"] = int(safe.get("num_classes", 10))

    layers = []
    for idx, layer in enumerate(safe.get("layers", [])[: ZERO_COST_SEARCH_SPACE.max_layers]):
        next_layer = deepcopy(layer)
        next_layer["index"] = idx
        next_layer["op"] = next_layer.get("op", "conv3x3")
        if next_layer["op"] not in OPERATION_SPECS:
            next_layer["op"] = "conv3x3"
        next_layer["channels"] = min(
            max(8, int(next_layer.get("channels", 32))),
            ZERO_COST_CHANNEL_OPTIONS[-1],
        )
        next_layer["stride"] = 1 if idx == 0 else max(1, min(2, int(next_layer.get("stride", 1))))
        next_layer["repeat"] = 1
        next_layer["activation"] = next_layer.get("activation", "relu")
        layers.append(next_layer)

    safe["layers"] = layers
    safe["connections"] = [
        {"from": idx, "to": idx + 1, "operation": layer["op"]}
        for idx, layer in enumerate(layers)
    ]
    signature = architecture_signature(safe)
    safe["signature"] = signature
    safe["id"] = stable_id(signature)
    return safe


def sample_zero_cost_architecture(
    hardware: Optional[str] = "cpu",
    *,
    seed: Optional[int] = None,
    objective: str = "balanced",
) -> Dict[str, Any]:
    profile = get_zero_cost_profile(hardware)
    architecture = sample_architecture(
        profile,
        seed=seed,
        objective=objective,
        search_space=ZERO_COST_SEARCH_SPACE,
    )
    return make_zero_cost_safe(architecture)


def initialize_zero_cost_population(
    hardware: Optional[str] = "cpu",
    n_samples: int = 8,
    *,
    seed: Optional[int] = None,
    objective: str = "balanced",
) -> List[Dict[str, Any]]:
    """Sample a small population intended for real proxy evaluation."""

    if n_samples <= 0:
        return []

    profile = get_zero_cost_profile(hardware)
    base_seed = 7 if seed is None else int(seed)
    population = []
    seen = set()
    attempts = 0

    while len(population) < n_samples and attempts < n_samples * 40:
        attempts += 1
        architecture = sample_architecture(
            profile,
            seed=base_seed + attempts * 9973,
            objective=objective,
            search_space=ZERO_COST_SEARCH_SPACE,
        )
        architecture = make_zero_cost_safe(architecture)
        signature = architecture_signature(architecture)
        if signature in seen:
            continue
        seen.add(signature)
        population.append(architecture)

    return population

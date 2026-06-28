"""Response formatting helpers for the MONAS frontend."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .evaluation import pareto_mask


def _finite(value: float) -> float:
    if value == float("inf"):
        return 1e12
    if value == float("-inf"):
        return -1e12
    return value


def population_row(individual: Dict[str, Any]) -> Dict[str, Any]:
    architecture = individual["architecture"]
    metrics = individual["metrics"]
    connections = architecture.get("connections", [])
    layers = architecture.get("layers", [])
    return {
        "id": individual["id"],
        "modelId": individual["modelId"],
        "nodes": len(layers) + 2,
        "edges": len(connections),
        "layers": len(layers),
        "fitness": f"{_finite(individual['fitness']):.4f}",
        "accuracy": f"{metrics['accuracy']:.3f}",
        "flops": f"{metrics['flops']:.2f}M",
        "params": f"{metrics['params']:.2f}M",
        "latency": f"{metrics['latency']:.1f}ms",
        "generation": individual.get("generation", 0),
        "rank": individual.get("rank", 0),
        "crowdingDistance": _finite(individual.get("crowdingDistance", 0.0)),
        "isPareto": bool(individual.get("isPareto", individual.get("rank", 1) == 0)),
        "architecture": {
            "cells": architecture.get("cells", 1),
            "operations": [layer.get("op", "conv3x3") for layer in layers],
            "layers": layers,
            "connections": connections,
            "inputShape": architecture.get("input_shape", [3, 32, 32]),
            "numClasses": architecture.get("num_classes", 10),
        },
        "metrics": metrics,
    }


def pareto_point(individual: Dict[str, Any]) -> Dict[str, Any]:
    metrics = individual["metrics"]
    return {
        "id": individual["id"],
        "modelId": individual["modelId"],
        "accuracy": f"{metrics['accuracy']:.3f}",
        "flops": f"{metrics['flops']:.2f}",
        "params": f"{metrics['params']:.2f}",
        "latency": f"{metrics['latency']:.1f}",
        "fitness": f"{_finite(individual['fitness']):.4f}",
        "isPareto": bool(individual.get("isPareto", individual.get("rank", 1) == 0)),
    }


def serialize_population(population: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = [population_row(item) for item in population]
    return sorted(rows, key=lambda item: float(item["fitness"]), reverse=True)


def serialize_pareto(population: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items = list(population)
    if not any("isPareto" in item for item in items):
        for item, is_pareto in zip(items, pareto_mask(items)):
            item["isPareto"] = is_pareto
    points = [pareto_point(item) for item in items]
    return sorted(points, key=lambda item: (not item["isPareto"], float(item["flops"])))


def best_tradeoff(population: Iterable[Dict[str, Any]]) -> Dict[str, float]:
    items = list(population)
    if not items:
        return {"accuracy": 0.0, "flops": 0.0}
    best = max(items, key=lambda item: item["fitness"])
    return {
        "accuracy": best["metrics"]["accuracy"],
        "flops": round(best["metrics"]["flops"], 2),
    }

"""
evaluation.py
Evaluation module for MONAS using NAS-Bench-301 surrogate models.

This file:
- Loads NAS301 surrogate predictors
- Evaluates architectures on multiple metrics (acc, latency, params, flops)
- Provides a GA-friendly scoring wrapper
- Supports caching to avoid redundant evaluations
"""

from nasbench301 import api
from typing import Dict, Any

import hashlib

def hash_architecture(arch_tuple: tuple) -> str:
    """
    Converts architecture tuple to a stable hash key for caching.
    """
    arch_str = str(arch_tuple)
    return hashlib.md5(arch_str.encode()).hexdigest()

class SurrogateEvaluator:
    def __init__(self):
        """
        Loads NAS-Bench-301 surrogate models.
        """
        # Load NAS-Bench-301 API
        self.nb301 = api.NASBench301API()

        # Caching for speed
        self.cache = {}

        print("[MONAS] NAS-Bench-301 surrogate loaded successfully.")

    def evaluate_architecture(self, arch_tuple: tuple) -> Dict[str, Any]:
        """
        Core evaluator used by GA.
        Returns all metrics.

        Input: tuple representing architecture (NAS-Bench-301)
        Output: dict with accuracy, latency, params, flops
        """

        # hash for caching
        arch_key = hash_architecture(arch_tuple)
        if arch_key in self.cache:
            return self.cache[arch_key]

        # Query NAS-Bench-301
        try:
            arch_info = self.nb301.query_by_arch(arch_tuple)
        except Exception as e:
            print(f"[MONAS] Failed to evaluate architecture: {e}")
            return {
                "accuracy": 0.0,
                "latency": float("inf"),
                "params": float("inf"),
                "flops": float("inf"),
            }

        result = {
            "accuracy": float(arch_info.get("validation_accuracy", 0.0)),
            "latency": float(arch_info.get("latency", 0.0)),
            "params": float(arch_info.get("params", 0.0)),
            "flops": float(arch_info.get("flops", 0.0)),
        }

        # cache result
        self.cache[arch_key] = result
        return result

    def compute_fitness(
        self,
        metrics: Dict[str, float],
        objectives: Dict[str, float],
        hardware_constraints: Dict[str, float],
    ) -> float:
        """
        Computes fitness score using a weighted multi-objective function.

        metrics:
            predicted metrics (accuracy, latency, params, flops)
        objectives:
            weights for each metric, e.g.:
                { "accuracy": 0.7, "latency": 0.2, "params": 0.1 }
        hardware_constraints:
            max allowed params, flops, etc.

        returns: fitness value (higher = better)
        """

        # HARD CONSTRAINT VIOLATION CHECK
        if "max_flops" in hardware_constraints:
            if metrics["flops"] > hardware_constraints["max_flops"]:
                return -1e6  # hard penalty

        # weighted score
        score = 0.0
        for metric, weight in objectives.items():
            score += metrics.get(metric, 0.0) * weight

        return score

"""In-memory runtime state for the MONAS API."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock
from typing import Any, Dict, List, Optional

from .nsga2 import NSGA2Search, SearchConfig, mark_pareto
from .serializers import best_tradeoff, serialize_pareto, serialize_population


class MonasState:
    def __init__(self) -> None:
        self._lock = RLock()
        self.population: List[Dict[str, Any]] = []
        self.history: List[Dict[str, float]] = []
        self.logs: List[str] = []
        self.last_config: SearchConfig = SearchConfig()
        self.total_evaluations = 0
        self.activities: List[Dict[str, Any]] = []
        self.add_activity("System initialized", "info")

    def add_activity(self, action: str, activity_type: str = "info") -> None:
        with self._lock:
            self.activities.append(
                {
                    "id": len(self.activities) + 1,
                    "action": action,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "type": activity_type,
                }
            )
            self.activities = self.activities[-20:]

    def initialize(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        config = SearchConfig.from_payload(payload)
        search = NSGA2Search(config)
        population = mark_pareto(search.initialize())
        with self._lock:
            self.population = population
            self.history = []
            self.logs = [f"[INFO] Population initialized with {len(population)} individuals"]
            self.last_config = config
            self.total_evaluations = search.evaluations
        self.add_activity("Population initialized", "success")
        return {
            "success": True,
            "population": serialize_population(population),
            "logs": list(self.logs),
            "kpis": self.kpis(),
        }

    def run_search(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        config = SearchConfig.from_payload(payload)
        search = NSGA2Search(config)
        initial = None
        with self._lock:
            if self.population and self._same_population_shape(config):
                initial = self.population
        result = search.run(initial_population=initial)
        population = mark_pareto(result["population"])
        with self._lock:
            self.population = population
            self.history = result["history"]
            self.logs = result["logs"]
            self.last_config = config
            self.total_evaluations += result["totalEvaluations"]
        self.add_activity("Search completed successfully", "success")
        return {
            "success": True,
            "logs": result["logs"],
            "population": serialize_population(population),
            "paretoFront": serialize_pareto(result["paretoFront"]),
            "history": result["history"],
            "bestModel": serialize_population([result["bestModel"]])[0],
            "kpis": self.kpis(),
        }

    def _same_population_shape(self, config: SearchConfig) -> bool:
        return (
            len(self.population) == config.population_size
            and self.last_config.hardware == config.hardware
            and self.last_config.objective == config.objective
            and self.last_config.constraints() == config.constraints()
        )

    def get_population(self) -> List[Dict[str, Any]]:
        with self._lock:
            if not self.population:
                self.initialize({"populationSize": self.last_config.population_size})
            return serialize_population(self.population)

    def get_pareto(self) -> List[Dict[str, Any]]:
        with self._lock:
            if not self.population:
                self.initialize({"populationSize": self.last_config.population_size})
            return serialize_pareto(self.population)

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for item in self.population:
                if item["modelId"] == model_id or item["id"] == model_id:
                    return item
        return None

    def kpis(self) -> Dict[str, Any]:
        with self._lock:
            if not self.population:
                return {
                    "bestAccuracy": 0.0,
                    "bestTradeoff": {"accuracy": 0.0, "flops": 0.0},
                    "currentGeneration": 0,
                    "totalEvaluations": self.total_evaluations,
                }
            best_accuracy = max(item["metrics"]["accuracy"] for item in self.population)
            current_generation = max(item.get("generation", 0) for item in self.population)
            return {
                "bestAccuracy": best_accuracy,
                "bestTradeoff": best_tradeoff(self.population),
                "currentGeneration": current_generation,
                "totalEvaluations": self.total_evaluations,
            }

    def get_activity(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.activities)


state = MonasState()

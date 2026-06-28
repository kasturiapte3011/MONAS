"""NSGA-II search engine for MONAS."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import random
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .evaluation import ObjectiveWeights, SurrogateEvaluator, dominates, objective_vector, pareto_mask
from .initialization import (
    CHANNEL_OPTIONS,
    OPERATION_SPECS,
    REPEAT_OPTIONS,
    STRIDE_OPTIONS,
    architecture_signature,
    get_hardware_profile,
    initialize_population,
    stable_id,
)


Individual = Dict[str, Any]


@dataclass
class SearchConfig:
    population_size: int = 50
    generations: int = 10
    mutation_rate: float = 0.10
    crossover_rate: float = 0.70
    objective: str = "balanced"
    hardware: str = "gpu"
    seed: Optional[int] = 7
    max_params: Optional[float] = None
    max_flops: Optional[float] = None
    max_latency: Optional[float] = None

    @classmethod
    def from_payload(cls, payload: Optional[Dict[str, Any]]) -> "SearchConfig":
        payload = payload or {}
        hardware = payload.get("hardware") or payload.get("targetHardware") or payload.get("target_hardware") or "gpu"
        return cls(
            population_size=_bounded_int(payload.get("populationSize", payload.get("population_size", 50)), 2, 200),
            generations=_bounded_int(payload.get("generations", 10), 1, 100),
            mutation_rate=_bounded_float(payload.get("mutationRate", payload.get("mutation_rate", 0.10)), 0.0, 1.0),
            crossover_rate=_bounded_float(payload.get("crossoverRate", payload.get("crossover_rate", 0.70)), 0.0, 1.0),
            objective=str(payload.get("objective", "balanced")),
            hardware=str(hardware),
            seed=_optional_int(payload.get("seed", 7)),
            max_params=_optional_float(payload.get("maxParams", payload.get("max_params"))),
            max_flops=_optional_float(payload.get("maxFlops", payload.get("max_flops"))),
            max_latency=_optional_float(payload.get("maxLatency", payload.get("max_latency"))),
        )

    def constraints(self) -> Dict[str, float]:
        constraints = {}
        if self.max_params is not None:
            constraints["max_params"] = self.max_params
        if self.max_flops is not None:
            constraints["max_flops"] = self.max_flops
        if self.max_latency is not None:
            constraints["max_latency"] = self.max_latency
        return constraints


def _bounded_int(value: Any, low: int, high: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = low
    return max(low, min(high, parsed))


def _bounded_float(value: Any, low: float, high: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = low
    return max(low, min(high, parsed))


def _optional_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _objective_weights(config: SearchConfig) -> Dict[str, float]:
    return ObjectiveWeights.from_name(config.objective).as_dict()


class NSGA2Search:
    def __init__(self, config: SearchConfig):
        self.config = config
        self.profile = get_hardware_profile(config.hardware)
        self.evaluator = SurrogateEvaluator(config.hardware)
        self.rng = random.Random(config.seed)
        self.logs: List[str] = []
        self.history: List[Dict[str, float]] = []
        self.evaluations = 0

    def initialize(self) -> List[Individual]:
        architectures = initialize_population(
            self.config.hardware,
            self.config.population_size,
            seed=self.config.seed,
            objective=self.config.objective,
        )
        population = [self._make_individual(arch, generation=0, ordinal=idx + 1) for idx, arch in enumerate(architectures)]
        return self._rank_population(population)

    def run(self, initial_population: Optional[List[Individual]] = None) -> Dict[str, Any]:
        population = initial_population or self.initialize()
        population = self._rank_population(population)

        self.logs.append(f"[INFO] Initializing population with {len(population)} individuals...")
        self.logs.append(f"[INFO] Starting NSGA-II search for {self.config.generations} generations...")
        self.logs.append(
            f"[INFO] Mutation rate: {self.config.mutation_rate:.2f}, "
            f"Crossover rate: {self.config.crossover_rate:.2f}"
        )

        for generation in range(1, self.config.generations + 1):
            offspring = self._create_offspring(population, generation)
            combined = self._rank_population(population + offspring)
            population = self._select_next_generation(combined, self.config.population_size)
            population = self._rank_population(population)

            best = max(population, key=lambda item: item["fitness"])
            avg_fitness = sum(item["fitness"] for item in population) / max(1, len(population))
            pareto_count = sum(1 for item in population if item["rank"] == 0)
            self.history.append(
                {
                    "generation": generation,
                    "bestFitness": round(best["fitness"], 6),
                    "averageFitness": round(avg_fitness, 6),
                    "bestAccuracy": best["metrics"]["accuracy"],
                    "paretoCount": pareto_count,
                }
            )
            self.logs.append(f"[GEN {generation}] Evaluating population...")
            self.logs.append(f"[GEN {generation}] Best fitness: {best['fitness']:.4f}")
            self.logs.append(f"[GEN {generation}] Average fitness: {avg_fitness:.4f}")
            self.logs.append(f"[GEN {generation}] Pareto front size: {pareto_count}")

        pareto_front = [item for item in population if item["rank"] == 0]
        best = max(population, key=lambda item: item["fitness"])
        self.logs.append("[INFO] Search completed successfully!")
        self.logs.append(f"[INFO] Best model found with accuracy: {best['metrics']['accuracy']:.3f}")
        self.logs.append(f"[INFO] Pareto-optimal architectures: {len(pareto_front)}")

        return {
            "success": True,
            "logs": self.logs,
            "population": population,
            "paretoFront": pareto_front,
            "history": self.history,
            "bestModel": best,
            "totalEvaluations": self.evaluations,
            "config": self.config,
        }

    def _make_individual(self, architecture: Dict[str, Any], generation: int, ordinal: int) -> Individual:
        architecture = deepcopy(architecture)
        model_id = f"model_{ordinal}" if generation == 0 else stable_id(architecture_signature(architecture), "model")
        architecture["id"] = model_id
        metrics = self.evaluator.evaluate_architecture(architecture)
        fitness = self.evaluator.compute_fitness(metrics, _objective_weights(self.config), self.config.constraints())
        self.evaluations += 1
        return {
            "id": stable_id((model_id, architecture_signature(architecture)), "ind"),
            "modelId": model_id,
            "generation": generation,
            "architecture": architecture,
            "metrics": metrics,
            "fitness": fitness,
            "rank": 0,
            "crowdingDistance": 0.0,
        }

    def _create_offspring(self, population: List[Individual], generation: int) -> List[Individual]:
        offspring = []
        while len(offspring) < self.config.population_size:
            parent_a = self._tournament(population)
            parent_b = self._tournament(population)
            if self.rng.random() < self.config.crossover_rate:
                child_arch_a, child_arch_b = self._crossover(parent_a["architecture"], parent_b["architecture"])
            else:
                child_arch_a = deepcopy(parent_a["architecture"])
                child_arch_b = deepcopy(parent_b["architecture"])

            child_arch_a = self._mutate(child_arch_a)
            offspring.append(self._make_individual(child_arch_a, generation, len(offspring) + 1))
            if len(offspring) < self.config.population_size:
                child_arch_b = self._mutate(child_arch_b)
                offspring.append(self._make_individual(child_arch_b, generation, len(offspring) + 1))
        return offspring

    def _tournament(self, population: List[Individual]) -> Individual:
        left, right = self.rng.sample(population, 2)
        if left["rank"] != right["rank"]:
            return left if left["rank"] < right["rank"] else right
        if left["crowdingDistance"] != right["crowdingDistance"]:
            return left if left["crowdingDistance"] > right["crowdingDistance"] else right
        return left if left["fitness"] >= right["fitness"] else right

    def _crossover(self, left: Dict[str, Any], right: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        child_a = deepcopy(left)
        child_b = deepcopy(right)
        layers_a = child_a.get("layers", [])
        layers_b = child_b.get("layers", [])
        if len(layers_a) < 2 or len(layers_b) < 2:
            return child_a, child_b

        cut_a = self.rng.randint(1, len(layers_a) - 1)
        cut_b = self.rng.randint(1, len(layers_b) - 1)
        child_a["layers"] = layers_a[:cut_a] + layers_b[cut_b:]
        child_b["layers"] = layers_b[:cut_b] + layers_a[cut_a:]
        child_a["cells"] = self.rng.choice([left.get("cells", 3), right.get("cells", 3)])
        child_b["cells"] = self.rng.choice([left.get("cells", 3), right.get("cells", 3)])
        self._repair(child_a)
        self._repair(child_b)
        return child_a, child_b

    def _mutate(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        arch = deepcopy(architecture)
        layers = arch.get("layers", [])
        allowed_ops = self.profile.get("allowed_ops", list(OPERATION_SPECS.keys()))

        for layer in layers:
            if self.rng.random() > self.config.mutation_rate:
                continue
            mutation = self.rng.choice(["op", "channels", "stride", "repeat", "activation"])
            if mutation == "op":
                layer["op"] = self.rng.choice(allowed_ops)
            elif mutation == "channels":
                layer["channels"] = self.rng.choice(CHANNEL_OPTIONS)
            elif mutation == "stride":
                layer["stride"] = self.rng.choice(STRIDE_OPTIONS)
            elif mutation == "repeat":
                layer["repeat"] = self.rng.choice(REPEAT_OPTIONS)
            else:
                layer["activation"] = self.rng.choice(["relu", "gelu", "swish"])

        if self.rng.random() < self.config.mutation_rate and len(layers) < 16:
            insert_at = self.rng.randint(0, len(layers))
            layers.insert(
                insert_at,
                {
                    "index": insert_at,
                    "op": self.rng.choice(allowed_ops),
                    "channels": self.rng.choice(CHANNEL_OPTIONS),
                    "stride": self.rng.choice(STRIDE_OPTIONS),
                    "repeat": self.rng.choice(REPEAT_OPTIONS),
                    "activation": self.rng.choice(["relu", "gelu", "swish"]),
                },
            )
        if self.rng.random() < self.config.mutation_rate and len(layers) > 4:
            del layers[self.rng.randrange(len(layers))]
        if self.rng.random() < self.config.mutation_rate:
            arch["cells"] = max(2, min(7, int(arch.get("cells", 3)) + self.rng.choice([-1, 1])))

        self._repair(arch)
        return arch

    def _repair(self, architecture: Dict[str, Any]) -> None:
        layers = architecture.get("layers", [])
        for idx, layer in enumerate(layers):
            layer["index"] = idx
            if idx == 0:
                layer["stride"] = 1
            if layer.get("op") in {"skip", "maxpool3x3", "avgpool3x3"} and idx > 0:
                layer["stride"] = min(int(layer.get("stride", 1)), 2)

        connections = []
        for idx, layer in enumerate(layers):
            connections.append({"from": max(0, idx), "to": idx + 1, "operation": layer["op"]})
            if idx > 1 and self.rng.random() < 0.22:
                connections.append({"from": self.rng.randint(0, idx - 1), "to": idx + 1, "operation": "skip"})
        architecture["connections"] = connections
        architecture["id"] = stable_id(architecture_signature(architecture))

    def _rank_population(self, population: List[Individual]) -> List[Individual]:
        fronts = fast_non_dominated_sort(population)
        for rank, front in enumerate(fronts):
            for item in front:
                item["rank"] = rank
            assign_crowding_distance(front)
        return population

    def _select_next_generation(self, population: List[Individual], size: int) -> List[Individual]:
        fronts = fast_non_dominated_sort(population)
        selected: List[Individual] = []
        for front in fronts:
            assign_crowding_distance(front)
            if len(selected) + len(front) <= size:
                selected.extend(front)
            else:
                needed = size - len(selected)
                selected.extend(sorted(front, key=lambda item: item["crowdingDistance"], reverse=True)[:needed])
                break
        return selected


def fast_non_dominated_sort(population: List[Individual]) -> List[List[Individual]]:
    fronts: List[List[Individual]] = [[]]
    domination_counts: Dict[int, int] = {}
    dominated_sets: Dict[int, List[int]] = {}
    object_indexes = {id(item): idx for idx, item in enumerate(population)}

    for p_idx, p in enumerate(population):
        dominated_sets[p_idx] = []
        domination_counts[p_idx] = 0
        for q_idx, q in enumerate(population):
            if p_idx == q_idx:
                continue
            if dominates(p["metrics"], q["metrics"]):
                dominated_sets[p_idx].append(q_idx)
            elif dominates(q["metrics"], p["metrics"]):
                domination_counts[p_idx] += 1
        if domination_counts[p_idx] == 0:
            p["rank"] = 0
            fronts[0].append(p)

    current = 0
    while current < len(fronts) and fronts[current]:
        next_front = []
        for p in fronts[current]:
            p_idx = object_indexes[id(p)]
            for q_idx in dominated_sets[p_idx]:
                domination_counts[q_idx] -= 1
                if domination_counts[q_idx] == 0:
                    population[q_idx]["rank"] = current + 1
                    next_front.append(population[q_idx])
        current += 1
        if next_front:
            fronts.append(next_front)
    return fronts


def assign_crowding_distance(front: List[Individual]) -> None:
    if not front:
        return
    for item in front:
        item["crowdingDistance"] = 0.0
    if len(front) <= 2:
        for item in front:
            item["crowdingDistance"] = float("inf")
        return

    objective_count = len(objective_vector(front[0]["metrics"]))
    for objective_idx in range(objective_count):
        front.sort(key=lambda item: objective_vector(item["metrics"])[objective_idx])
        front[0]["crowdingDistance"] = float("inf")
        front[-1]["crowdingDistance"] = float("inf")
        low = objective_vector(front[0]["metrics"])[objective_idx]
        high = objective_vector(front[-1]["metrics"])[objective_idx]
        if high == low:
            continue
        for idx in range(1, len(front) - 1):
            previous_value = objective_vector(front[idx - 1]["metrics"])[objective_idx]
            next_value = objective_vector(front[idx + 1]["metrics"])[objective_idx]
            front[idx]["crowdingDistance"] += (next_value - previous_value) / (high - low)


def mark_pareto(population: List[Individual]) -> List[Individual]:
    mask = pareto_mask(population)
    for item, is_pareto in zip(population, mask):
        item["isPareto"] = is_pareto
    return population

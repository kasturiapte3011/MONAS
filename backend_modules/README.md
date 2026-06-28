# MONAS Backend

FastAPI backend for Multi-Objective Neural Architecture Search using a
Genetic Algorithm / NSGA-II loop.

## What It Provides

- Architecture population initialization
- Surrogate evaluation for accuracy, latency, parameters, and FLOPs
- NSGA-II evolution with mutation, crossover, non-dominated sorting, and crowding distance
- Pareto-front extraction
- Model advisor recommendations
- Lightweight architecture explainability
- PyTorch code generation for selected architectures

The evaluator is deterministic and local-first, so the API works without a
NASBench dataset download or GPU. NASBench/vLLM can be added as optional deeper
evaluators later without changing the frontend contract.

## Zero-Cost Proxy Evaluator

For near realistic proof-of-concept scoring, we use the modules:

- `initialization.py`
- `evaluation.py`

These instantiate candidate models in PyTorch and measure real parameter count, hook-based FLOPs, median forward latency, and zero-cost quality proxies (`NASWOT`, `SynFlow`, `grad_norm`). The `accuracy` value returned by this path is an `accuracy_proxy`, not trained validation accuracy.

## Run

From the repository root:

```bash
backend_modules/.venv/bin/python -m uvicorn backend_modules.main:app --reload --host 127.0.0.1 --port 8000
```

Open the API docs at:

```text
http://127.0.0.1:8000/docs
```

## Frontend-Friendly Endpoints

- `GET /api/health`
- `POST /api/initialize`
- `POST /api/population/initialize`
- `GET /api/population`
- `POST /api/search`
- `GET /api/pareto`
- `GET /api/kpis`
- `GET /api/activity`
- `POST /api/explain`
- `GET /api/explain/{model_id}`
- `POST /api/advisor`
- `GET /api/models/{model_id}`
- `GET /api/models/{model_id}/code`

## Example Search Request

```json
{
  "populationSize": 50,
  "mutationRate": 0.1,
  "crossoverRate": 0.7,
  "generations": 10,
  "objective": "balanced",
  "hardware": "gpu",
  "seed": 7
}
```
"""FastAPI application for the MONAS backend."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from .advisor import advisor_suggest
from .codegen import ArchitectureCodeGenerator
from .explainability import explain_model
from .store import state


app = FastAPI(
    title="MONAS Backend",
    description="Multi-Objective Neural Architecture Search backend using GA / NSGA-II.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    populationSize: int = Field(default=50, ge=2, le=200)
    mutationRate: float = Field(default=0.1, ge=0.0, le=1.0)
    crossoverRate: float = Field(default=0.7, ge=0.0, le=1.0)
    generations: int = Field(default=10, ge=1, le=100)
    objective: str = "balanced"
    hardware: Optional[str] = "gpu"
    seed: Optional[int] = 7
    maxParams: Optional[float] = None
    maxFlops: Optional[float] = None
    maxLatency: Optional[float] = None


class ExplanationRequest(BaseModel):
    modelId: str
    explainType: str = "global"


class AdvisorRequest(BaseModel):
    taskType: str = "Image Classification"
    datasetSize: str = "Medium (10k-100k)"
    priority: Dict[str, float] = Field(default_factory=lambda: {"accuracy": 0.6, "latency": 0.3, "size": 0.1})
    targetHardware: str = "Cloud GPU"
    maxParams: Optional[str] = ""
    maxFlops: Optional[str] = ""
    maxLatency: Optional[str] = ""
    specialRequirements: Optional[str] = ""


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "service": "monas-backend"}


@app.get("/api/kpis")
def get_kpis() -> Dict[str, Any]:
    return state.kpis()


@app.get("/api/activity")
def get_activity() -> Any:
    return state.get_activity()


@app.post("/api/population/initialize")
@app.post("/api/initialize")
def initialize_population(request: SearchRequest) -> Dict[str, Any]:
    return state.initialize(request.model_dump())


@app.get("/api/population")
def get_population() -> Any:
    return state.get_population()


@app.post("/api/search")
def run_search(request: SearchRequest) -> Dict[str, Any]:
    state.add_activity("Search started", "info")
    return state.run_search(request.model_dump())


@app.get("/api/pareto")
def get_pareto() -> Any:
    return state.get_pareto()


@app.get("/api/models/{model_id}")
def get_model(model_id: str) -> Dict[str, Any]:
    model = state.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    from .serializers import population_row

    return population_row(model)


@app.post("/api/explain")
def explain(request: ExplanationRequest) -> Dict[str, Any]:
    model = state.get_model(request.modelId)
    return explain_model(request.modelId, model, request.explainType)


@app.get("/api/explain/{model_id}")
def explain_by_id(model_id: str, explainType: str = "global") -> Dict[str, Any]:
    model = state.get_model(model_id)
    return explain_model(model_id, model, explainType)


@app.post("/api/advisor")
def advisor(request: AdvisorRequest) -> Dict[str, Any]:
    state.add_activity("Model Advisor recommendations generated", "success")
    return advisor_suggest(request.model_dump())


@app.get("/api/models/{model_id}/code", response_class=PlainTextResponse)
def generate_model_code(model_id: str) -> str:
    model = state.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    generator = ArchitectureCodeGenerator()
    return generator.generate_code(model["architecture"])

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.environment import EnvironmentalState


class EvidenceItem(BaseModel):
    document_id: str
    chunk_id: str | None = None
    title: str
    source: str | None = None
    year: int | None = None
    publisher: str | None = None
    source_url: str | None = None
    text: str
    score: float | None = None
    domain: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    limitations: str | None = None
    methodology: str | None = None


class Recommendation(BaseModel):
    action: str
    why_it_works: str
    metrics_impacted: list[str] = Field(default_factory=list)
    expected_direction: dict[str, str] = Field(default_factory=dict)
    estimated_effect: str
    time_horizon: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    confidence: str
    assumptions: list[str] = Field(default_factory=list)
    tradeoffs: list[str] = Field(default_factory=list)
    measurement_plan: str
    internal_rank: float | None = None


class ReasoningTrace(BaseModel):
    activated_variables: list[str] = Field(default_factory=list)
    pathways: list[list[str]] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    candidate_interventions: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class AgentQueryResponse(BaseModel):
    status: Literal["clarification_required", "recommendation_ready", "insufficient_evidence"]
    session_id: str
    message: str
    missing_information: list[str] = Field(default_factory=list)
    clarifying_questions: list[str] = Field(default_factory=list)
    summary: str | None = None
    environmental_state: EnvironmentalState | None = None
    reasoning: ReasoningTrace | None = None
    recommendations: list[Recommendation] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    pipeline: list[str] = Field(default_factory=list)


class KnowledgeSearchResponse(BaseModel):
    results: list[EvidenceItem]


class HealthResponse(BaseModel):
    status: str
    app: str
    database: str
    documents_indexed: int

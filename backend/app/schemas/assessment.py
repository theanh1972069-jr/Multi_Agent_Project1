from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentStepOut(BaseModel):
    """Sanitized execution step trace for a single agent node."""

    step_order: int
    agent_name: str
    status: str
    latency_ms: int
    summary: str
    error_code: str | None = None


class AssessmentCreateRequest(BaseModel):
    """Structured screening payload forwarded to Data Analysis Agent for validation."""

    model_config = ConfigDict(extra="allow")

    age: Any = None
    gender: Any = None
    height_cm: Any = None
    weight_kg: Any = None
    waist_cm: Any = None
    hip_cm: Any = None
    previously_diagnosed_diabetes: Any = False
    is_pregnant: Any = None


class AssessmentOut(BaseModel):
    """Full assessment response including ML prediction, citations, and agent trace."""

    id: str
    request_id: str
    status: str
    raw_inputs: dict[str, Any]
    derived_features: dict[str, Any] | None = None
    prediction: dict[str, Any] | None = None
    summary_text: str
    recommendations: list[str] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    kg_relations: list[dict[str, Any]] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    llm_used: bool = False
    llm_fallback: bool = False
    agent_steps: list[AgentStepOut] = Field(default_factory=list)
    total_latency_ms: int = 0
    error_code: str | None = None
    created_at: datetime

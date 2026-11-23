from __future__ import annotations

from typing import Any, Literal, TypedDict

from pydantic import BaseModel


class AssessmentInput(BaseModel):
    """Strict anthropometric and cohort screening input schema for NHANES assessment."""

    age: int
    gender: Literal[1, 2]
    height_cm: float
    weight_kg: float
    waist_cm: float
    hip_cm: float | None = None
    previously_diagnosed_diabetes: bool = False
    is_pregnant: bool | None = None


class AgentStepTrace(BaseModel):
    """Sanitized execution trace entry for a single LangGraph agent node."""

    step_order: int
    agent_name: str
    status: str
    latency_ms: int
    summary: str
    error_code: str | None = None


class OrchestrationState(TypedDict, total=False):
    """Shared state passed across the 5-node LangGraph StateGraph."""

    request_id: str
    flow: Literal["assessment", "chat"]
    intent: str
    payload: dict[str, Any]
    message: str
    history: list[dict[str, Any]]
    linked_assessment: dict[str, Any] | None
    active_source_ids: set[str] | None

    status: str
    da_valid: bool
    prediction_ok: bool

    validated_input: dict[str, Any] | None
    nhanes_features: dict[str, float | int | None] | None
    derived_features: dict[str, float | None] | None
    prediction: dict[str, Any] | None

    knowledge_query: str
    citations: list[dict[str, Any]]
    kg_relations: list[dict[str, Any]]
    kg_source: str | None
    has_relevant_evidence: bool

    summary_text: str
    answer: str
    recommendations: list[str]
    limitations: list[str]
    redirect_to_assessment: bool
    safety_flag: str | None

    llm_used: bool
    llm_fallback: bool
    llm_provider: str
    llm_model: str

    agent_steps: list[dict[str, Any]]
    error_code: str | None

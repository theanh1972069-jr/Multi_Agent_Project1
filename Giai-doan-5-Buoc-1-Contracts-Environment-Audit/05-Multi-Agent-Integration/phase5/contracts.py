"""Stage 5 Step 1: strict API and LangGraph contracts.

Design only: no model load, DB access, network call, or LLM call.
Never treat an HbA1c >= 5.7% classifier as future type-2 diabetes risk.
"""
from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict
import math
import re

from pydantic import BaseModel, ConfigDict, Field, model_validator

EXPECTED_TASK = "classify_hba1c_ge_5_7_indicator"
EXPECTED_MODEL = "LogisticRegression"
EXPECTED_SHA256 = "31e9c94b0f14369be7920b9315b026d0c4afedb9f7b2885d120d631d930582b1"
THRESHOLD = 0.225
CHROMA_COLLECTION = "diabetes_kb_step3_e5small_v1"
CHROMA_SNAPSHOT_SHA256 = "cc064ec7187192c999418051cb2125a0510412843f8d0908e3d6842e4a71c7cd"
PREDICTION_PATH = "/api/v1/research/nhanes/hba1c/predict"
RESEARCH_WARNING = (
    "Research-only HbA1c >=5.7% indicator classification; "
    "NOT a diagnosis or future type 2 diabetes risk estimate."
)

Operation = Literal["research_prediction", "synthetic_rag_demo"]
KnowledgeGate = Literal["BLOCKED_RESEARCH_ONLY", "NOT_EVALUATED", "SYNTHETIC_READY"]


class ResearchFeatures(BaseModel):
    """Locked NHANES input schema (strict, without real patient data in tests)."""

    model_config = ConfigDict(strict=True, extra="forbid")
    RIDAGEYR: int = Field(ge=20, le=80)
    RIAGENDR: Literal[1, 2]
    BMXBMI: float = Field(ge=11.1, le=74.8, allow_inf_nan=False)


class WorkflowRequest(BaseModel):
    """Only the caller may set these fields. Gate and result are server-owned."""

    model_config = ConfigDict(strict=True, extra="forbid")
    request_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    operation: Operation
    # Every Step 1 run is synthetic; real user/clinical payloads are outside scope.
    synthetic_test_only: Literal[True] = True
    features: ResearchFeatures | None = None
    question: str | None = Field(default=None, min_length=1, max_length=500)

    @model_validator(mode="after")
    def mode_exclusivity(self) -> "WorkflowRequest":
        if self.operation == "research_prediction":
            if self.features is None or self.question is not None:
                raise ValueError("research_prediction requires features and forbids question")
        else:
            if self.features is not None or self.question is None:
                raise ValueError("synthetic_rag_demo requires question and forbids features")
        return self


class EvidenceMetadata(BaseModel):
    """Identifiers ONLY. Retrieved unapproved medical content must not enter state."""

    model_config = ConfigDict(strict=True, extra="forbid")
    chunk_id: str = Field(min_length=1, max_length=180)
    source_id: str = Field(min_length=1, max_length=120)
    source_url: str | None = None
    provenance_match: bool
    review_status: str
    allowed_to_answer: bool = False

    @model_validator(mode="after")
    def reject_unreviewed_answer_access(self) -> "EvidenceMetadata":
        # Current Phase 4 snapshot has ZERO medically-approved claims/relations.
        # This guard is a prototype invariant, not a production ACL.
        if self.allowed_to_answer:
            raise ValueError("medical evidence is not approved for answering")
        return self


class AgentError(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    code: str = Field(pattern=r"^[A-Z][A-Z0-9_]{1,79}$")
    component: str = Field(min_length=1, max_length=80)
    # Deliberately no arbitrary exception text, request payload, or credentials.


class UpstreamPrediction(BaseModel):
    """Matches existing 8B response; use Step 2 to call API and validate."""

    model_config = ConfigDict(strict=True, extra="forbid")
    status: Literal["research_only"]
    task: Literal["classify_hba1c_ge_5_7_indicator"]
    model_name: Literal["LogisticRegression"]
    model_sha256: Literal["31e9c94b0f14369be7920b9315b026d0c4afedb9f7b2885d120d631d930582b1"]
    threshold: float = Field(allow_inf_nan=False)
    model_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    predicted_label: Literal[0, 1]
    warning: str = Field(min_length=1)

    @model_validator(mode="after")
    def verify_locked_threshold_and_label(self) -> "UpstreamPrediction":
        if not math.isclose(self.threshold, THRESHOLD, rel_tol=0, abs_tol=1e-12):
            raise ValueError("threshold mismatch")
        if self.predicted_label != int(self.model_score >= THRESHOLD):
            raise ValueError("predicted_label mismatch")
        return self


class WorkflowResponse(BaseModel):
    """Safe, research-only output envelope, no implied clinical assessment."""

    model_config = ConfigDict(strict=True, extra="forbid")
    request_id: str
    operation: Operation
    status: Literal["not_connected", "blocked", "needs_input", "failed", "ok"]
    knowledge_gate: KnowledgeGate
    llm_called: bool = False
    prediction: UpstreamPrediction | None = None
    evidence_metadata: list[EvidenceMetadata] = Field(default_factory=list)
    errors: list[AgentError] = Field(default_factory=list)
    warning: str = RESEARCH_WARNING

    @model_validator(mode="after")
    def fail_closed(self) -> "WorkflowResponse":
        if self.operation == "research_prediction":
            if self.knowledge_gate != "BLOCKED_RESEARCH_ONLY" or self.llm_called:
                raise ValueError("research medical KB must remain blocked; LLM disabled")
        elif self.prediction is not None:
            raise ValueError("synthetic Atlas demo must never carry NHANES prediction")
        if self.knowledge_gate != "SYNTHETIC_READY" and self.llm_called:
            raise ValueError("LLM call requires explicitly reviewed synthetic evidence")
        if self.status in {"blocked", "not_connected", "needs_input", "failed"} and self.prediction is not None:
            raise ValueError("unfinished/failed workflow cannot contain a prediction")
        return self


class AgentState(TypedDict):
    """LangGraph shared state; each node returns a partial state dictionary."""

    request_id: str
    operation: Operation
    raw_input: dict[str, Any]
    knowledge_gate: KnowledgeGate
    errors: list[dict[str, Any]]
    llm_called: bool
    validated_input: NotRequired[dict[str, Any]]
    prediction_result: NotRequired[dict[str, Any] | None]
    evidence_metadata: NotRequired[list[dict[str, Any]]]
    knowledge_status: NotRequired[str]
    prediction_status: NotRequired[str]
    final_response: NotRequired[dict[str, Any]]


def make_initial_state(request: WorkflowRequest) -> AgentState:
    """Construct server-owned gate. Users cannot submit/override gate fields."""
    raw: dict[str, Any] = (
        {"features": request.features.model_dump()}
        if request.operation == "research_prediction" and request.features is not None
        else {"synthetic_question": request.question}
    )
    return {
        "request_id": request.request_id,
        "operation": request.operation,
        "raw_input": raw,
        "knowledge_gate": "BLOCKED_RESEARCH_ONLY"
        if request.operation == "research_prediction" else "NOT_EVALUATED",
        "errors": [],
        "llm_called": False,
    }

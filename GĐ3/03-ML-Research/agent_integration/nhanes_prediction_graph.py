"""Step 8C: LangGraph Prediction Agent (local research-only integration).

Educational example for the USER to run. Does not load, fit, or modify any ML model.
This graph implements only the deterministic prediction route, NOT the full five-agent system.
Requires an already-running 8B API at 127.0.0.1:8000.
"""
from __future__ import annotations

from typing import Any, Callable, Literal, TypedDict
import math
import requests
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from langgraph.graph import StateGraph, START, END

EXPECTED_SHA256 = "31e9c94b0f14369be7920b9315b026d0c4afedb9f7b2885d120d631d930582b1"
EXPECTED_MODEL = "LogisticRegression"
EXPECTED_TASK = "classify_hba1c_ge_5_7_indicator"
THRESHOLD = 0.225
PREDICT_URL = "http://127.0.0.1:8000/api/v1/research/nhanes/hba1c/predict"

RESEARCH_WARNING = (
    "Research-only HbA1c >=5.7% indicator classification; "
    "NOT a diagnosis or future type 2 diabetes risk estimate."
)

class FeatureInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    RIDAGEYR: int = Field(ge=20, le=80)  # NHANES age 80 is top-coded 80+
    RIAGENDR: Literal[1, 2]
    BMXBMI: float = Field(ge=11.1, le=74.8, allow_inf_nan=False)

class UpstreamOutput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    status: Literal["research_only"]
    task: str
    model_name: str
    model_sha256: str
    threshold: float
    model_score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    predicted_label: Literal[0, 1]
    warning: str

class PredictionState(TypedDict, total=False):
    request_id: str
    task_type: str
    features: dict[str, Any]
    validated_features: dict[str, Any]
    status: str
    error_code: str | None
    upstream_result: dict[str, Any] | None
    final_response: dict[str, Any]

# Injectable boundary for mock testing. Never add LLM generation to this path.
PredictionCaller = Callable[[dict[str, Any]], tuple[int, dict[str, Any]]]

def call_local_api(features: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Perform one POST to the fixed localhost inference endpoint, no implicit retry."""
    resp = requests.post(
        PREDICT_URL, json=features, timeout=(2.0, 5.0), allow_redirects=False
    )
    try:
        data = resp.json()
    except ValueError:
        data = {}
    return resp.status_code, data if isinstance(data, dict) else {}


def build_prediction_graph(caller: PredictionCaller | None = None):
    """Compile a minimal LangGraph route; no database, LLM, or external tool access."""
    invoke_api = caller if caller is not None else call_local_api

    def validate_input(state: PredictionState) -> dict[str, Any]:
        if state.get("task_type") != EXPECTED_TASK:
            return {"status": "needs_input", "error_code": "UNSUPPORTED_TASK"}
        if not isinstance(state.get("features"), dict):
            return {"status": "needs_input", "error_code": "INVALID_FEATURES"}
        try:
            parsed = FeatureInput.model_validate(state["features"])
        except ValidationError:
            return {"status": "needs_input", "error_code": "INVALID_FEATURES"}
        return {"status": "validated", "error_code": None,
                "validated_features": parsed.model_dump()}

    def route_after_validation(state: PredictionState) -> str:
        return "prediction_agent" if state.get("status") == "validated" else "finalize"

    def prediction_agent(state: PredictionState) -> dict[str, Any]:
        try:
            status_code, body = invoke_api(state["validated_features"])
        except (requests.exceptions.RequestException, TimeoutError, OSError):
            return {"status": "failed", "error_code": "PREDICTION_SERVICE_UNAVAILABLE"}
        except Exception:
            return {"status": "failed", "error_code": "PREDICTION_SERVICE_ERROR"}
        if status_code != 200:
            return {"status": "failed", "error_code": "UPSTREAM_HTTP_ERROR"}
        try:
            out = UpstreamOutput.model_validate(body)
        except ValidationError:
            return {"status": "failed", "error_code": "INVALID_UPSTREAM_RESPONSE"}
        # Fail closed on any mismatch; don't trust a score from an unknown/changed model.
        valid = (
            out.task == EXPECTED_TASK
            and out.model_name == EXPECTED_MODEL
            and out.model_sha256 == EXPECTED_SHA256
            and math.isclose(out.threshold, THRESHOLD, abs_tol=1e-12, rel_tol=0)
            and out.predicted_label == int(out.model_score >= THRESHOLD)
            and bool(out.warning.strip())
        )
        if not valid:
            return {"status": "failed", "error_code": "UPSTREAM_CONTRACT_MISMATCH"}
        return {"status": "ok", "error_code": None,
                "upstream_result": out.model_dump()}

    def finalize(state: PredictionState) -> dict[str, Any]:
        if state.get("status") == "ok" and state.get("upstream_result"):
            r = state["upstream_result"]
            response = {
                "status": "ok", "task": EXPECTED_TASK,
                "model_score": r["model_score"], "predicted_label": r["predicted_label"],
                "threshold": r["threshold"], "model_name": r["model_name"],
                "model_sha256": r["model_sha256"], "warning": RESEARCH_WARNING,
            }
        else:
            response = {
                "status": state.get("status", "failed"),
                "error_code": state.get("error_code") or "UNSPECIFIED_ERROR",
                "warning": RESEARCH_WARNING,
            }
        return {"final_response": response}

    builder = StateGraph(PredictionState)
    builder.add_node("validate_input", validate_input)
    builder.add_node("prediction_agent", prediction_agent)
    builder.add_node("finalize", finalize)
    builder.add_edge(START, "validate_input")
    builder.add_conditional_edges("validate_input", route_after_validation,
                                  {"prediction_agent": "prediction_agent", "finalize": "finalize"})
    builder.add_edge("prediction_agent", "finalize")
    builder.add_edge("finalize", END)
    return builder.compile()

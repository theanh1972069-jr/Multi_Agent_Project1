"""Phase 5 Step 2: safe research-only Data Analysis -> Prediction adapter.

Only explicit live operation talks to the EXISTING localhost Phase 3 FastAPI.
No joblib loads, model training, Chroma/Neo4j access, Ollama, or medical LLM.
Test data are synthetic, never real patient data. This is not clinical software.
"""
from __future__ import annotations

import json
import math
import socket
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from pydantic import ValidationError

from .contracts import (
    AgentError, AgentState, EXPECTED_SHA256, PREDICTION_PATH, RESEARCH_WARNING,
    ResearchFeatures, UpstreamPrediction, WorkflowRequest, WorkflowResponse,
    make_initial_state,
)

# Max response limits defend against accidental oversized/malformed responses.
MAX_RESPONSE_BYTES = 8192
HTTP_TIMEOUT_SECONDS = 5.0


class IntegrationFailure(Exception):
    """Only sanitized fixed error codes leave this adapter."""

    ALLOWED = {
        "INVALID_INPUT", "UPSTREAM_UNAVAILABLE", "UPSTREAM_HTTP_ERROR",
        "UPSTREAM_BAD_JSON", "UPSTREAM_SCHEMA_MISMATCH", "UPSTREAM_NOT_READY",
        "UNSAFE_API_URL", "INTERNAL_INTEGRATION_ERROR",
    }

    def __init__(self, code: str):
        super().__init__(code if code in self.ALLOWED else "INTERNAL_INTEGRATION_ERROR")
        self.code = code if code in self.ALLOWED else "INTERNAL_INTEGRATION_ERROR"


def validate_loopback_predict_url(url: str) -> str:
    """Only a literal loopback host and the locked inference route are accepted.

    No arbitrary hostname, userinfo, query, redirects or URL fragments.
    """
    parsed = urlparse(url)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or parsed.port is None
        or parsed.path != PREDICTION_PATH
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.params
    ):
        raise IntegrationFailure("UNSAFE_API_URL")
    return url


class PredictionClient(Protocol):
    def predict(self, features: ResearchFeatures) -> UpstreamPrediction: ...


class MockPredictionClient:
    """Deterministic CONTRACT fixture; scores are not the trained model output."""

    def __init__(self, mode: str = "valid") -> None:
        self.mode = mode
        self.calls = 0

    def predict(self, features: ResearchFeatures) -> UpstreamPrediction:
        self.calls += 1
        # A synthetic score deliberately chosen away from the 0.225 threshold.
        data: dict[str, Any] = {
            "status": "research_only",
            "task": "classify_hba1c_ge_5_7_indicator",
            "model_name": "LogisticRegression",
            "model_sha256": EXPECTED_SHA256,
            "threshold": 0.225,
            "model_score": 0.42,
            "predicted_label": 1,
            "warning": "Research-only HbA1c >=5.7% indicator classification; not a diagnosis or future type 2 diabetes risk estimate.",
        }
        if self.mode == "unavailable":
            raise IntegrationFailure("UPSTREAM_UNAVAILABLE")
        if self.mode == "bad_hash":
            data["model_sha256"] = "wrong-sha256"
        if self.mode == "bad_threshold":
            data["threshold"] = 0.5
        if self.mode == "bad_label":
            data["predicted_label"] = 0
        if self.mode == "bad_warning":
            data["warning"] = "Everything is safe to diagnose."
        return parse_upstream_prediction(data)


def parse_upstream_prediction(data: object) -> UpstreamPrediction:
    """Enforce frozen SHA/threshold/schema and research-only disclaimer."""
    try:
        result = UpstreamPrediction.model_validate(data)
    except (ValidationError, TypeError, ValueError) as exc:
        raise IntegrationFailure("UPSTREAM_SCHEMA_MISMATCH") from exc
    text = result.warning.lower()
    if "research-only" not in text or "not a diagnosis" not in text or "future" not in text:
        raise IntegrationFailure("UPSTREAM_SCHEMA_MISMATCH")
    return result


def _read_local_json(req: Request, *, timeout: float) -> Any:
    """Do not follow HTTP redirects. Restrict status/body size and redact errors."""
    class _NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, *args: Any, **kwargs: Any) -> None:
            return None

    opener = build_opener(ProxyHandler({}), _NoRedirect())
    try:
        with opener.open(req, timeout=timeout) as resp:
            if resp.status != 200:
                raise IntegrationFailure("UPSTREAM_HTTP_ERROR")
            body = resp.read(MAX_RESPONSE_BYTES + 1)
            if len(body) > MAX_RESPONSE_BYTES:
                raise IntegrationFailure("UPSTREAM_BAD_JSON")
            try:
                return json.loads(body)
            except (ValueError, UnicodeDecodeError) as exc:
                raise IntegrationFailure("UPSTREAM_BAD_JSON") from exc
    except HTTPError as exc:
        raise IntegrationFailure("UPSTREAM_HTTP_ERROR") from exc
    except (URLError, TimeoutError, socket.timeout, OSError) as exc:
        raise IntegrationFailure("UPSTREAM_UNAVAILABLE") from exc


class LocalFastAPIClient:
    """Uses the already-running *local* Phase 3 FastAPI; no model deserialization."""

    def __init__(self, prediction_url: str, *, timeout: float = HTTP_TIMEOUT_SECONDS) -> None:
        self.prediction_url = validate_loopback_predict_url(prediction_url)
        if not (0.0 < timeout <= 15.0 and math.isfinite(timeout)):
            raise ValueError("invalid timeout")
        self.timeout = timeout
        parsed = urlparse(prediction_url)
        self.ready_url = urlunparse((parsed.scheme, parsed.netloc, "/health/ready", "", "", ""))

    def readiness(self) -> None:
        payload = _read_local_json(Request(self.ready_url, method="GET"), timeout=self.timeout)
        if not isinstance(payload, dict) or (
            payload.get("status") != "ready"
            or payload.get("model_sha256") != EXPECTED_SHA256
            or payload.get("research_only") is not True
        ):
            raise IntegrationFailure("UPSTREAM_NOT_READY")

    def predict(self, features: ResearchFeatures) -> UpstreamPrediction:
        self.readiness()
        payload = json.dumps(features.model_dump(), ensure_ascii=True).encode("utf-8")
        req = Request(self.prediction_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        return parse_upstream_prediction(_read_local_json(req, timeout=self.timeout))


def make_step2_graph(client: PredictionClient):
    """5-node LangGraph: 2 integrated agents, 3 no-LLM/no-DB stubs.

    Graph remains strictly linear until phase5 step5 orchestrator branching.
    """
    from langgraph.graph import START, END, StateGraph

    def orchestrator_agent(state: AgentState) -> dict[str, Any]:
        return {"llm_called": False}

    def data_analysis_agent(state: AgentState) -> dict[str, Any]:
        try:
            validated = ResearchFeatures.model_validate(state["raw_input"]["features"])
            return {"validated_input": validated.model_dump()}
        except (ValidationError, KeyError, TypeError, ValueError):
            return {"errors": [{"code": "INVALID_INPUT", "component": "data_analysis_agent"}]}

    def prediction_agent(state: AgentState) -> dict[str, Any]:
        if state.get("errors"):
            return {"prediction_status": "SKIPPED", "prediction_result": None}
        try:
            features = ResearchFeatures.model_validate(state["validated_input"])
            result = client.predict(features)
        except (IntegrationFailure, ValidationError, KeyError) as exc:
            code = exc.code if isinstance(exc, IntegrationFailure) else "INVALID_INPUT"
            return {
                "prediction_status": "FAILED",
                "prediction_result": None,
                "errors": [{"code": code, "component": "prediction_agent"}],
            }
        except Exception:
            # No raw exception string that might disclose user/config/host data.
            return {
                "prediction_status": "FAILED", "prediction_result": None,
                "errors": [{"code": "INTERNAL_INTEGRATION_ERROR", "component": "prediction_agent"}],
            }
        return {"prediction_status": "SUCCESS", "prediction_result": result.model_dump()}

    def knowledge_agent(state: AgentState) -> dict[str, Any]:
        return {"knowledge_gate": "BLOCKED_RESEARCH_ONLY", "evidence_metadata": [], "knowledge_status": "NOT_CONNECTED"}

    def consultation_agent(state: AgentState) -> dict[str, Any]:
        errs = [AgentError.model_validate(err) for err in state.get("errors", [])]
        predicted = None
        if not errs and state.get("prediction_result") is not None:
            predicted = UpstreamPrediction.model_validate(state["prediction_result"])
        response = WorkflowResponse(
            request_id=state["request_id"],
            operation="research_prediction",
            status="ok" if predicted is not None else "failed",
            knowledge_gate="BLOCKED_RESEARCH_ONLY",
            prediction=predicted,
            llm_called=False,
            errors=errs,
            warning=RESEARCH_WARNING,
        )
        return {"final_response": response.model_dump(), "llm_called": False}

    builder = StateGraph(AgentState)
    for name, node in [
        ("orchestrator_agent", orchestrator_agent),
        ("data_analysis_agent", data_analysis_agent),
        ("prediction_agent", prediction_agent),
        ("knowledge_agent", knowledge_agent),
        ("consultation_agent", consultation_agent),
    ]:
        builder.add_node(name, node)
    builder.add_edge(START, "orchestrator_agent")
    builder.add_edge("orchestrator_agent", "data_analysis_agent")
    builder.add_edge("data_analysis_agent", "prediction_agent")
    builder.add_edge("prediction_agent", "knowledge_agent")
    builder.add_edge("knowledge_agent", "consultation_agent")
    builder.add_edge("consultation_agent", END)
    return builder.compile()


def run_step2_graph(client: PredictionClient, req: WorkflowRequest) -> WorkflowResponse:
    """Accept only synthetic prediction requests; never medical queries or real data."""
    if req.operation != "research_prediction" or req.synthetic_test_only is not True:
        raise IntegrationFailure("INVALID_INPUT")
    state = make_initial_state(req)
    finished = make_step2_graph(client).invoke(state)
    return WorkflowResponse.model_validate(finished["final_response"])

from __future__ import annotations

from pathlib import Path

from ai_services.knowledge.service import HybridKnowledgeService
from ai_services.llm.base import LLMResponse, LLMUnavailableError
from ai_services.ml.predictor import NHANESPredictor
from ai_services.orchestration.graph import MultiAgentOrchestrator
from ai_services.orchestration.state import AgentStepTrace, AssessmentInput


class FakeLLM:
    provider_name = "fake"
    model_name = "fake-1"

    def __init__(
        self,
        fail: bool = False,
        text: str = "Giải thích tham khảo [1]. Đây không phải chẩn đoán y khoa.",
    ) -> None:
        self.fail = fail
        self.text = text
        self.calls: list[dict] = []

    def generate(self, messages, temperature: float = 0.1, json_mode: bool = False):
        self.calls.append(
            {"messages": messages, "temperature": temperature, "json_mode": json_mode}
        )
        if self.fail:
            raise LLMUnavailableError("offline")
        return LLMResponse(
            content=self.text,
            provider=self.provider_name,
            model=self.model_name,
            latency_ms=5,
        )

    def health_check(self) -> bool:
        return not self.fail


def _build(tmp_path: Path, llm: FakeLLM) -> MultiAgentOrchestrator:
    pred = NHANESPredictor(
        Path("ml_pipeline/artifacts/nhanes_hba1c_v2.joblib"),
        Path("ml_pipeline/artifacts/model_manifest.json"),
    )
    kb = HybridKnowledgeService(
        tmp_path / "chroma",
        tmp_path / "kg.json",
        use_lightweight_embedder=True,
    )
    kb.seed_default_sources_if_empty()
    return MultiAgentOrchestrator(pred, kb, llm)


def test_assessment_runs_all_five_agents_and_preserves_ml_score(tmp_path: Path):
    orch = _build(tmp_path, FakeLLM())
    res = orch.run_assessment(
        "req-1",
        {
            "age": 55,
            "gender": 1,
            "height_cm": 170,
            "weight_kg": 88,
            "waist_cm": 102,
            "hip_cm": 100,
        },
    )
    assert res["status"] == "completed"
    assert res["prediction"]["model_score"] >= 0.0
    assert [s["agent_name"] for s in res["agent_steps"]] == [
        "orchestrator",
        "data_analysis",
        "prediction",
        "knowledge",
        "consultation",
    ]
    assert len(res["citations"]) >= 1
    assert res["derived_features"]["bmi"] == 30.45
    assert res["llm_used"] is True
    assert res["llm_fallback"] is False
    assert res["llm_provider"] == "fake"
    assert res["llm_model"] == "fake-1"
    assert isinstance(res["total_latency_ms"], int) and res["total_latency_ms"] >= 0

    # Verify Pydantic models work as documented and step summaries never leak raw biometrics
    parsed_input = AssessmentInput(
        age=55, gender=1, height_cm=170, weight_kg=88, waist_cm=102, hip_cm=100
    )
    assert parsed_input.age == 55
    for step in res["agent_steps"]:
        AgentStepTrace.model_validate(step)
        for raw_token in ("55", "170", "88", "102", "100", "30.45"):
            assert raw_token not in step["summary"]


def test_assessment_out_of_scope_skips_prediction(tmp_path: Path):
    orch = _build(tmp_path, FakeLLM())
    for bad in [
        {"age": 16, "gender": 1, "height_cm": 170, "weight_kg": 65, "waist_cm": 80},
        {
            "age": 40,
            "gender": 2,
            "height_cm": 160,
            "weight_kg": 60,
            "waist_cm": 85,
            "is_pregnant": True,
        },
        {
            "age": 50,
            "gender": 1,
            "height_cm": 170,
            "weight_kg": 80,
            "waist_cm": 95,
            "previously_diagnosed_diabetes": True,
        },
        {"age": 85, "gender": 1, "height_cm": 168, "weight_kg": 70, "waist_cm": 90},
    ]:
        res = orch.run_assessment("req-oos", bad)
        assert res["status"] == "out_of_scope"
        assert res["prediction"] is None
        assert "prediction" not in [s["agent_name"] for s in res["agent_steps"]]
        assert len(res["summary_text"]) > 10


def test_assessment_needs_input_skips_prediction(tmp_path: Path):
    orch = _build(tmp_path, FakeLLM())
    for invalid in [
        {"age": 40, "gender": 3, "height_cm": 170, "weight_kg": 70, "waist_cm": 85},
        {"age": 40, "gender": 1, "height_cm": 90, "weight_kg": 70, "waist_cm": 85},
        {"age": 40, "gender": 1, "height_cm": 170, "weight_kg": 20, "waist_cm": 85},
        {"age": 40, "gender": 1, "height_cm": 170, "weight_kg": 70, "waist_cm": 40},
        {
            "age": 40,
            "gender": 1,
            "height_cm": 170,
            "weight_kg": 70,
            "waist_cm": 85,
            "hip_cm": 45,
        },
        {"age": 40, "gender": 1, "height_cm": 170, "weight_kg": 70},
    ]:
        res = orch.run_assessment("req-bad", invalid)
        assert res["status"] == "needs_input"
        assert res["prediction"] is None
        assert "prediction" not in [s["agent_name"] for s in res["agent_steps"]]


def test_assessment_and_chat_gracefully_fallback_when_ollama_offline(tmp_path: Path):
    orch = _build(tmp_path, FakeLLM(fail=True))
    res = orch.run_assessment(
        "req-fb",
        {"age": 52, "gender": 2, "height_cm": 158, "weight_kg": 72, "waist_cm": 92},
    )
    assert res["status"] == "completed" and res["llm_fallback"] is True
    assert res["llm_used"] is False
    assert res["prediction"] is not None and len(res["summary_text"]) > 20
    assert str(res["prediction"]["model_score"]) in res["summary_text"] or (
        f"{res['prediction']['model_score'] * 100:.1f}%" in res["summary_text"]
    )
    assert "[1]" in res["summary_text"]

    chat = orch.run_chat("req-c1", "Chỉ số HbA1c bao nhiêu là tiền tiểu đường?")
    assert chat["status"] == "completed" and chat["llm_fallback"] is True
    assert chat["llm_used"] is False
    assert len(chat["citations"]) >= 1
    assert "[1]" in chat["answer"]


def test_chat_redirects_biometric_scoring_and_blocks_prescription(tmp_path: Path):
    orch = _build(tmp_path, FakeLLM())
    r_rx = orch.run_chat("req-rx", "Tôi nên tiêm bao nhiêu đơn vị insulin mỗi ngày?")
    assert r_rx["safety_flag"] == "prescription"
    assert r_rx["intent"] == "safety_guardrail"
    assert "knowledge" not in [s["agent_name"] for s in r_rx["agent_steps"]]

    r_score = orch.run_chat(
        "req-sc",
        "Tôi 50 tuổi, cao 170cm, nặng 85kg, vòng eo 100cm, hãy dự đoán nguy cơ tiểu đường giúp tôi",
    )
    assert r_score["redirect_to_assessment"] is True
    assert r_score["intent"] == "risk_assessment_redirect"
    assert [s["agent_name"] for s in r_score["agent_steps"]] == [
        "orchestrator",
        "consultation",
    ]
    assert "/assessment" in r_score["answer"]


def test_chat_explain_assessment_and_output_safety_postcheck(tmp_path: Path):
    unsafe_llm = FakeLLM(
        text="Bạn chắc chắn đã mắc bệnh tiểu đường. Hãy uống metformin 500 mg mỗi ngày."
    )
    orch = _build(tmp_path, unsafe_llm)
    linked = {
        "status": "completed",
        "derived_features": {"bmi": 28.5, "whtr": 0.56, "whr": 0.95},
        "prediction": {
            "model_version": "nhanes_hba1c_v2",
            "model_score": 0.62,
            "risk_band": "elevated",
            "predicted_label": 1,
            "threshold_low": 0.3,
            "threshold_high": 0.55,
            "feature_contributions": [
                {
                    "feature": "BMXWAIST",
                    "label_vi": "Vòng eo (cm)",
                    "value": 98,
                    "contribution": 0.42,
                    "direction": "increase",
                }
            ],
        },
    }
    chat = orch.run_chat(
        "req-exp",
        "Giải thích giúp tôi kết quả đánh giá nguy cơ vừa rồi",
        linked_assessment=linked,
    )
    assert chat["status"] == "completed"
    assert chat["intent"] == "explain_assessment"
    assert chat["llm_fallback"] is True
    assert chat["llm_used"] is False
    assert [s["agent_name"] for s in chat["agent_steps"]] == [
        "orchestrator",
        "knowledge",
        "consultation",
    ]
    assert "chắc chắn đã mắc" not in chat["answer"].lower()


def test_chat_out_of_domain_refuses_without_relevant_evidence(tmp_path: Path):
    llm = FakeLLM()
    orch = _build(tmp_path, llm)
    chat = orch.run_chat("req-ood", "Dự báo thời tiết Hà Nội và tỷ giá vàng hôm nay thế nào?")
    assert chat["status"] == "completed"
    assert chat["intent"] == "general_qa"
    assert chat["citations"] == []
    assert chat["llm_used"] is False
    assert len(llm.calls) == 0

"""Run: python -m phase5.step1_self_test

Deterministic contract tests: no API, LLM, model, DB, files modified.
"""
from __future__ import annotations
import unittest
from pydantic import ValidationError

from .contracts import (
    EXPECTED_SHA256, ResearchFeatures, WorkflowRequest, WorkflowResponse,
    EvidenceMetadata, UpstreamPrediction, make_initial_state,
)


def research_req(**overrides):
    data = {
        "request_id": "step1-syn-01", "operation": "research_prediction",
        "features": {"RIDAGEYR": 45, "RIAGENDR": 1, "BMXBMI": 28.5},
    }
    data.update(overrides)
    return data


def synthetic_req(**overrides):
    data = {"request_id": "step1-atlas-01", "operation": "synthetic_rag_demo", "question": "Atlas co may mo-dun?"}
    data.update(overrides)
    return data


class TestContracts(unittest.TestCase):
    def test_01_valid_nhanes_synthetic(self):
        self.assertEqual(WorkflowRequest.model_validate(research_req()).features.RIDAGEYR, 45)

    def test_02_invalid_age(self):
        with self.assertRaises(ValidationError):
            WorkflowRequest.model_validate(research_req(features={"RIDAGEYR": 19, "RIAGENDR": 1, "BMXBMI": 28.5}))

    def test_03_invalid_sex_code(self):
        with self.assertRaises(ValidationError):
            WorkflowRequest.model_validate(research_req(features={"RIDAGEYR": 45, "RIAGENDR": 0, "BMXBMI": 28.5}))

    def test_04_invalid_bmi(self):
        with self.assertRaises(ValidationError):
            WorkflowRequest.model_validate(research_req(features={"RIDAGEYR": 45, "RIAGENDR": 1, "BMXBMI": 90.0}))

    def test_05_extra_field_forbidden(self):
        with self.assertRaises(ValidationError):
            WorkflowRequest.model_validate(research_req(knowledge_gate="SYNTHETIC_READY"))

    def test_06_modes_are_disjoint(self):
        with self.assertRaises(ValidationError):
            WorkflowRequest.model_validate(research_req(question="What is HbA1c?"))
        with self.assertRaises(ValidationError):
            WorkflowRequest.model_validate(synthetic_req(features={"RIDAGEYR": 45, "RIAGENDR": 1, "BMXBMI": 28.5}))

    def test_07_synthetic_only_enforced(self):
        with self.assertRaises(ValidationError):
            WorkflowRequest.model_validate(research_req(synthetic_test_only=False))

    def test_08_default_medical_gate_cannot_be_overridden(self):
        state = make_initial_state(WorkflowRequest.model_validate(research_req()))
        self.assertEqual(state["knowledge_gate"], "BLOCKED_RESEARCH_ONLY")
        self.assertFalse(state["llm_called"])

    def test_09_atlas_never_gets_medical_gate(self):
        state = make_initial_state(WorkflowRequest.model_validate(synthetic_req()))
        self.assertEqual(state["knowledge_gate"], "NOT_EVALUATED")
        self.assertNotIn("features", state["raw_input"])

    def test_10_medical_llm_bypass_forbidden(self):
        with self.assertRaises(ValidationError):
            WorkflowResponse(request_id="x", operation="research_prediction", status="ok",
                             knowledge_gate="SYNTHETIC_READY", llm_called=True)

    def test_11_medical_evidence_content_is_rejected(self):
        with self.assertRaises(ValidationError):
            EvidenceMetadata(chunk_id="c1", source_id="s1", review_status="draft_unverified",
                             provenance_match=True, full_text="unauthorized medical content")

        with self.assertRaises(ValidationError):
            EvidenceMetadata(chunk_id="c1", source_id="s1", review_status="draft_unverified",
                             provenance_match=True, allowed_to_answer=True)

    def test_12_prediction_identity_is_locked(self):
        with self.assertRaises(ValidationError):
            UpstreamPrediction(status="research_only", task="classify_hba1c_ge_5_7_indicator",
                               model_name="LogisticRegression", model_sha256="wrong", threshold=0.225,
                               model_score=0.8, predicted_label=1, warning="research-only")

    def test_13_prediction_label_consistency(self):
        with self.assertRaises(ValidationError):
            UpstreamPrediction(status="research_only", task="classify_hba1c_ge_5_7_indicator",
                               model_name="LogisticRegression", model_sha256=EXPECTED_SHA256,
                               threshold=0.225, model_score=0.9, predicted_label=0,
                               warning="research-only")

    def test_14_no_fake_prediction_on_unconnected_workflow(self):
        with self.assertRaises(ValidationError):
            WorkflowResponse(request_id="x", operation="research_prediction", status="not_connected",
                             knowledge_gate="BLOCKED_RESEARCH_ONLY", prediction={
                                 "status": "research_only", "task": "classify_hba1c_ge_5_7_indicator",
                                 "model_name": "LogisticRegression", "model_sha256": EXPECTED_SHA256,
                                 "threshold": 0.225, "model_score": 0.8, "predicted_label": 1,
                                 "warning": "research-only",
                             })


if __name__ == "__main__":
    unittest.main(verbosity=2)

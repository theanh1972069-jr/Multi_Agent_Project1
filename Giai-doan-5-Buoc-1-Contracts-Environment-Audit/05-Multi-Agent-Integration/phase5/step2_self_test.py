"""Step 2 unit tests use only MOCK fixtures. NO localhost/network/model/DB."""
from __future__ import annotations

import unittest
from pydantic import ValidationError
from .contracts import ResearchFeatures, WorkflowRequest, THRESHOLD, EXPECTED_SHA256
from .step2_prediction_integration import (
    IntegrationFailure, MockPredictionClient, parse_upstream_prediction,
    validate_loopback_predict_url,
)


class Step2ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = ResearchFeatures(RIDAGEYR=45, RIAGENDR=1, BMXBMI=28.5)

    def test_valid_fixture(self):
        r = MockPredictionClient().predict(self.fx)
        self.assertEqual(r.model_sha256, EXPECTED_SHA256)
        self.assertEqual(r.threshold, THRESHOLD)

    def test_bad_hash_blocked(self):
        with self.assertRaises(IntegrationFailure):
            MockPredictionClient("bad_hash").predict(self.fx)

    def test_bad_threshold_blocked(self):
        with self.assertRaises(IntegrationFailure):
            MockPredictionClient("bad_threshold").predict(self.fx)

    def test_bad_label_blocked(self):
        with self.assertRaises(IntegrationFailure):
            MockPredictionClient("bad_label").predict(self.fx)

    def test_misleading_warning_blocked(self):
        with self.assertRaises(IntegrationFailure):
            MockPredictionClient("bad_warning").predict(self.fx)

    def test_service_unavailable(self):
        with self.assertRaises(IntegrationFailure) as ctx:
            MockPredictionClient("unavailable").predict(self.fx)
        self.assertEqual(ctx.exception.code, "UPSTREAM_UNAVAILABLE")

    def test_invalid_age(self):
        with self.assertRaises(ValidationError):
            ResearchFeatures(RIDAGEYR=19, RIAGENDR=1, BMXBMI=28.5)

    def test_invalid_gender(self):
        with self.assertRaises(ValidationError):
            ResearchFeatures(RIDAGEYR=45, RIAGENDR=0, BMXBMI=28.5)

    def test_invalid_bmi(self):
        with self.assertRaises(ValidationError):
            ResearchFeatures(RIDAGEYR=45, RIAGENDR=1, BMXBMI=float("nan"))

    def test_unknown_user_gate_forbidden(self):
        with self.assertRaises(ValidationError):
            WorkflowRequest.model_validate({
                "request_id": "test", "operation": "research_prediction",
                "features": self.fx.model_dump(), "knowledge_gate": "SYNTHETIC_READY",
            })

    def test_external_host_blocked(self):
        with self.assertRaises(IntegrationFailure):
            validate_loopback_predict_url("https://example.com/api/v1/research/nhanes/hba1c/predict")

    def test_redirect_url_blocked(self):
        with self.assertRaises(IntegrationFailure):
            validate_loopback_predict_url("http://127.0.0.1:8000/api/v1/research/nhanes/hba1c/predict?x=1")

    def test_local_url_allowed(self):
        s = "http://127.0.0.1:8000/api/v1/research/nhanes/hba1c/predict"
        self.assertEqual(validate_loopback_predict_url(s), s)

    def test_missing_field_blocked(self):
        with self.assertRaises(IntegrationFailure):
            parse_upstream_prediction({"status": "research_only"})

    def test_non_dictionary_blocked(self):
        with self.assertRaises(IntegrationFailure):
            parse_upstream_prediction("unsafe")

    def test_real_data_not_allowed(self):
        with self.assertRaises(ValidationError):
            WorkflowRequest.model_validate({
                "request_id": "test", "operation": "research_prediction",
                "synthetic_test_only": False, "features": self.fx.model_dump(),
            })


if __name__ == "__main__":
    unittest.main(verbosity=2)

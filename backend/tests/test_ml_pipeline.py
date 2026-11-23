import json
from pathlib import Path

import pytest

from ai_services.ml.predictor import ModelIntegrityError, NHANESPredictor

ARTIFACTS = Path("ml_pipeline/artifacts")


def test_manifest_and_comparison_report_exist_and_beat_or_match_baseline():
    manifest = json.loads((ARTIFACTS / "model_manifest.json").read_text(encoding="utf-8"))
    comp = json.loads((ARTIFACTS / "comparison_report.json").read_text(encoding="utf-8"))
    assert manifest["features"] == ["RIDAGEYR", "RIAGENDR", "BMXBMI", "BMXWAIST", "WHtR", "WHR"]
    assert 0.0 < manifest["thresholds"]["low"] < manifest["thresholds"]["high"] < 1.0
    assert manifest["test_metrics"]["roc_auc"] > 0.70
    assert manifest["model_sha256"] == manifest["sha256"]
    assert "gd3_baseline_3feat" in comp


def test_predictor_returns_calibrated_score_and_local_contributions():
    pred = NHANESPredictor(ARTIFACTS / "nhanes_hba1c_v2.joblib", ARTIFACTS / "model_manifest.json")
    out = pred.predict({"RIDAGEYR": 58, "RIAGENDR": 1, "BMXBMI": 31.5, "BMXWAIST": 106.0, "WHtR": 0.62, "WHR": 1.02})
    assert 0.0 <= out["model_score"] <= 1.0
    assert out["risk_band"] in {"low", "moderate", "elevated"}
    assert len(out["feature_contributions"]) == 6
    assert all(c["direction"] in {"increase", "decrease"} for c in out["feature_contributions"])
    abs_contribs = [abs(c["contribution"]) for c in out["feature_contributions"]]
    assert abs_contribs == sorted(abs_contribs, reverse=True)
    assert "HbA1c" in out["warning"]


def test_predictor_handles_missing_optional_whr_via_imputation():
    pred = NHANESPredictor(ARTIFACTS / "nhanes_hba1c_v2.joblib", ARTIFACTS / "model_manifest.json")
    out = pred.predict({"RIDAGEYR": 42, "RIAGENDR": 2, "BMXBMI": 24.0, "BMXWAIST": 78.0, "WHtR": 0.48, "WHR": None})
    assert 0.0 <= out["model_score"] <= 1.0
    assert out["predicted_label"] in {0, 1}
    assert len(out["feature_contributions"]) == 6


def test_predictor_fails_closed_on_sha256_mismatch(tmp_path):
    bad_manifest = json.loads((ARTIFACTS / "model_manifest.json").read_text(encoding="utf-8"))
    bad_manifest["model_sha256"] = "0" * 64
    p = tmp_path / "bad_manifest.json"
    p.write_text(json.dumps(bad_manifest), encoding="utf-8")
    with pytest.raises(ModelIntegrityError):
        NHANESPredictor(ARTIFACTS / "nhanes_hba1c_v2.joblib", p)


def test_predictor_fails_closed_on_alt_sha256_key_mismatch(tmp_path):
    bad_manifest = json.loads((ARTIFACTS / "model_manifest.json").read_text(encoding="utf-8"))
    bad_manifest["sha256"] = "f" * 64
    p = tmp_path / "bad_manifest_alt.json"
    p.write_text(json.dumps(bad_manifest), encoding="utf-8")
    with pytest.raises(ModelIntegrityError):
        NHANESPredictor(ARTIFACTS / "nhanes_hba1c_v2.joblib", p)


def test_predictor_risk_bands_and_manifest_property():
    pred = NHANESPredictor(ARTIFACTS / "nhanes_hba1c_v2.joblib", ARTIFACTS / "model_manifest.json")
    assert pred.manifest["model_version"]
    low_profile = pred.predict({"RIDAGEYR": 23, "RIAGENDR": 2, "BMXBMI": 19.5, "BMXWAIST": 66.0, "WHtR": 0.40, "WHR": 0.72})
    high_profile = pred.predict({"RIDAGEYR": 72, "RIAGENDR": 1, "BMXBMI": 36.0, "BMXWAIST": 120.0, "WHtR": 0.72, "WHR": 1.10})
    assert low_profile["model_score"] < high_profile["model_score"]
    assert low_profile["risk_band"] == "low"
    assert high_profile["risk_band"] in {"moderate", "elevated"}

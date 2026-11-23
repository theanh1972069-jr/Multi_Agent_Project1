from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from ml_pipeline.explain import FEATURES, compute_local_contributions

SCREENING_WARNING_VI = (
    "Kết quả chỉ phản ánh chỉ dấu sàng lọc HbA1c >= 5.7% dựa trên dữ liệu khảo sát NHANES 2021–2023, "
    "KHÔNG phải chẩn đoán bệnh tiểu đường hay dự báo nguy cơ mắc bệnh trong tương lai."
)


class ModelIntegrityError(Exception):
    """Raised when the serialized ML artifact fails SHA256 verification against its manifest."""


def _compute_file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class NHANESPredictor:
    """SHA256-verified runtime predictor for the NHANES v2 HbA1c screening model."""

    def __init__(self, artifact_path: Path | str, manifest_path: Path | str) -> None:
        self._artifact_path = Path(artifact_path)
        self._manifest_path = Path(manifest_path)

        if not self._manifest_path.is_file():
            raise ModelIntegrityError(f"Model manifest not found: {self._manifest_path}")
        if not self._artifact_path.is_file():
            raise ModelIntegrityError(f"Model artifact not found: {self._artifact_path}")

        self._manifest: dict[str, Any] = json.loads(self._manifest_path.read_text(encoding="utf-8"))
        actual_sha256 = _compute_file_sha256(self._artifact_path)

        expected_keys = [
            self._manifest.get(k) for k in ("model_sha256", "sha256") if self._manifest.get(k) is not None
        ]
        if not expected_keys or any(str(expected).lower() != actual_sha256.lower() for expected in expected_keys):
            raise ModelIntegrityError(
                "Model artifact SHA256 mismatch against manifest; refusing to load unverified model."
            )

        self._actual_sha256 = actual_sha256
        self._pipeline = joblib.load(self._artifact_path)

    @property
    def manifest(self) -> dict[str, Any]:
        """Return a shallow copy of the verified model manifest dictionary."""
        return dict(self._manifest)

    def predict(self, features: dict[str, float | int | None]) -> dict[str, Any]:
        """Score a single profile and attach local feature contributions and screening disclaimer."""
        feature_order: list[str] = list(self._manifest.get("features", FEATURES))
        row_values: dict[str, list[float]] = {}
        for feat in feature_order:
            val = features.get(feat)
            if val is None:
                row_values[feat] = [float("nan")]
            else:
                num_val = float(val)
                row_values[feat] = [num_val]

        row_df = pd.DataFrame(row_values, columns=feature_order)
        probs = np.asarray(self._pipeline.predict_proba(row_df), dtype=float)
        score = float(probs[0, 1])

        if not math.isfinite(score) or score < 0.0 or score > 1.0:
            raise ValueError(f"Model produced invalid probability score: {score!r}")

        thresholds = self._manifest["thresholds"]
        t_low = float(thresholds["low"])
        t_high = float(thresholds["high"])

        if score < t_low:
            risk_band = "low"
        elif score < t_high:
            risk_band = "moderate"
        else:
            risk_band = "elevated"

        predicted_label = int(score >= t_low)
        contributions = compute_local_contributions(self._pipeline, row_df, features)

        return {
            "model_version": self._manifest["model_version"],
            "model_name": self._manifest["model_name"],
            "model_sha256": self._actual_sha256,
            "threshold_low": t_low,
            "threshold_high": t_high,
            "model_score": round(score, 6),
            "predicted_label": predicted_label,
            "risk_band": risk_band,
            "feature_contributions": contributions,
            "warning": SCREENING_WARNING_VI,
            "limitations": list(self._manifest.get("limitations", [])),
        }

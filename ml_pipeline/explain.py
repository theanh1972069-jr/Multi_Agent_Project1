from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

FEATURES: list[str] = [
    "RIDAGEYR",
    "RIAGENDR",
    "BMXBMI",
    "BMXWAIST",
    "WHtR",
    "WHR",
]

NUMERIC_FEATURES: list[str] = [
    "RIDAGEYR",
    "BMXBMI",
    "BMXWAIST",
    "WHtR",
    "WHR",
]

CATEGORICAL_FEATURES: list[str] = ["RIAGENDR"]

FEATURE_LABELS_VI: dict[str, str] = {
    "RIDAGEYR": "Tuổi",
    "RIAGENDR": "Giới tính",
    "BMXBMI": "Chỉ số BMI",
    "BMXWAIST": "Vòng eo (cm)",
    "WHtR": "Tỷ lệ Vòng eo / Chiều cao",
    "WHR": "Tỷ lệ Vòng eo / Vòng hông",
}


def _clean_feature_value(raw: float | int | None) -> float | int | None:
    if raw is None:
        return None
    if isinstance(raw, (float, np.floating)) and math.isnan(float(raw)):
        return None
    if isinstance(raw, (int, np.integer)):
        return int(raw)
    return round(float(raw), 4)


def _extract_reference_values(pipeline: Pipeline) -> dict[str, Any]:
    preprocessor = pipeline.named_steps["preprocessor"]
    num_imputer = preprocessor.named_transformers_["num"].named_steps["imputer"]
    cat_imputer = preprocessor.named_transformers_["cat"].named_steps["imputer"]
    refs: dict[str, Any] = dict(zip(NUMERIC_FEATURES, num_imputer.statistics_))
    refs["RIAGENDR"] = cat_imputer.statistics_[0]
    return refs


def _compute_linear_contributions(
    pipeline: Pipeline,
    row_df: pd.DataFrame,
) -> dict[str, float]:
    preprocessor = pipeline.named_steps["preprocessor"]
    classifier: LogisticRegression = pipeline.named_steps["classifier"]
    x_trans = np.asarray(preprocessor.transform(row_df), dtype=float)
    feature_names = list(preprocessor.get_feature_names_out())
    coefs = np.asarray(classifier.coef_[0], dtype=float)

    contributions: dict[str, float] = {}
    for feat in NUMERIC_FEATURES:
        target_name = f"num__{feat}"
        idx = feature_names.index(target_name)
        contributions[feat] = float(coefs[idx] * x_trans[0, idx])

    cat_indices = [i for i, name in enumerate(feature_names) if name.startswith("cat__RIAGENDR_")]
    if cat_indices:
        cat_mean_coef = float(np.mean([coefs[i] for i in cat_indices]))
        cat_raw = float(sum(coefs[i] * x_trans[0, i] for i in cat_indices))
        contributions["RIAGENDR"] = cat_raw - cat_mean_coef
    else:
        contributions["RIAGENDR"] = 0.0

    return contributions


def _compute_perturbation_contributions(
    pipeline: Pipeline,
    row_df: pd.DataFrame,
) -> dict[str, float]:
    refs = _extract_reference_values(pipeline)
    base_score = float(pipeline.predict_proba(row_df)[0, 1])
    contributions: dict[str, float] = {}
    for feat in FEATURES:
        perturbed = row_df.copy()
        perturbed[feat] = refs[feat]
        ref_score = float(pipeline.predict_proba(perturbed)[0, 1])
        contributions[feat] = base_score - ref_score
    return contributions


def compute_local_contributions(
    pipeline: Pipeline,
    row_df: pd.DataFrame,
    feature_values: dict[str, float | int | None],
) -> list[dict[str, Any]]:
    """Compute local per-feature contributions for a single NHANES v2 profile.

    Uses exact mean-centered log-odds contributions when the final estimator is
    ``LogisticRegression``, and single-feature median/mode reference perturbation
    for non-linear tree pipelines.
    """
    classifier = pipeline.named_steps["classifier"]
    if isinstance(classifier, LogisticRegression):
        raw_contribs = _compute_linear_contributions(pipeline, row_df)
    else:
        raw_contribs = _compute_perturbation_contributions(pipeline, row_df)

    results: list[dict[str, Any]] = []
    for feat in FEATURES:
        contrib = float(raw_contribs[feat])
        results.append(
            {
                "feature": feat,
                "label_vi": FEATURE_LABELS_VI[feat],
                "value": _clean_feature_value(feature_values.get(feat)),
                "contribution": round(contrib, 6),
                "direction": "increase" if contrib > 0.0 else "decrease",
            }
        )

    results.sort(key=lambda item: abs(item["contribution"]), reverse=True)
    return results

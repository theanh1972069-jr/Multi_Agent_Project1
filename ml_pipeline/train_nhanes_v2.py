from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    fbeta_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml_pipeline.explain import CATEGORICAL_FEATURES, FEATURE_LABELS_VI, FEATURES, NUMERIC_FEATURES

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = REPO_ROOT / "GĐ3" / "03-ML-Research" / "data" / "raw"
DEFAULT_GD3_BASELINE_PATH = (
    REPO_ROOT
    / "GĐ3"
    / "03-ML-Research"
    / "data"
    / "outputs"
    / "model_evaluation"
    / "test_6b_FINAL"
    / "06b_test_final_results.json"
)
DEFAULT_ARTIFACTS_DIR = REPO_ROOT / "ml_pipeline" / "artifacts"

RANDOM_STATE = 42
MODEL_VERSION = "nhanes_hba1c_v2.0.0"

LIMITATIONS = [
    "NHANES 2021-2023 cross-sectional survey: only classifies observed HbA1c >= 5.7%.",
    "Not a clinical diabetes diagnosis or a longitudinal forecast of future type 2 diabetes.",
    "NHANES complex survey weights (WTPH2YR) were not applied during model fitting.",
    "Pregnancy status (RIDEXPRG) is only published for women aged 20-44; NaN rows are retained after excluding confirmed RIDEXPRG == 1.",
    "Local feature contributions indicate statistical contribution to the model score, not causal etiology.",
]


def load_nhanes_screening_cohort(raw_dir: Path) -> tuple[pd.DataFrame, pd.Series]:
    """Load NHANES 2021-2023 XPT tables and construct the 6-feature screening_candidate cohort."""
    demo = pd.read_sas(raw_dir / "DEMO_L.xpt")[["SEQN", "RIDAGEYR", "RIAGENDR", "RIDEXPRG"]]
    bmx = pd.read_sas(raw_dir / "BMX_L.xpt")[["SEQN", "BMXBMI", "BMXWAIST", "BMXHT", "BMXHIP"]]
    diq = pd.read_sas(raw_dir / "DIQ_L.xpt")[["SEQN", "DIQ010"]]
    ghb = pd.read_sas(raw_dir / "GHB_L.xpt")[["SEQN", "LBXGH"]]

    merged = (
        demo.merge(bmx, on="SEQN", how="left")
        .merge(diq, on="SEQN", how="left")
        .merge(ghb, on="SEQN", how="left")
    )

    cohort = merged[
        (merged["RIDAGEYR"] >= 20)
        & (merged["DIQ010"] == 2)
        & (~(merged["RIDEXPRG"] == 1))
        & (merged["LBXGH"].notna())
    ].copy()

    cohort["WHtR"] = np.where(cohort["BMXHT"] > 0, cohort["BMXWAIST"] / cohort["BMXHT"], np.nan)
    cohort["WHR"] = np.where(cohort["BMXHIP"] > 0, cohort["BMXWAIST"] / cohort["BMXHIP"], np.nan)

    X = cohort[FEATURES].astype(float).reset_index(drop=True)
    y = (cohort["LBXGH"] >= 5.7).astype(int).reset_index(drop=True)
    return X, y


def build_preprocessor() -> ColumnTransformer:
    """Create leakage-safe ColumnTransformer for NHANES v2 numeric and categorical features."""
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )


def build_candidate_pipelines() -> dict[str, Pipeline]:
    """Build the 3 candidate sklearn pipelines to compare on Validation."""
    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=200,
            max_depth=8,
            random_state=RANDOM_STATE,
        ),
        "HistGradientBoostingClassifier": HistGradientBoostingClassifier(
            max_depth=4,
            learning_rate=0.05,
            random_state=RANDOM_STATE,
        ),
    }
    return {
        name: Pipeline(steps=[("preprocessor", build_preprocessor()), ("classifier", clf)])
        for name, clf in candidates.items()
    }


def compute_binary_metrics(y_true: pd.Series | np.ndarray, y_prob: np.ndarray, threshold: float) -> dict[str, Any]:
    """Compute threshold-independent and thresholded binary classification metrics."""
    y_arr = np.asarray(y_true, dtype=int)
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_arr, y_pred, labels=[0, 1]).ravel()
    specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    return {
        "threshold": round(float(threshold), 4),
        "n": int(len(y_arr)),
        "positive_n": int(y_arr.sum()),
        "positive_rate": float(y_arr.mean()),
        "roc_auc": float(roc_auc_score(y_arr, y_prob)),
        "average_precision": float(average_precision_score(y_arr, y_prob)),
        "brier_score": float(brier_score_loss(y_arr, y_prob)),
        "log_loss": float(log_loss(y_arr, y_prob)),
        "precision": float(precision_score(y_arr, y_pred, zero_division=0)),
        "recall": float(recall_score(y_arr, y_pred, zero_division=0)),
        "specificity": specificity,
        "f1": float(f1_score(y_arr, y_pred, zero_division=0)),
        "f2": float(fbeta_score(y_arr, y_pred, beta=2.0, zero_division=0)),
        "accuracy": float(accuracy_score(y_arr, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_arr, y_pred)),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def lock_validation_thresholds(y_val: pd.Series | np.ndarray, y_val_prob: np.ndarray) -> tuple[float, float]:
    """Lock low (Recall >= 0.80, max specificity) and high (max F1 > low) thresholds on Validation."""
    grid = np.round(np.arange(0.05, 0.955, 0.005), 4)
    y_arr = np.asarray(y_val, dtype=int)

    low_candidates: list[tuple[float, float, float]] = []
    for t in grid:
        y_pred = (y_val_prob >= t).astype(int)
        rec = float(recall_score(y_arr, y_pred, zero_division=0))
        if rec >= 0.80:
            tn, fp, _, _ = confusion_matrix(y_arr, y_pred, labels=[0, 1]).ravel()
            spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
            low_candidates.append((spec, -float(t), float(t)))

    if not low_candidates:
        # Defensive fallback if recall never reaches 0.80 on the standard grid.
        best_t = float(min(grid, key=lambda t: abs(recall_score(y_arr, (y_val_prob >= t).astype(int)) - 0.80)))
        t_low = best_t
    else:
        # Highest specificity among thresholds with Recall >= 0.80; lowest threshold breaks exact ties.
        t_low = max(low_candidates)[2]

    high_candidates: list[tuple[float, float, float]] = []
    for t in grid:
        if t <= t_low:
            continue
        y_pred = (y_val_prob >= t).astype(int)
        f1 = float(f1_score(y_arr, y_pred, zero_division=0))
        prec = float(precision_score(y_arr, y_pred, zero_division=0))
        high_candidates.append((f1, prec, float(t)))

    if not high_candidates:
        t_high = round(min(0.95, t_low + 0.10), 4)
    else:
        t_high = max(high_candidates)[2]

    return round(t_low, 4), round(t_high, 4)


def _compute_training_feature_stats(X_train: pd.DataFrame) -> dict[str, Any]:
    stats: dict[str, Any] = {}
    for feat in NUMERIC_FEATURES:
        col = X_train[feat].dropna()
        stats[feat] = {
            "median": round(float(col.median()), 4),
            "mean": round(float(col.mean()), 4),
            "std": round(float(col.std(ddof=0)), 4),
            "min": round(float(col.min()), 4),
            "max": round(float(col.max()), 4),
            "missing_train_n": int(X_train[feat].isna().sum()),
        }
    gender_counts = X_train["RIAGENDR"].value_counts(dropna=False).to_dict()
    stats["RIAGENDR"] = {
        "counts": {str(int(k)): int(v) for k, v in gender_counts.items() if pd.notna(k)},
        "missing_train_n": int(X_train["RIAGENDR"].isna().sum()),
    }
    return stats


def load_gd3_baseline_metrics(baseline_path: Path) -> dict[str, Any]:
    """Read GĐ3 3-feature baseline final test metrics without modifying GĐ3."""
    return json.loads(baseline_path.read_text(encoding="utf-8"))


def train_and_export(
    raw_dir: Path = DEFAULT_RAW_DIR,
    gd3_baseline_path: Path = DEFAULT_GD3_BASELINE_PATH,
    artifacts_dir: Path = DEFAULT_ARTIFACTS_DIR,
) -> dict[str, Any]:
    """Run full leak-free NHANES v2 training, validation selection, test evaluation, and artifact export."""
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    X, y = load_nhanes_screening_cohort(raw_dir)

    # Exact 70 / 15 / 15 stratified split matching GĐ3 seed=42
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.15, stratify=y, random_state=RANDOM_STATE
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val,
        y_train_val,
        test_size=0.15 / 0.85,
        stratify=y_train_val,
        random_state=RANDOM_STATE,
    )

    pipelines = build_candidate_pipelines()
    val_results: dict[str, dict[str, Any]] = {}
    val_probs: dict[str, np.ndarray] = {}

    for name, pipe in pipelines.items():
        pipe.fit(X_train, y_train)
        prob = pipe.predict_proba(X_val)[:, 1]
        val_probs[name] = prob
        val_results[name] = {
            "roc_auc": float(roc_auc_score(y_val, prob)),
            "average_precision": float(average_precision_score(y_val, prob)),
            "brier_score": float(brier_score_loss(y_val, prob)),
            "log_loss": float(log_loss(y_val, prob)),
        }

    # Select winner on Validation ROC-AUC, tiebreaking with lowest Brier score
    winner_name = max(
        val_results.keys(),
        key=lambda n: (round(val_results[n]["roc_auc"], 6), -val_results[n]["brier_score"]),
    )
    winner_pipe = pipelines[winner_name]
    winner_val_prob = val_probs[winner_name]

    t_low, t_high = lock_validation_thresholds(y_val, winner_val_prob)
    val_at_low = compute_binary_metrics(y_val, winner_val_prob, t_low)
    val_at_high = compute_binary_metrics(y_val, winner_val_prob, t_high)

    # Single evaluation on holdout Test at locked thresholds
    test_prob = winner_pipe.predict_proba(X_test)[:, 1]
    test_at_low = compute_binary_metrics(y_test, test_prob, t_low)
    test_at_high = compute_binary_metrics(y_test, test_prob, t_high)

    model_path = artifacts_dir / "nhanes_hba1c_v2.joblib"
    joblib.dump(winner_pipe, model_path)
    model_sha256 = hashlib.sha256(model_path.read_bytes()).hexdigest()

    gd3_baseline = load_gd3_baseline_metrics(gd3_baseline_path)
    baseline_comparison = {
        "gd3_model": gd3_baseline["model"],
        "gd3_features": gd3_baseline["features"],
        "gd3_test_roc_auc": float(gd3_baseline["roc_auc"]),
        "gd3_test_average_precision": float(gd3_baseline["average_precision"]),
        "gd3_test_brier_score": float(gd3_baseline["brier_score"]),
        "v2_test_roc_auc": test_at_low["roc_auc"],
        "v2_test_average_precision": test_at_low["average_precision"],
        "v2_test_brier_score": test_at_low["brier_score"],
        "roc_auc_delta": round(test_at_low["roc_auc"] - float(gd3_baseline["roc_auc"]), 6),
        "average_precision_delta": round(
            test_at_low["average_precision"] - float(gd3_baseline["average_precision"]), 6
        ),
        "brier_score_delta": round(test_at_low["brier_score"] - float(gd3_baseline["brier_score"]), 6),
    }

    trained_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "model_version": MODEL_VERSION,
        "model_name": winner_name,
        "model_sha256": model_sha256,
        "sha256": model_sha256,
        "trained_at_utc": trained_at,
        "source": "NHANES August 2021-August 2023 (DEMO_L, BMX_L, DIQ_L, GHB_L)",
        "cohort": "screening_candidate (RIDAGEYR >= 20, DIQ010 == 2, RIDEXPRG != 1, LBXGH notna)",
        "target": "LBXGH >= 5.7% (HbA1c screening indicator)",
        "features": FEATURES,
        "feature_labels_vi": FEATURE_LABELS_VI,
        "split": {
            "total_n": int(len(X)),
            "total_positive_n": int(y.sum()),
            "train_n": int(len(X_train)),
            "val_n": int(len(X_val)),
            "test_n": int(len(X_test)),
            "random_state": RANDOM_STATE,
            "stratified": True,
        },
        "feature_stats": _compute_training_feature_stats(X_train),
        "thresholds": {
            "low": t_low,
            "high": t_high,
            "low_criterion": "Highest Validation specificity with Recall >= 0.80",
            "high_criterion": "Highest Validation F1 among thresholds > low",
        },
        "validation_metrics": {
            **val_at_low,
            "at_threshold_high": val_at_high,
        },
        "test_metrics": {
            **test_at_low,
            "at_threshold_high": test_at_high,
        },
        "baseline_comparison": baseline_comparison,
        "limitations": LIMITATIONS,
    }
    (artifacts_dir / "model_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    comparison_report = {
        "generated_at_utc": trained_at,
        "model_version": MODEL_VERSION,
        "cohort_n": int(len(X)),
        "positive_n": int(y.sum()),
        "split_counts": {
            "train": int(len(X_train)),
            "val": int(len(X_val)),
            "test": int(len(X_test)),
        },
        "selected_model": winner_name,
        "selection_criterion": "Highest Validation ROC-AUC (tiebreaker: lowest Validation Brier score)",
        "locked_thresholds": {"low": t_low, "high": t_high},
        "v2_candidates_validation": val_results,
        "v2_winner_validation": val_at_low,
        "v2_winner_test": test_at_low,
        "gd3_baseline_3feat": gd3_baseline,
        "comparison_summary": baseline_comparison,
    }
    (artifacts_dir / "comparison_report.json").write_text(
        json.dumps(comparison_report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return comparison_report


def main() -> None:
    report = train_and_export()
    print(f"Cohort: n={report['cohort_n']}, positives={report['positive_n']}")
    print(f"Split: {report['split_counts']}")
    print("\nValidation Comparison (6-feature NHANES v2 candidates):")
    print(f"{'Model':<32} {'ROC-AUC':>9} {'PR-AUC':>9} {'Brier':>9} {'LogLoss':>9}")
    for name, m in report["v2_candidates_validation"].items():
        marker = " *" if name == report["selected_model"] else ""
        print(
            f"{name + marker:<32} {m['roc_auc']:>9.4f} {m['average_precision']:>9.4f} "
            f"{m['brier_score']:>9.4f} {m['log_loss']:>9.4f}"
        )
    t_low = report["locked_thresholds"]["low"]
    t_high = report["locked_thresholds"]["high"]
    test_m = report["v2_winner_test"]
    gd3_m = report["gd3_baseline_3feat"]
    delta = report["comparison_summary"]
    print(f"\nWinner: {report['selected_model']} | Locked thresholds: low={t_low}, high={t_high}")
    print(
        f"Test v2 (n={test_m['n']}): ROC-AUC={test_m['roc_auc']:.4f}, PR-AUC={test_m['average_precision']:.4f}, "
        f"Brier={test_m['brier_score']:.4f}, Recall={test_m['recall']:.4f}, Spec={test_m['specificity']:.4f}, F1={test_m['f1']:.4f}"
    )
    print(
        f"Test GD3 3-feat baseline: ROC-AUC={gd3_m['roc_auc']:.4f}, PR-AUC={gd3_m['average_precision']:.4f}, "
        f"Brier={gd3_m['brier_score']:.4f}"
    )
    print(
        f"Delta (v2 - GD3): ROC-AUC={delta['roc_auc_delta']:+.4f}, "
        f"PR-AUC={delta['average_precision_delta']:+.4f}, Brier={delta['brier_score_delta']:+.4f}"
    )


if __name__ == "__main__":
    main()

"""Run Phase 5 Step 2 mock or explicit localhost inference smoke test.

Command examples:
  python -m phase5.step2_run --mode mock
  python -m phase5.step2_run --mode live

Outputs only fixture IDs, statuses and security flags (no feature payload).
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .contracts import EXPECTED_SHA256, WorkflowRequest
from .step1_environment_audit import CONFIG_LOCAL, _safe_config
from .step2_prediction_integration import IntegrationFailure, LocalFastAPIClient, MockPredictionClient, run_step2_graph

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "outputs" / "phase5_step2" / "step2_prediction_integration_report.json"

# Explicitly synthetic examples; no user/patient input accepted by this CLI.
FIXTURES = [
    ("SYN-PRED-01", 45, 1, 28.5),
    ("SYN-PRED-02", 60, 2, 34.8),
]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["mock", "live"], default="mock")
    p.add_argument("--config", type=Path, default=CONFIG_LOCAL)
    p.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = p.parse_args()
    if args.mode == "live":
        if not args.config.is_file():
            print("CONFIG_MISSING: copy example config to phase5_step1_config.json first")
            return 2
        try:
            config = _safe_config(json.loads(args.config.read_text(encoding="utf-8")))
            client = LocalFastAPIClient(config["prediction_api_url"] or "")
        except (IntegrationFailure, ValueError, TypeError, OSError, json.JSONDecodeError):
            print("INVALID_LOCAL_CONFIG: verify prediction_api_url (localhost only)")
            return 2
    else:
        client = MockPredictionClient()
    rows = []
    for name, age, gender, bmi in FIXTURES:
        req = WorkflowRequest.model_validate({
            "request_id": name, "operation": "research_prediction", "synthetic_test_only": True,
            "features": {"RIDAGEYR": age, "RIAGENDR": gender, "BMXBMI": float(bmi)},
        })
        try:
            response = run_step2_graph(client, req)
        except ImportError:
            print("MISSING_LANGGRAPH: python -m pip install 'langgraph>=1.0,<2'")
            return 2
        # This report contains no submitted features, no raw upstream error, no credentials.
        rows.append({
            "case_id": name,
            "status": response.status,
            "prediction_present": response.prediction is not None,
            "model_sha256_match": response.prediction.model_sha256 == EXPECTED_SHA256 if response.prediction else False,
            "threshold_match": response.prediction.threshold == 0.225 if response.prediction else False,
            "gate": response.knowledge_gate,
            "llm_called": response.llm_called,
            "error_codes": [e.code for e in response.errors],
            "research_only": response.prediction is not None and response.prediction.status == "research_only",
        })
    successes = sum(x["status"] == "ok" for x in rows)
    report = {
        "experiment": "EXP-PHASE5-STEP2-001",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "status": "technical_pass_mock_only" if successes == len(rows) and args.mode == "mock" else
                  "local_prediction_api_checked" if successes == len(rows) else "upstream_failed_or_contract_blocked",
        "cases": rows,
        "successes": successes,
        "total": len(rows),
        "model_retrained": False,
        "model_loaded_by_this_program": False,
        "chroma_or_neo4j_accessed": False,
        "db_writes": False,
        "medical_knowledge_gate": "BLOCKED_RESEARCH_ONLY",
        "llm_called": False,
        "network": "none" if args.mode == "mock" else "localhost_API_only",
        "caution": "Synthetic inputs and research-only HbA1c indicator, not a diagnosis or future diabetes risk. Mock scores are fabricated for contract tests, not predictions.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("===== GIAI ĐOẠN 5 — BƯỚC 2: DATA ANALYSIS + PREDICTION =====")
    print(f"Mode: {args.mode}")
    print(f"Cases: {successes}/{len(rows)}")
    for row in rows:
        print(f"{row['case_id']}: {row['status']} | hash_match={row['model_sha256_match']} | gate={row['gate']} | errors={','.join(row['error_codes']) or 'none'}")
    print("LLM: NO | ChromaDB/Neo4j: NO | DB writes: NO | ML training: NO")
    print("Status:", report["status"])
    print("Saved:", args.output)
    print("===== SEND OUTPUT AND JSON REPORT =====")
    return 0 if successes == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())

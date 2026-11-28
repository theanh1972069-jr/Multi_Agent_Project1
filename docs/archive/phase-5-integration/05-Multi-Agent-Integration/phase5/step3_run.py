"""CLI for Phase 5 Step 3: dry/mock then explicit live read-only knowledge retrieval."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import getpass
import json
import os
from pathlib import Path

from .step1_environment_audit import CONFIG_LOCAL, _safe_config
from .step3_knowledge_integration import (
    EXPECTED_COUNTS, QUESTIONS, KnowledgeIntegrationFailure,
    LiveKnowledgeBackend, MockKnowledgeBackend, execute_knowledge_query,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "outputs" / "phase5_step3" / "step3_knowledge_integration_report.json"


def main() -> int:
    p = argparse.ArgumentParser(description="Read-only research Knowledge Agent trial")
    p.add_argument("--mode", choices=("mock", "live"), default="mock")
    p.add_argument("--config", type=Path, default=CONFIG_LOCAL)
    p.add_argument("--output", type=Path, default=OUTPUT)
    args = p.parse_args()
    backend = None
    try:
        if args.mode == "mock":
            backend = MockKnowledgeBackend()
        else:
            try:
                config = _safe_config(json.loads(args.config.read_text(encoding="utf-8")))
                raw_dir = config.get("chroma_persist_dir")
                uri = config.get("neo4j_uri")
                database = config.get("neo4j_database")
                if not raw_dir or not uri or not database:
                    raise ValueError("missing mandatory settings")
                chroma_dir = Path(raw_dir).expanduser()
                if not chroma_dir.is_absolute():
                    chroma_dir = ROOT / chroma_dir
            except (ValueError, TypeError, OSError, json.JSONDecodeError):
                print("STOP: CONFIG_NOT_READY – check phase5_step1_config.json")
                return 2
            username = os.environ.get("NEO4J_USERNAME", "neo4j")
            password = os.environ.get("NEO4J_PASSWORD") or getpass.getpass("Neo4j password (hidden): ")
            if not password:
                print("STOP: MISSING_NEO4J_PASSWORD")
                return 2
            backend = LiveKnowledgeBackend(
                chroma_dir=chroma_dir, uri=uri, username=username,
                password=password, database=database,
            )
        audit = backend.audit()
        if audit != EXPECTED_COUNTS:
            raise KnowledgeIntegrationFailure("GRAPH_STATE_MISMATCH")
        # Backend check before any evidence is presented; count check is not clinical review.
        outputs = [execute_knowledge_query(backend, qid) for qid in QUESTIONS]
        joined_hits = sum(len(x["hits"]) for x in outputs)
        matched = sum(int(hit["provenance_match"]) for x in outputs for hit in x["hits"])
        errs = sum(bool(x["error_codes"]) for x in outputs)
        status = (
            "technical_pass_mock_only" if args.mode == "mock" and errs == 0 and joined_hits == 9 and matched == 9
            else "local_chroma_neo4j_checked" if args.mode == "live" and errs == 0 and joined_hits == 9 and matched == 9
            else "technical_check_failed_blocked"
        )
        report = {
            "experiment": "EXP-PHASE5-STEP3-001",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "mode": args.mode, "status": status,
            "neo4j_audit": audit, "queries": outputs,
            "joined_hits": joined_hits, "provenance_matches": matched,
            "medical_knowledge_gate": "BLOCKED_RESEARCH_ONLY",
            "answers_generated": 0, "llm_called": False,
            "application_db_write_operations": False, "ml_training": False,
            "network": "none" if args.mode == "mock" else "neo4j_aura_plus_local_model_cache",
            "limitations": [
                "No clinical validation or independent rights approval.",
                "Fixed query smoke test; not an authorization boundary or a production ACL.",
                "Read-only APIs used; prefer a read-only Neo4j account for enforcement.",
            ],
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("===== GIAI ĐOẠN 5 — BƯỚC 3: KNOWLEDGE AGENT =====")
        print("Mode:", args.mode)
        print(f"Neo4j: {audit['sources']} sources | {audit['chunks']} ChunkRef | {audit['approved_claims']} approved claims")
        print(f"Joined hits: {joined_hits} | provenance matches: {matched}")
        for q in outputs:
            print(f"{q['query_id']}: {q['status']} | hits={len(q['hits'])} | errors={','.join(q['error_codes']) or 'none'}")
        print("Answer gate: BLOCKED_RESEARCH_ONLY | LLM: NO | App DB writes: NO | ML training: NO")
        print("Status:", status)
        print("Saved:", args.output)
        print("===== SEND THIS OUTPUT AND JSON REPORT =====")
        return 0 if status != "technical_check_failed_blocked" else 1
    except KnowledgeIntegrationFailure as exc:
        print("STOP:", exc.code, "(no medical answers generated)")
        return 2
    except ImportError:
        print("STOP: MISSING_LANGGRAPH – install requirements-step3.txt")
        return 2
    finally:
        if backend is not None:
            backend.close()


if __name__ == "__main__":
    raise SystemExit(main())

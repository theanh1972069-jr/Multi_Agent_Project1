"""Bước 6: đối chiếu bằng chứng thực nghiệm Giai đoạn 4 (chỉ đọc JSON).

Không kết nối mạng, không gọi LLM, không đọc/ghi Neo4j hay ChromaDB.
Chỉ tạo báo cáo và file review CSV nếu chưa có.
"""
from __future__ import annotations
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

EXPECTED = {
    "S01": ("EVIDENCE_READY", "SYN-ATLAS-001"),
    "S02": ("EVIDENCE_READY", "SYN-ATLAS-002"),
    "S03": ("EVIDENCE_READY", "SYN-ATLAS-003"),
    "S04": ("ABSTAIN_NO_EVIDENCE", None),
    "S05": ("ABSTAIN_UNSAFE_REQUEST", None),
    "S06": ("ABSTAIN_MEDICAL_REQUEST", None),
}
COLUMNS = [
    "case_id", "evidence_chunk_id", "answer_fully_supported_yes_no",
    "citation_correct_yes_no", "unsupported_claim_found_yes_no",
    "reviewer", "reviewed_at_utc", "notes"
]

def load_json(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f"Không thấy báo cáo: {path}")
    return json.loads(path.read_text(encoding="utf-8"))

def create_review_if_needed(path: Path):
    if path.is_file():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for c in ("S01", "S02", "S03"):
            writer.writerow({"case_id": c, "evidence_chunk_id": EXPECTED[c][1]})
    return True

def review_result(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    by_id = {r.get("case_id"): r for r in rows}
    if len(by_id) != len(rows):
        return {"status": "invalid_duplicate_case_id", "completed": 0}
    completed = 0
    failed = []
    for cid in ("S01", "S02", "S03"):
        r = by_id.get(cid)
        if not r:
            failed.append(cid + ": missing"); continue
        fields = [r.get("answer_fully_supported_yes_no", "").strip().lower(),
                  r.get("citation_correct_yes_no", "").strip().lower(),
                  r.get("unsupported_claim_found_yes_no", "").strip().lower()]
        if not all(x in ("yes", "no") for x in fields) or not r.get("reviewer", "").strip() or not r.get("reviewed_at_utc", "").strip():
            continue
        completed += 1
        if fields != ["yes", "yes", "no"]:
            failed.append(cid + ": review needs correction")
        if r.get("evidence_chunk_id", "").strip() != EXPECTED[cid][1]:
            failed.append(cid + ": wrong evidence ID")
    status = "pending_manual_review" if completed < 3 else ("manual_review_found_issues" if failed else "manual_review_pass")
    return {"status": status, "completed": completed, "total": 3, "issues": failed}

def main():
    ap = argparse.ArgumentParser(description="Đối chiếu ba báo cáo Giai đoạn 4 và phiếu review")
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--step5m", default=None)
    ap.add_argument("--step5l", default=None)
    ap.add_argument("--step5e", default=None)
    ap.add_argument("--manual-review", default=None)
    args = ap.parse_args()
    root = Path(args.project_root).resolve()
    path5m = Path(args.step5m) if args.step5m else root/'data/outputs/rag_sandbox_step5m/step5m_rag_sandbox_report.json'
    path5l = Path(args.step5l) if args.step5l else root/'data/outputs/safe_retrieval_step5l/step5l_safe_retrieval_report.json'
    path5e = Path(args.step5e) if args.step5e else root/'data/outputs/graph_retrieval_step5e/step5e_graph_retrieval_report.json'
    review_path = Path(args.manual_review) if args.manual_review else root/'registry/06_manual_answer_review.csv'
    r5m, r5l, r5e = load_json(path5m), load_json(path5l), load_json(path5e)
    checks = {}
    def check(name, condition):
        checks[name] = bool(condition)
    check("5E_chroma_66", r5e.get("chroma_records") == 66)
    counts = r5e.get("neo4j_counts", {})
    check("5E_neo4j_metadata", counts.get("chunk_refs") == 66 and counts.get("chunk_links") == 66 and counts.get("source_documents") == 7 and counts.get("orphans") == 0)
    check("5E_provenance_9_9", r5e.get("joined_hits") == 9 and r5e.get("provenance_matches") == 9)
    check("5L_index_unchanged_66", r5l.get("neo4j_audit", {}).get("chunks") == 66 and r5l.get("neo4j_audit", {}).get("orphans") == 0)
    check("5L_all_results_blocked", all(q.get("answer_gate") == "BLOCKED_RESEARCH_ONLY" for q in r5l.get("queries", [])) and len(r5l.get("queries", [])) == 3 and all(h.get("allowed_to_answer") is False for q in r5l.get("queries", []) for h in q.get("hits", [])))
    check("5L_technical_provenance", r5l.get("joined_hits") == 9 and r5l.get("provenance_matches") == 9)
    check("5L_no_llm_or_writes", r5l.get("llm_called") is False and r5l.get("chroma_modified") is False and r5l.get("neo4j_modified") is False)
    check("5M_synthetic_separation", r5m.get("dataset_id") == "SYN-ATLAS-RAG-05M-v1" and r5m.get("clinical_kb_accessed") is False and r5m.get("neo4j_or_chroma_modified") is False)
    check("5M_preflight_6_6", r5m.get("preflight_passed") == 6 and r5m.get("preflight_total") == 6)
    cases = r5m.get("cases", [])
    by_case = {x.get("case_id"): x for x in cases}
    check("5M_six_cases_present", len(cases) == 6 and set(by_case) == set(EXPECTED))
    for cid, (expected_gate, evidence_id) in EXPECTED.items():
        entry = by_case.get(cid, {})
        status_match = entry.get("gate_status") == expected_gate and entry.get("preflight_pass") is True
        if evidence_id is not None:
            ok = status_match and entry.get("llm_status") == "LLM_OUTPUT_NEEDS_HUMAN_REVIEW" and bool(entry.get("llm_answer")) and evidence_id in entry.get("retrieved_ids", []) and evidence_id in entry.get("llm_citations", []) and set(entry.get("llm_citations", [])).issubset(set(entry.get("retrieved_ids", [])))
        else:
            ok = status_match and entry.get("llm_status") == "NOT_CALLED" and entry.get("llm_answer") is None and not entry.get("llm_citations")
        check("5M_" + cid, ok)
    check("5M_knowledge_gate_blocked", r5m.get("medical_knowledge_gate") == "BLOCKED_RESEARCH_ONLY")

    created_review = create_review_if_needed(review_path)
    manual = review_result(review_path)
    technical_pass = all(checks.values())
    if not technical_pass:
        status = "technical_checks_failed"
    elif manual["status"] == "manual_review_pass":
        status = "research_sandbox_phase4_ready_to_close_with_limitations"
    else:
        status = "technical_pass_manual_review_pending"

    out = {
        "experiment": "EXP-PHASE4-E2E-STEP6-001",
        "stage": "phase4_step6_research_evaluation",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "checks": checks,
        "technical_checks_passed": sum(checks.values()),
        "technical_checks_total": len(checks),
        "technical_pass": technical_pass,
        "manual_answer_review": manual,
        "manual_review_csv": str(review_path),
        "input_reports": [str(path5e), str(path5l), str(path5m)],
        "no_live_model_or_database_calls": True,
        "medical_knowledge_gate": "BLOCKED_RESEARCH_ONLY",
        "clinical_validation": False,
        "independent_rights_verification": False,
        "phase4_completion_scope": "research_sandbox_only",
        "important_limits": [
            "S01-S03 must be checked against the original synthetic text, not merely a valid citation ID",
            "Prompt injection safety and medical claims are not production-validated",
            "No licensed or clinical clearance of the 7 real documents is implied",
            "This script verifies stored reports; it is not a live end-to-end penetration or medical test"
        ]
    }
    report_path = root/'data/outputs/phase4_e2e_step6/step6_phase4_e2e_report.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("===== GIAI ĐOẠN 4 — BƯỚC 6: REPORT CONSISTENCY & MANUAL REVIEW =====")
    print(f"Technical checks: {sum(checks.values())}/{len(checks)}")
    print("S01–S03 manual review:", manual["status"], f"({manual.get('completed', 0)}/3)")
    print("Medical answering: BLOCKED_RESEARCH_ONLY")
    print("LLM called: NO | DB writes: NO | ML training: NO")
    print("Review template created:", created_review)
    print("Status:", status)
    print("Saved:", report_path)
    return 0 if technical_pass else 1

if __name__ == "__main__":
    raise SystemExit(main())

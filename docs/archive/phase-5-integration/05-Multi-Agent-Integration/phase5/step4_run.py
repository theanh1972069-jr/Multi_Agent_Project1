"""Run Step 4 with FIXED synthetic Atlas cases (mock default; Ollama opt-in)."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from .step4_consultation import CASES, ConsultationError, ROOT, execute_consultation, load_synthetic_documents

REPORT = ROOT / 'data' / 'outputs' / 'phase5_step4' / 'step4_consultation_report.json'


def main() -> int:
    parser = argparse.ArgumentParser(description='Phase 5 Step 4: Consultation Agent synthetic sandbox')
    parser.add_argument('--mode', choices=('mock', 'ollama'), default='mock')
    parser.add_argument('--model', default='qwen2.5:1.5b')
    parser.add_argument('--output', type=Path, default=REPORT)
    args = parser.parse_args()
    try:
        docs = load_synthetic_documents()
        results = [execute_consultation(case_id, mode=args.mode, documents=docs, model=args.model) for case_id in CASES]
    except ConsultationError as exc:
        print('STOP:', exc.code, '| no medical answers generated')
        return 2
    passes = sum(r['gate_status'] == CASES[r['case_id']]['expected_gate'] and
                 (r['retrieved_ids'] == ([CASES[r['case_id']]['chunk_id']] if CASES[r['case_id']]['chunk_id'] else [])) for r in results)
    blocked = sum(r['gate_status'].startswith('ABSTAIN_') and not r['llm_called'] for r in results)
    llm_attempts = sum(r['llm_called'] for r in results)
    errors = sum(bool(r['error_codes']) for r in results)
    expected_attempts = 3 if args.mode == 'ollama' else 0
    status = ('technical_pass_mock_only' if args.mode == 'mock' and passes == 6 and blocked == 3 and errors == 0
              else 'local_ollama_outputs_need_manual_review' if args.mode == 'ollama' and passes == 6 and blocked == 3 and llm_attempts == 3 and errors == 0
              else 'sandbox_incomplete_or_llm_error')
    report = {
        'experiment': 'EXP-PHASE5-STEP4-001', 'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'mode': args.mode, 'model': args.model if args.mode == 'ollama' else None,
        'status': status, 'dataset_id': 'SYN-ATLAS-RAG-05M-v1',
        'preflight_passed': passes, 'preflight_total': 6,
        'blocked_before_llm': blocked, 'llm_attempts': llm_attempts,
        'llm_expected_attempts': expected_attempts,
        'clinical_kb_accessed': False, 'prediction_api_accessed': False,
        'medical_knowledge_gate': 'BLOCKED_RESEARCH_ONLY',
        'chroma_or_neo4j_modified': False, 'ml_training': False,
        'manual_review_complete': False, 'cases': results,
        'notes': ['Fixed six-case smoke test, not general prompt-injection protection.',
                  'Citation validity is checked structurally; factual grounding must be reviewed manually.',
                  'No clinical or rights validation and no production authorization boundary.'],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('===== GIAI ĐOẠN 5 — BƯỚC 4: CONSULTATION AGENT SANDBOX =====')
    print('Mode:', args.mode, '| Dataset:', report['dataset_id'])
    print(f"Preflight: {passes}/6 | blocked before LLM: {blocked}/3 | LLM attempts: {llm_attempts}")
    for item in results:
        print(f"{item['case_id']}: {item['status']} | citations={','.join(item['citations']) or '-'} | errors={','.join(item['error_codes']) or 'none'}")
    print('Medical gate: BLOCKED_RESEARCH_ONLY | Clinical KB: NO | DB writes: NO | ML training: NO')
    print('Status:', status)
    print('Saved:', args.output)
    print('===== SEND THIS OUTPUT AND JSON REPORT =====')
    return 0 if status != 'sandbox_incomplete_or_llm_error' else 1


if __name__ == '__main__':
    raise SystemExit(main())

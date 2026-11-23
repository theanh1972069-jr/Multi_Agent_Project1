"""Fixed synthetic smoke tests over one five-agent LangGraph.

Mock default. 'live' opt-in, requiring existing local FastAPI + Chroma + Neo4j.
Ollama is optional and may ONLY be called on S01-S03 synthetic Atlas cases.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from .contracts import EXPECTED_SHA256
from .step5_orchestrator import (Step5Request, invoke_step5, MEDICAL_GATE,
                                 OP_ATLAS, OP_KNOW, OP_PRED)
from .step5_runtime import build_runtime

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / 'data' / 'outputs' / 'phase5_step5' / 'step5_orchestrator_report.json'

FIXTURES = [
    {'request_id': 'SYN-PRED-01', 'operation': OP_PRED,
     'features': {'RIDAGEYR': 45, 'RIAGENDR': 1, 'BMXBMI': 28.5}},
    {'request_id': 'SYN-PRED-02', 'operation': OP_PRED,
     'features': {'RIDAGEYR': 60, 'RIAGENDR': 2, 'BMXBMI': 30.0}},
    *({'request_id': f'SYN-KNOW-{qid}', 'operation': OP_KNOW, 'query_id': qid}
      for qid in ['Q01','Q02','Q03']),
    *({'request_id': f'SYN-ATLAS-{sid}', 'operation': OP_ATLAS, 'case_id': sid}
      for sid in ['S01','S02','S03','S04','S05','S06']),
]


def evaluate_response(operation: str, result: dict, *, mode: str, llm_mode: str,
                      case_id: str | None = None) -> bool:
    if result['medical_gate'] != MEDICAL_GATE:
        return False
    if operation == OP_PRED:
        p = result.get('prediction')
        return result['status'] == 'ok' and p is not None and p['model_sha256'] == EXPECTED_SHA256 and p['threshold'] == 0.225 and not result['llm_called'] and not result['evidence_metadata']
    if operation == OP_KNOW:
        evidence = result['evidence_metadata']
        return (result['status'] == 'blocked_research_only' and len(evidence) == 3 and
                all(h['provenance_match'] and not h['allowed_to_answer'] for h in evidence) and
                result['synthetic_answer'] is None and not result['llm_called'])
    if operation == OP_ATLAS:
        if case_id in {'S04','S05','S06'}:
            return result['status'] == 'abstained' and result['synthetic_answer'] is None and not result['llm_called']
        expected_status = ('llm_output_needs_human_review' if llm_mode == 'ollama'
                           else 'mock_response_not_llm')
        return (result['status'] == expected_status and bool(result['synthetic_answer'])
                and len(result['synthetic_citations']) == 1
                and result['llm_called'] == (llm_mode == 'ollama'))
    return False


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--mode', choices=['mock','live'], default='mock')
    p.add_argument('--consultation', choices=['mock','ollama'], default='mock')
    p.add_argument('--model', default='qwen2.5:1.5b')
    p.add_argument('--output', type=Path, default=DEFAULT_OUT)
    args = p.parse_args()
    backend = None
    try:
        graph, backend = build_runtime(mode=args.mode, consultation_mode=args.consultation, model=args.model)
    except Exception as exc:
        print('STOP: BACKEND_OR_GRAPH_NOT_READY (no medical answers generated)')
        return 2
    rows = []
    try:
        for input_data in FIXTURES:
            req = Step5Request.model_validate({**input_data, 'synthetic_test_only': True})
            response = invoke_step5(graph, req)
            full = response.model_dump()
            passed = evaluate_response(req.operation, full, mode=args.mode,
                     llm_mode=args.consultation, case_id=input_data.get('case_id'))
            # Store minimal metadata only, no private input, raw clinical evidence or answers.
            rows.append({
                'request_id': req.request_id, 'operation': req.operation,
                'status': full['status'], 'passed': passed, 'error_codes': full['error_codes'],
                'prediction_sha256_match': full['prediction']['model_sha256'] == EXPECTED_SHA256 if full['prediction'] else None,
                'evidence_count': len(full['evidence_metadata']),
                'provenance_matches': sum(int(x['provenance_match']) for x in full['evidence_metadata']),
                'synthetic_citations': full['synthetic_citations'],
                'llm_called': full['llm_called'], 'medical_gate': full['medical_gate'],
            })
    finally:
        backend.close()
    passed = sum(x['passed'] for x in rows)
    report = {
        'experiment': 'EXP-PHASE5-STEP5-001', 'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'mode': args.mode, 'consultation_mode': args.consultation,
        'model': args.model if args.consultation == 'ollama' else None,
        'status': ('orchestrator_live_technical_pass_manual_review_pending' if passed == len(rows) and args.mode == 'live' and args.consultation == 'ollama'
                   else 'orchestrator_live_technical_pass' if passed == len(rows) and args.mode == 'live'
                   else 'orchestrator_mock_technical_pass' if passed == len(rows) else 'orchestrator_incomplete'),
        'passed': passed, 'total': len(rows), 'cases': rows,
        'medical_knowledge_gate': MEDICAL_GATE, 'clinical_answers_generated': False,
        'db_writes': False, 'model_retrained': False,
        'limitation': 'Only fixed synthetic fixtures; Ollama answers need manual review; not a production authorization boundary.',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('===== GIAI ĐOẠN 5 — BƯỚC 5: ORCHESTRATOR LANGGRAPH =====')
    print(f'Mode: {args.mode} | Consultation: {args.consultation}')
    print(f'Cases: {passed}/{len(rows)}')
    for row in rows:
        print(f"{row['request_id']}: {row['status']} | passed={row['passed']} | errors={','.join(row['error_codes']) or 'none'}")
    print('Medical gate:', MEDICAL_GATE, '| Medical LLM: NO | DB writes: NO | ML training: NO')
    print('Status:', report['status'])
    print('Saved:', args.output)
    return 0 if passed == len(rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())

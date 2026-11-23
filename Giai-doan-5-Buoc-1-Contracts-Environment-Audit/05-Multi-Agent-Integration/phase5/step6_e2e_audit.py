"""Phase 5 Step 6: offline, research-only cross-report consistency audit.

Reads local Step 2-5 JSON reports, optional HTTP smoke JSON and human review CSV.
No database/API connections, LLM calls, model loading, or ML retraining.
Stored reports are evidence of earlier tests; this is NOT a live pen-test or clinical audit.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path

GATE = 'BLOCKED_RESEARCH_ONLY'
PRED_IDS = ('SYN-PRED-01', 'SYN-PRED-02')
KNOW_IDS = ('SYN-KNOW-Q01', 'SYN-KNOW-Q02', 'SYN-KNOW-Q03')
ATLAS_IDS = tuple(f'SYN-ATLAS-S{i:02d}' for i in range(1, 7))
ATLAS_SOURCE = {f'S0{i}': f'SYN-ATLAS-00{i}' for i in range(1, 4)}


def load_json(path: Path):
    if not path.is_file():
        return None, 'missing_file'
    try:
        result = json.loads(path.read_text(encoding='utf-8-sig'))
        if not isinstance(result, dict):
            return None, 'invalid_json_root'
        return result, None
    except (OSError, ValueError):
        return None, 'invalid_json'


def unique_map(rows, field):
    if not isinstance(rows, list):
        return None
    result = {}
    for x in rows:
        if not isinstance(x, dict) or not isinstance(x.get(field), str) or x[field] in result:
            return None
        result[x[field]] = x
    return result


def validate_step2(d):
    if not d:
        return False
    rows = unique_map(d.get('cases'), 'case_id')
    return all([
        d.get('mode') == 'live', d.get('status') == 'local_prediction_api_checked',
        d.get('successes') == 2, d.get('total') == 2,
        d.get('medical_knowledge_gate') == GATE,
        d.get('model_retrained') is False, d.get('chroma_or_neo4j_accessed') is False,
        d.get('db_writes') is False, d.get('llm_called') is False,
        rows is not None, set(rows or {}) == set(PRED_IDS),
        all(rows.get(k, {}).get('status') == 'ok' and
            rows.get(k, {}).get('prediction_present') is True and
            rows.get(k, {}).get('model_sha256_match') is True and
            rows.get(k, {}).get('threshold_match') is True and
            rows.get(k, {}).get('gate') == GATE and
            rows.get(k, {}).get('llm_called') is False and
            rows.get(k, {}).get('research_only') is True and
            rows.get(k, {}).get('error_codes') == [] for k in PRED_IDS) if rows else False,
    ])


def validate_step3(d):
    if not d:
        return False
    a = d.get('neo4j_audit', {})
    rows = unique_map(d.get('queries'), 'query_id')
    return all([
        d.get('mode') == 'live', d.get('status') == 'local_chroma_neo4j_checked',
        d.get('joined_hits') == 9, d.get('provenance_matches') == 9,
        d.get('medical_knowledge_gate') == GATE,
        d.get('answers_generated') == 0, d.get('llm_called') is False,
        d.get('application_db_write_operations') is False, d.get('ml_training') is False,
        a.get('sources') == 7, a.get('chunks') == 66, a.get('chunk_links') == 66,
        a.get('orphans') == 0, a.get('approved_claims') == 0, a.get('approved_relations') == 0,
        rows is not None, set(rows or {}) == {'Q01','Q02','Q03'},
        all(rows[q].get('status') == 'blocked_research_only' and
            rows[q].get('knowledge_gate') == GATE and
            rows[q].get('llm_called') is False and
            rows[q].get('answer_generated') is False and
            rows[q].get('error_codes') == [] and
            isinstance(rows[q].get('hits'), list) and len(rows[q]['hits']) == 3 and
            all(isinstance(hit, dict) and hit.get('provenance_match') is True and
                hit.get('allowed_to_answer') is False and
                isinstance(hit.get('chunk_id'), str) and isinstance(hit.get('source_id'), str)
                for hit in rows[q]['hits']) for q in ('Q01','Q02','Q03')) if rows else False,
    ])


def validate_step4(d):
    if not d:
        return False
    rows = unique_map(d.get('cases'), 'case_id')
    return all([
        d.get('mode') == 'ollama', d.get('dataset_id') == 'SYN-ATLAS-RAG-05M-v1',
        d.get('preflight_passed') == 6, d.get('preflight_total') == 6,
        d.get('blocked_before_llm') == 3, d.get('llm_attempts') == 3,
        d.get('clinical_kb_accessed') is False, d.get('prediction_api_accessed') is False,
        d.get('medical_knowledge_gate') == GATE, d.get('chroma_or_neo4j_modified') is False,
        d.get('ml_training') is False,
        rows is not None, set(rows or {}) == {f'S0{i}' for i in range(1, 7)},
        all(rows[k].get('llm_called') is True and
            rows[k].get('gate_status') == 'EVIDENCE_READY' and
            rows[k].get('status') == 'LLM_OUTPUT_NEEDS_HUMAN_REVIEW' and
            rows[k].get('medical_knowledge_gate') == GATE and
            rows[k].get('retrieved_ids') == [source] and
            rows[k].get('citations') == [source] and
            isinstance(rows[k].get('answer'), str) and bool(rows[k]['answer'].strip()) and
            rows[k].get('error_codes') == []
            for k, source in ATLAS_SOURCE.items()) if rows else False,
        all(rows[k].get('status') == status and rows[k].get('gate_status') == status and
            rows[k].get('medical_knowledge_gate') == GATE and
            rows[k].get('llm_called') is False and rows[k].get('answer') is None and
            rows[k].get('citations') == [] and rows[k].get('error_codes') == []
            for k, status in (('S04','ABSTAIN_NO_EVIDENCE'),
                              ('S05','ABSTAIN_UNSAFE_REQUEST'),
                              ('S06','ABSTAIN_MEDICAL_REQUEST'))) if rows else False,
    ])


def validate_step5(d, *, consultation='mock'):
    if not d:
        return False
    rows = unique_map(d.get('cases'), 'request_id')
    status = ('orchestrator_live_technical_pass' if consultation == 'mock'
              else 'orchestrator_live_technical_pass_manual_review_pending')
    if not (d.get('mode') == 'live' and d.get('consultation_mode') == consultation and
            d.get('status') == status and d.get('passed') == 11 and d.get('total') == 11 and
            d.get('medical_knowledge_gate') == GATE and
            d.get('clinical_answers_generated') is False and d.get('db_writes') is False and
            d.get('model_retrained') is False and rows is not None and
            set(rows) == set(PRED_IDS + KNOW_IDS + ATLAS_IDS)):
        return False
    for k in PRED_IDS:
        r = rows[k]
        if not all((r.get('operation') == 'research_prediction', r.get('status') == 'ok',
                    r.get('passed') is True, r.get('error_codes') == [],
                    r.get('prediction_sha256_match') is True,
                    r.get('evidence_count') == 0, r.get('llm_called') is False,
                    r.get('medical_gate') == GATE)):
            return False
    for k in KNOW_IDS:
        r = rows[k]
        if not all((r.get('operation') == 'knowledge_research_lookup',
                    r.get('status') == 'blocked_research_only', r.get('passed') is True,
                    r.get('error_codes') == [], r.get('evidence_count') == 3,
                    r.get('provenance_matches') == 3, r.get('llm_called') is False,
                    r.get('medical_gate') == GATE)):
            return False
    for i, k in enumerate(ATLAS_IDS, start=1):
        r = rows[k]
        if not all((r.get('operation') == 'synthetic_rag_demo', r.get('passed') is True,
                    r.get('error_codes') == [], r.get('medical_gate') == GATE)):
            return False
        if i <= 3:
            if not (r.get('status') == ('mock_response_not_llm' if consultation == 'mock' else 'llm_output_needs_human_review') and
                    r.get('synthetic_citations') == [f'SYN-ATLAS-00{i}'] and
                    r.get('llm_called') is (consultation == 'ollama')):
                return False
        else:
            if not (r.get('status') == 'abstained' and r.get('synthetic_citations') == [] and
                    r.get('llm_called') is False):
                return False
    return True


def validate_http(d):
    if not d:
        return False
    return (d.get('mode') == 'mock' and d.get('passed') == 8 and d.get('total') == 8 and
            d.get('status') == 'api_mock_smoke_pass' and
            d.get('medical_knowledge_gate') == GATE and
            d.get('all_requests_localhost') is True and
            d.get('clinical_answers_generated') is False and
            isinstance(d.get('checks'), dict) and len(d['checks']) == 8 and
            all(v is True for v in d['checks'].values()))


def validate_manual_csv(path, step4):
    if not path.exists():
        return 'pending', 0, ['manual_review_csv_missing']
    if not step4:
        return 'pending', 0, ['step4_report_missing']
    source_rows = unique_map(step4.get('cases'), 'case_id') or {}
    try:
        with path.open('r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error):
        return 'fail', 0, ['manual_review_csv_unreadable']
    mapped = unique_map(rows, 'case_id')
    if mapped is None or set(mapped) != set(ATLAS_SOURCE):
        return 'fail', 0, ['manual_review_requires_exactly_S01_S02_S03']
    completed = 0
    issues = []
    for case_id, source_id in ATLAS_SOURCE.items():
        row = mapped[case_id]
        upstream = source_rows.get(case_id, {})
        if row.get('citation_id') != source_id or row.get('llm_answer') != upstream.get('answer'):
            issues.append(f'{case_id}:citation_or_answer_does_not_match_source_report')
            continue
        answers = [row.get(f, '').strip().lower() for f in
                   ('answer_fully_supported_yes_no','citation_correct_yes_no','unsupported_claim_found_yes_no')]
        author = row.get('reviewer', '').strip()
        date = row.get('reviewed_at_utc', '').strip()
        if not any(answers) and not author and not date:
            continue
        if answers != ['yes', 'yes', 'no']:
            issues.append(f'{case_id}:human_review_not_passed_or_incomplete')
            continue
        try:
            if not author or not date:
                raise ValueError('missing identity or time')
            parsed = datetime.fromisoformat(date.replace('Z','+00:00'))
            if parsed.tzinfo is None:
                raise ValueError('timezone required')
        except ValueError:
            issues.append(f'{case_id}:reviewer_or_utc_time_invalid')
            continue
        completed += 1
    if issues:
        return 'fail', completed, issues
    return ('pass' if completed == 3 else 'pending'), completed, []


def main():
    parser = argparse.ArgumentParser(description='Offline Phase 5 Step 6 E2E audit')
    root_default = Path(__file__).resolve().parents[1]
    parser.add_argument('--project-root', type=Path, default=root_default)
    parser.add_argument('--step5-ollama-report', type=Path, default=None,
                        help='Optional separate Step 5 live Ollama metadata report')
    args = parser.parse_args()
    root = args.project_root.expanduser().resolve()
    locations = {
        'step2': root/'data/outputs/phase5_step2/step2_prediction_integration_report.json',
        'step3': root/'data/outputs/phase5_step3/step3_knowledge_integration_report.json',
        'step4': root/'data/outputs/phase5_step4/step4_consultation_report.json',
        'step5': root/'data/outputs/phase5_step5/step5_orchestrator_report.json',
        'http': root/'data/outputs/phase5_step6/step6_http_smoke_report.json',
    }
    reports = {k: load_json(v)[0] for k,v in locations.items()}
    checks = {
        'step2_live_prediction': validate_step2(reports['step2']),
        'step3_live_knowledge': validate_step3(reports['step3']),
        'step4_ollama_synthetic': validate_step4(reports['step4']),
        'step5_live_mock_consultation': validate_step5(reports['step5']),
        'step6_http_mock': validate_http(reports['http']),
    }
    core_passed = all(checks[k] for k in list(checks)[:4])
    review_file = root/'registry/step6_consultation_manual_review.csv'
    manual_status, manual_completed, manual_issues = validate_manual_csv(review_file, reports['step4'])
    ollama_status = 'not_supplied'
    if args.step5_ollama_report:
        ol, _ = load_json(args.step5_ollama_report)
        ollama_status = 'technical_pass_content_review_required' if validate_step5(ol, consultation='ollama') else 'invalid_or_missing'
    if not core_passed:
        status = 'report_checks_failed_or_missing'
    elif not checks['step6_http_mock']:
        status = 'technical_pass_http_pending'
    elif manual_status == 'pending':
        status = 'technical_pass_manual_review_pending'
    elif manual_status == 'fail':
        status = 'manual_review_requires_attention'
    else:
        status = 'phase5_research_sandbox_ready_to_close_with_limitations'
    result = {
        'experiment': 'EXP-PHASE5-STEP6-001',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'stage': 'phase5_step6_offline_consistency_and_local_http_smoke',
        'status': status,
        'report_checks': checks,
        'reports_verified': sum(checks.values()), 'reports_total': len(checks),
        'manual_review': {'status': manual_status,'completed':manual_completed,'total':3,
                          'issues':manual_issues},
        'step5_live_ollama_optional': ollama_status,
        'medical_knowledge_gate': GATE,
        'llm_called_by_this_audit': False,
        'network_called_by_this_audit': False,
        'application_db_writes': False,
        'ml_training': False,
        'scope': 'research_sandbox_only',
        'limitations': [
            'This script validates stored reports and optional local API smoke evidence, not live database contents.',
            'Step 5 live + Consultation mock is not proof of Ollama executing inside Orchestrator.',
            'No medical validation, rights clearance, production authorization or generalized injection protection.',
            'Step 4 Atlas text needs independent/manual groundedness confirmation.',
        ],
    }
    out = root/'data/outputs/phase5_step6/step6_phase5_e2e_report.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('===== GIAI ĐOẠN 5 — BƯỚC 6: E2E CONSISTENCY =====')
    for name, value in checks.items():
        print(f'{name}: {"PASS" if value else "PENDING_OR_FAIL"}')
        if not value:
            print(f'  Check corresponding JSON in: {root / "data/outputs"}')
    print(f'Manual Atlas review: {manual_status} ({manual_completed}/3)')
    if manual_issues: print('Manual review issues:', ', '.join(manual_issues))
    print('Optional Step 5 Ollama:', ollama_status)
    print('Medical gate:', GATE, '| LLM: NO | Network: NO | DB writes: NO')
    print('Status:', status)
    print('Saved:', out)
    return 0 if status == 'phase5_research_sandbox_ready_to_close_with_limitations' else 1


if __name__ == '__main__':
    raise SystemExit(main())

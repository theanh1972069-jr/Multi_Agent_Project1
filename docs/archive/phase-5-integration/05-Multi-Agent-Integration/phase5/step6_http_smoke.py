"""Phase 5 Step 6: strictly loopback-only HTTP smoke tests against mock FastAPI :8001.

Start: python -m phase5.step5_api --mode mock --port 8001
Then: python -m phase5.step6_http_smoke
No real clinical inputs, no database access, no LLM call expected.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, ProxyHandler, HTTPRedirectHandler, build_opener

GATE='BLOCKED_RESEARCH_ONLY'
ROOT=Path(__file__).resolve().parents[1]


def fetch(base: str, path: str, data=None):
    encoded=(json.dumps(data).encode('utf-8') if data is not None else None)
    req=Request(base+path, data=encoded, method='POST' if data is not None else 'GET',
                headers={'Content-Type':'application/json'} if data is not None else {})
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(req,timeout=8) as r:
            data = r.read(65537)
            if len(data) > 65536: return None, None
            return r.status, json.loads(data.decode('utf-8'))
    except HTTPError as exc:
        # Return HTTP status only. Never expose raw error bodies or inputs to report.
        return exc.code, None
    except (URLError, TimeoutError, ValueError, OSError):
        return None, None


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8001')
    parser.add_argument('--output',type=Path, default=ROOT/'data/outputs/phase5_step6/step6_http_smoke_report.json')
    args=parser.parse_args()
    try:
        parts=urlsplit(args.base_url)
        explicit_port=parts.port
    except ValueError:
        print('STOP: INVALID_LOOPBACK_URL')
        return 2
    # Explicitly refuse proxy/external hosts. No production endpoint use.
    if parts.scheme!='http' or parts.hostname not in {'127.0.0.1','localhost'} or parts.username or parts.password or parts.path not in {'','/'} or parts.query or parts.fragment or explicit_port is None:
        print('STOP: ONLY_HTTP_LOOPBACK_WITH_EXPLICIT_PORT_IS_ALLOWED')
        return 2
    base=args.base_url.rstrip('/')
    checks={}
    status, doc=fetch(base,'/health/live')
    checks['health_live_mock']=(status==200 and isinstance(doc,dict) and doc.get('status')=='alive' and doc.get('mode')=='mock')
    status, doc=fetch(base,'/health/ready')
    checks['health_ready_not_backend_probe']=(status==200 and isinstance(doc,dict) and
        doc.get('status')=='graph_compiled_backends_not_probed' and doc.get('mode')=='mock' and doc.get('medical_gate')==GATE)
    endpoint='/api/v1/research/agents/run'
    p={'request_id':'STEP6-PRED','operation':'research_prediction','synthetic_test_only':True,
       'features':{'RIDAGEYR':45,'RIAGENDR':1,'BMXBMI':28.5}}
    status, doc=fetch(base,endpoint,p)
    checks['prediction_mock_200']=(status==200 and isinstance(doc,dict) and doc.get('status')=='ok' and
        doc.get('medical_gate')==GATE and not doc.get('llm_called') and
        isinstance(doc.get('prediction'),dict) and doc['prediction'].get('threshold')==0.225 and
        doc.get('evidence_metadata')==[])
    k={'request_id':'STEP6-KNOW','operation':'knowledge_research_lookup','synthetic_test_only':True,'query_id':'Q01'}
    status,doc=fetch(base,endpoint,k)
    hits=doc.get('evidence_metadata') if isinstance(doc,dict) else None
    checks['knowledge_blocked_200']=(status==200 and isinstance(doc,dict) and
        doc.get('status')=='blocked_research_only' and doc.get('medical_gate')==GATE and
        doc.get('llm_called') is False and isinstance(hits,list) and len(hits)==3 and
        all(isinstance(h,dict) and h.get('allowed_to_answer') is False for h in hits))
    a={'request_id':'STEP6-ATLAS','operation':'synthetic_rag_demo','synthetic_test_only':True,'case_id':'S01'}
    status,doc=fetch(base,endpoint,a)
    checks['atlas_mock_200']=(status==200 and isinstance(doc,dict) and
        doc.get('status')=='mock_response_not_llm' and doc.get('medical_gate')==GATE and
        doc.get('synthetic_citations')==['SYN-ATLAS-001'] and doc.get('llm_called') is False)
    abstain={'request_id':'STEP6-ABSTAIN','operation':'synthetic_rag_demo','synthetic_test_only':True,'case_id':'S06'}
    status,doc=fetch(base,endpoint,abstain)
    checks['atlas_abstain_200']=(status==200 and isinstance(doc,dict) and
        doc.get('status')=='abstained' and doc.get('medical_gate')==GATE and
        doc.get('synthetic_answer') is None and doc.get('llm_called') is False)
    status,doc=fetch(base,endpoint,{**a,'medical_gate':'SYNTHETIC_READY'})
    checks['client_gate_override_rejected_422']=status==422
    status,doc=fetch(base,endpoint,{**k,'query_id':'Q99'})
    checks['unknown_medical_query_rejected_422']=status==422
    passed=sum(v is True for v in checks.values())
    report={'experiment':'EXP-PHASE5-STEP6-HTTP-001','timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'mode':'mock','status':'api_mock_smoke_pass' if passed==8 else 'api_mock_smoke_incomplete',
        'passed':passed,'total':8,'checks':checks,'all_requests_localhost':True,
        'medical_knowledge_gate':GATE,'clinical_answers_generated':False,
        'llm_called':False,'db_writes':False,'ml_training':False,
        'note':'Local-only API mock smoke. No backend readiness, authentication, load, or security pen-test.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('===== GIAI ĐOẠN 5 — BƯỚC 6: LOCAL API MOCK SMOKE =====')
    for name,ok in checks.items(): print(f'{name}: {"PASS" if ok else "FAIL"}')
    print(f'Checks: {passed}/8 | Status: {report["status"]}')
    print('LLM: NO | Medical KB: NO | DB writes: NO | ML training: NO')
    print('Saved:',args.output)
    return 0 if passed==8 else 1


if __name__=='__main__':
    raise SystemExit(main())

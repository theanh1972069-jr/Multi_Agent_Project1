"""Offline, dependency-free contract tests for Phase 5 Step 6 report evaluator."""
from __future__ import annotations

import csv
import tempfile
from pathlib import Path
import unittest

from .step6_e2e_audit import (ATLAS_SOURCE, GATE, validate_manual_csv,
                               validate_step2, validate_step3, validate_step4,
                               validate_step5, validate_http)


def step2_sample():
    return dict(mode='live',status='local_prediction_api_checked',successes=2,total=2,
      medical_knowledge_gate=GATE,model_retrained=False,chroma_or_neo4j_accessed=False,
      db_writes=False,llm_called=False,cases=[
        dict(case_id=f'SYN-PRED-0{i}',status='ok',prediction_present=True,
          model_sha256_match=True,threshold_match=True,gate=GATE,llm_called=False,
          research_only=True,error_codes=[]) for i in (1,2)])


def step3_sample():
    return dict(mode='live',status='local_chroma_neo4j_checked',joined_hits=9,
      provenance_matches=9,medical_knowledge_gate=GATE,answers_generated=0,
      llm_called=False,application_db_write_operations=False,ml_training=False,
      neo4j_audit=dict(sources=7,chunks=66,chunk_links=66,orphans=0,approved_claims=0,
                       approved_relations=0),
      queries=[dict(query_id=f'Q0{i}',status='blocked_research_only',knowledge_gate=GATE,
                    llm_called=False,answer_generated=False,error_codes=[],
                    hits=[dict(chunk_id=f'CH-{i}-{j}',source_id='SRC',provenance_match=True,
                               allowed_to_answer=False) for j in range(3)]) for i in (1,2,3)])


def step4_sample():
    cases=[]
    for i in range(1,7):
        key=f'S0{i}'
        if i<=3:
            cases.append(dict(case_id=key, llm_called=True,gate_status='EVIDENCE_READY',
                status='LLM_OUTPUT_NEEDS_HUMAN_REVIEW',medical_knowledge_gate=GATE,
                retrieved_ids=[f'SYN-ATLAS-00{i}'],citations=[f'SYN-ATLAS-00{i}'],
                answer=f'answer {i}',error_codes=[]))
        else:
            status={4:'ABSTAIN_NO_EVIDENCE',5:'ABSTAIN_UNSAFE_REQUEST',6:'ABSTAIN_MEDICAL_REQUEST'}[i]
            cases.append(dict(case_id=key,llm_called=False,gate_status=status,status=status,
                medical_knowledge_gate=GATE,answer=None,citations=[],error_codes=[]))
    return dict(mode='ollama',dataset_id='SYN-ATLAS-RAG-05M-v1',preflight_passed=6,
                preflight_total=6,blocked_before_llm=3,llm_attempts=3,clinical_kb_accessed=False,
                prediction_api_accessed=False,medical_knowledge_gate=GATE,
                chroma_or_neo4j_modified=False,ml_training=False,cases=cases)


def step5_sample(consultation='mock'):
    cases=[]
    for i in (1,2):
        cases.append(dict(request_id=f'SYN-PRED-0{i}',operation='research_prediction',
             status='ok',passed=True,error_codes=[],prediction_sha256_match=True,
             evidence_count=0,llm_called=False,medical_gate=GATE))
    for i in (1,2,3):
        cases.append(dict(request_id=f'SYN-KNOW-Q0{i}',operation='knowledge_research_lookup',
             status='blocked_research_only',passed=True,error_codes=[],evidence_count=3,
             provenance_matches=3,llm_called=False,medical_gate=GATE))
    for i in range(1,7):
        cases.append(dict(request_id=f'SYN-ATLAS-S0{i}',operation='synthetic_rag_demo',
             status=('mock_response_not_llm' if consultation=='mock' else 'llm_output_needs_human_review') if i<=3 else 'abstained',
             passed=True,error_codes=[],medical_gate=GATE,
             synthetic_citations=[f'SYN-ATLAS-00{i}'] if i<=3 else [],
             llm_called=i<=3 and consultation=='ollama'))
    return dict(mode='live', consultation_mode=consultation,
        status=('orchestrator_live_technical_pass' if consultation=='mock' else 'orchestrator_live_technical_pass_manual_review_pending'),
        passed=11,total=11,medical_knowledge_gate=GATE,
        clinical_answers_generated=False,db_writes=False,model_retrained=False,cases=cases)


def write_manual(path, step4, mode='blank'):
    columns=['case_id','citation_id','llm_answer','answer_fully_supported_yes_no',
             'citation_correct_yes_no','unsupported_claim_found_yes_no','reviewer','reviewed_at_utc']
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=columns)
        writer.writeheader()
        for case_id, source in ATLAS_SOURCE.items():
            upstream=next(x for x in step4['cases'] if x['case_id']==case_id)
            x={'case_id':case_id,'citation_id':source,'llm_answer':upstream['answer'],
               'answer_fully_supported_yes_no':'','citation_correct_yes_no':'',
               'unsupported_claim_found_yes_no':'','reviewer':'','reviewed_at_utc':''}
            if mode!='blank':
                x.update(answer_fully_supported_yes_no='yes',citation_correct_yes_no='yes',
                   unsupported_claim_found_yes_no='no',reviewer='Reviewer',
                   reviewed_at_utc='2026-11-04T00:00:00Z')
            if mode=='wrong_citation' and case_id=='S01':x['citation_id']='SYN-ATLAS-999'
            if mode=='bad_review' and case_id=='S01':x['unsupported_claim_found_yes_no']='yes'
            writer.writerow(x)


class Validators(unittest.TestCase):
    def test_step2_valid(self): self.assertTrue(validate_step2(step2_sample()))
    def test_step2_mismatched_hash_rejected(self):
        d=step2_sample();d['cases'][0]['model_sha256_match']=False
        self.assertFalse(validate_step2(d))
    def test_step3_valid(self):self.assertTrue(validate_step3(step3_sample()))
    def test_step3_unapproved_gate_rejected(self):
        d=step3_sample();d['queries'][0]['hits'][0]['allowed_to_answer']=True
        self.assertFalse(validate_step3(d))
    def test_step4_valid(self):self.assertTrue(validate_step4(step4_sample()))
    def test_step4_unsafe_llm_call_rejected(self):
        d=step4_sample();d['cases'][5]['llm_called']=True
        self.assertFalse(validate_step4(d))
    def test_step5_mock_valid(self):self.assertTrue(validate_step5(step5_sample()))
    def test_step5_ollama_valid(self):self.assertTrue(validate_step5(step5_sample('ollama'), consultation='ollama'))
    def test_step5_medical_gate_override_rejected(self):
        d=step5_sample();d['cases'][2]['medical_gate']='SYNTHETIC_READY'
        self.assertFalse(validate_step5(d))
    def test_step5_missing_case_rejected(self):
        d=step5_sample();d['cases'].pop()
        self.assertFalse(validate_step5(d))
    def test_http_sample_valid(self):
        d=dict(mode='mock',passed=8,total=8,status='api_mock_smoke_pass',
            medical_knowledge_gate=GATE,all_requests_localhost=True,
            clinical_answers_generated=False, checks={str(i):True for i in range(8)})
        self.assertTrue(validate_http(d));d['checks']['0']=False
        self.assertFalse(validate_http(d))
    def test_manual_review_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'review.csv'; d=step4_sample();write_manual(f,d)
            self.assertEqual(validate_manual_csv(f,d)[0:2],('pending',0))
    def test_manual_review_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'review.csv';d=step4_sample();write_manual(f,d,'pass')
            self.assertEqual(validate_manual_csv(f,d)[0:2],('pass',3))
    def test_manual_review_wrong_citation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'review.csv';d=step4_sample();write_manual(f,d,'wrong_citation')
            self.assertEqual(validate_manual_csv(f,d)[0],'fail')
    def test_manual_review_bad_judgement_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'review.csv';d=step4_sample();write_manual(f,d,'bad_review')
            self.assertEqual(validate_manual_csv(f,d)[0],'fail')


if __name__=='__main__':
    unittest.main(verbosity=2)

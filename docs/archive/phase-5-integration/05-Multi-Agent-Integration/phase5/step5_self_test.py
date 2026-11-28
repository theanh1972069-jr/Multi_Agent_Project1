"""Pure unit contract tests + optional actual LangGraph smoke if installed."""
from __future__ import annotations

import importlib.util
import unittest

from pydantic import ValidationError

from .contracts import EXPECTED_SHA256
from .step2_prediction_integration import MockPredictionClient
from .step3_knowledge_integration import MockKnowledgeBackend
from .step4_consultation import CASES
from .step5_orchestrator import Step5Request, Step5Response, invoke_step5, make_step5_graph


def req(**kwargs):
    return Step5Request.model_validate({'request_id': 'TEST-01', 'synthetic_test_only': True, **kwargs})


class ContractTests(unittest.TestCase):
    def test_prediction_ok(self):
        self.assertEqual(req(operation='research_prediction', features={'RIDAGEYR':45,'RIAGENDR':1,'BMXBMI':28.5}).operation, 'research_prediction')

    def test_knowledge_ok(self):
        self.assertEqual(req(operation='knowledge_research_lookup',query_id='Q03').query_id,'Q03')

    def test_atlas_ok(self):
        self.assertEqual(req(operation='synthetic_rag_demo',case_id='S03').case_id, 'S03')

    def test_missing_mode(self):
        with self.assertRaises(ValidationError):
            Step5Request.model_validate({'request_id':'X','operation':'synthetic_rag_demo','case_id':'S01'})

    def test_wrong_route_fields(self):
        with self.assertRaises(ValidationError):
            req(operation='research_prediction',features={'RIDAGEYR':45,'RIAGENDR':1,'BMXBMI':28.5},case_id='S01')

    def test_arbitrary_medical_question_rejected(self):
        with self.assertRaises(ValidationError):
            req(operation='knowledge_research_lookup',query_id='Q99')

    def test_user_gate_override_rejected(self):
        with self.assertRaises(ValidationError):
            req(operation='synthetic_rag_demo',case_id='S01',medical_gate='SYNTHETIC_READY')

    def test_invalid_age(self):
        with self.assertRaises(ValidationError):
            req(operation='research_prediction',features={'RIDAGEYR':12,'RIAGENDR':1,'BMXBMI':28.5})

    def test_invalid_bmi(self):
        with self.assertRaises(ValidationError):
            req(operation='research_prediction',features={'RIDAGEYR':45,'RIAGENDR':1,'BMXBMI':float('inf')})

    def test_no_prediction_on_atlas(self):
        with self.assertRaises(ValidationError):
            Step5Response(request_id='TEST',operation='synthetic_rag_demo',status='mock_response_not_llm',medical_gate='BLOCKED_RESEARCH_ONLY',prediction={})

    def test_unauthorized_medical_answer(self):
        with self.assertRaises(ValidationError):
            Step5Response(request_id='TEST',operation='knowledge_research_lookup',status='ok',medical_gate='BLOCKED_RESEARCH_ONLY')

    def test_llm_no_prediction(self):
        with self.assertRaises(ValidationError):
            Step5Response(request_id='TEST',operation='research_prediction',status='ok',medical_gate='BLOCKED_RESEARCH_ONLY',llm_called=True)

    def test_failed_cannot_have_prediction(self):
        with self.assertRaises(ValidationError):
            Step5Response(request_id='TEST',operation='research_prediction',status='failed',medical_gate='BLOCKED_RESEARCH_ONLY',prediction={})

    def test_unsafe_citation_rejected(self):
        with self.assertRaises(ValidationError):
            Step5Response(request_id='TEST',operation='synthetic_rag_demo',status='mock_response_not_llm',medical_gate='BLOCKED_RESEARCH_ONLY',synthetic_answer='a',synthetic_citations=['NIDDK-T2D-004'])

    def test_only_synthetic_citation(self):
        x = Step5Response(request_id='TEST',operation='synthetic_rag_demo',status='mock_response_not_llm',medical_gate='BLOCKED_RESEARCH_ONLY',synthetic_answer='ok',synthetic_citations=['SYN-ATLAS-001'])
        self.assertFalse(x.llm_called)

    def test_prediction_hash_frozen(self):
        self.assertEqual(len(EXPECTED_SHA256),64)


@unittest.skipUnless(importlib.util.find_spec('langgraph'), 'LangGraph not installed in current Python')
class LangGraphSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pred = MockPredictionClient()
        cls.knowledge = MockKnowledgeBackend()
        cls.graph = make_step5_graph(prediction_client=cls.pred, knowledge_backend=cls.knowledge)

    def test_prediction_route(self):
        r = invoke_step5(self.graph, req(operation='research_prediction', features={'RIDAGEYR':45,'RIAGENDR':1,'BMXBMI':28.5}))
        self.assertEqual(r.status, 'ok')
        self.assertIsNotNone(r.prediction)
        self.assertFalse(r.llm_called)
        self.assertEqual(len(r.evidence_metadata),0)

    def test_knowledge_route(self):
        r = invoke_step5(self.graph, req(operation='knowledge_research_lookup',query_id='Q03'))
        self.assertEqual(r.status,'blocked_research_only')
        self.assertEqual(len(r.evidence_metadata),3)
        self.assertTrue(all(not x.allowed_to_answer for x in r.evidence_metadata))
        self.assertFalse(r.llm_called)

    def test_atlas_route(self):
        r = invoke_step5(self.graph, req(operation='synthetic_rag_demo',case_id='S01'))
        self.assertEqual(r.status, 'mock_response_not_llm')
        self.assertEqual(r.synthetic_citations, ['SYN-ATLAS-001'])
        self.assertFalse(r.llm_called)

    def test_abstain(self):
        r = invoke_step5(self.graph, req(operation='synthetic_rag_demo',case_id='S06'))
        self.assertEqual(r.status, 'abstained')
        self.assertIsNone(r.synthetic_answer)
        self.assertFalse(r.llm_called)

    def test_11_cases(self):
        from .step5_run import FIXTURES, evaluate_response
        for case in FIXTURES:
            with self.subTest(case=case['request_id']):
                response = invoke_step5(self.graph,Step5Request.model_validate({**case,'synthetic_test_only':True}))
                self.assertTrue(evaluate_response(case['operation'],response.model_dump(),mode='mock',llm_mode='mock',case_id=case.get('case_id')))


if __name__ == '__main__':
    unittest.main(verbosity=2)

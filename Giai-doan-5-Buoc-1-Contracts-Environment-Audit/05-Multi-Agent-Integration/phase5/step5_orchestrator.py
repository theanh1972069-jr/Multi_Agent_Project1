"""Phase 5 Step 5: unified 5-agent research sandbox orchestrator.

Three mutually exclusive routes:
- research_prediction: locked NHANES localhost API; never LLM or clinical text.
- knowledge_research_lookup: fixed Q01/Q02/Q03, Chroma+Neo4j metadata read only, BLOCKED.
- synthetic_rag_demo: fixed S01-S06, checked Atlas synthetic corpus; optional Ollama.

Not clinical decision support, production ACL, or general prompt-injection defense.
"""
from __future__ import annotations

from typing import Any, Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .contracts import (EXPECTED_SHA256, RESEARCH_WARNING, ResearchFeatures,
                        UpstreamPrediction, EvidenceMetadata)
from .step2_prediction_integration import IntegrationFailure, PredictionClient
from .step3_knowledge_integration import (EXPECTED_COUNTS, QUESTIONS, KnowledgeBackend,
                                           KnowledgeIntegrationFailure, project_evidence,
                                           validate_audit)
from .step4_consultation import (CASES, ConsultationError, execute_consultation,
                                  load_synthetic_documents)

OP_PRED = 'research_prediction'
OP_KNOW = 'knowledge_research_lookup'
OP_ATLAS = 'synthetic_rag_demo'
MEDICAL_GATE = 'BLOCKED_RESEARCH_ONLY'


class Step5Request(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    request_id: str = Field(min_length=1, max_length=64, pattern=r'^[A-Za-z0-9_-]+$')
    operation: Literal['research_prediction', 'knowledge_research_lookup', 'synthetic_rag_demo']
    synthetic_test_only: Literal[True]
    features: ResearchFeatures | None = None
    query_id: Literal['Q01', 'Q02', 'Q03'] | None = None
    case_id: Literal['S01', 'S02', 'S03', 'S04', 'S05', 'S06'] | None = None

    @model_validator(mode='after')
    def exclusive_payload(self) -> 'Step5Request':
        okay = (
            (self.operation == OP_PRED and self.features is not None and self.query_id is None and self.case_id is None)
            or (self.operation == OP_KNOW and self.features is None and self.query_id is not None and self.case_id is None)
            or (self.operation == OP_ATLAS and self.features is None and self.query_id is None and self.case_id is not None)
        )
        if not okay:
            raise ValueError('incompatible operation and payload')
        return self


class Step5Response(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    request_id: str
    operation: Literal['research_prediction', 'knowledge_research_lookup', 'synthetic_rag_demo']
    status: Literal['ok', 'blocked_research_only', 'mock_response_not_llm',
                    'llm_output_needs_human_review', 'abstained', 'failed']
    medical_gate: Literal['BLOCKED_RESEARCH_ONLY']
    prediction: UpstreamPrediction | None = None
    evidence_metadata: list[EvidenceMetadata] = Field(default_factory=list)
    synthetic_answer: str | None = None
    synthetic_citations: list[str] = Field(default_factory=list)
    llm_called: bool = False
    error_codes: list[str] = Field(default_factory=list)
    warning: str = RESEARCH_WARNING

    @model_validator(mode='after')
    def enforce_isolation(self) -> 'Step5Response':
        if self.operation != OP_PRED and self.prediction is not None:
            raise ValueError('prediction crossed operation boundary')
        if self.operation != OP_KNOW and self.evidence_metadata:
            raise ValueError('medical evidence crossed operation boundary')
        if self.operation != OP_ATLAS and (self.llm_called or self.synthetic_answer is not None or self.synthetic_citations):
            raise ValueError('LLM/synthetic answer crossed operation boundary')
        if self.operation == OP_KNOW and self.status not in {'blocked_research_only', 'failed'}:
            raise ValueError('unreviewed medical knowledge must remain blocked')
        if self.operation == OP_KNOW and any(x.allowed_to_answer for x in self.evidence_metadata):
            raise ValueError('unreviewed evidence cannot authorize answers')
        if self.operation == OP_PRED and self.status == 'ok' and self.prediction is None:
            raise ValueError('missing prediction')
        if self.status == 'failed' and (self.prediction is not None or self.synthetic_answer is not None):
            raise ValueError('failed flow may not emit result')
        if self.operation == OP_ATLAS:
            if self.synthetic_citations and (len(self.synthetic_citations) != 1 or self.synthetic_citations[0] not in {'SYN-ATLAS-001','SYN-ATLAS-002','SYN-ATLAS-003'}):
                raise ValueError('invalid synthetic citation')
            if self.synthetic_answer is not None and not self.synthetic_citations:
                raise ValueError('answer without citation')
        return self


class Step5State(TypedDict, total=False):
    request: dict[str, Any]
    route: str
    validated_features: dict[str, Any]
    prediction: dict[str, Any] | None
    evidence_metadata: list[dict[str, Any]]
    consultation: dict[str, Any]
    errors: list[str]
    final: dict[str, Any]


def make_step5_graph(*, prediction_client: PredictionClient, knowledge_backend: KnowledgeBackend,
                     consultation_mode: Literal['mock', 'ollama'] = 'mock',
                     model: str = 'qwen2.5:1.5b', llm_call=None):
    """Build and compile one 5-agent graph; calls depend on user-selected route.

    No model/db read at graph build; real backends must be constructed explicitly by caller.
    """
    if consultation_mode not in {'mock', 'ollama'}:
        raise ValueError('invalid consultation mode')
    from langgraph.graph import START, END, StateGraph

    def orchestrator_agent(state: Step5State) -> dict[str, Any]:
        try:
            req = Step5Request.model_validate(state['request'])
        except (ValidationError, KeyError, TypeError):
            return {'route': 'invalid', 'errors': ['INVALID_INPUT']}
        return {'route': req.operation, 'errors': []}

    def routing(state: Step5State) -> str:
        route = state.get('route', 'invalid')
        return {OP_PRED: 'data_analysis_agent', OP_KNOW: 'knowledge_agent',
                OP_ATLAS: 'knowledge_agent'}.get(route, 'consultation_agent')

    def data_analysis_agent(state: Step5State) -> dict[str, Any]:
        try:
            data = ResearchFeatures.model_validate(state['request']['features'])
            return {'validated_features': data.model_dump()}
        except (ValidationError, KeyError, TypeError):
            return {'errors': ['INVALID_INPUT']}

    def prediction_agent(state: Step5State) -> dict[str, Any]:
        if state.get('errors'):
            return {'prediction': None}
        try:
            features = ResearchFeatures.model_validate(state['validated_features'])
            result = prediction_client.predict(features)
            return {'prediction': result.model_dump()}
        except IntegrationFailure as exc:
            return {'prediction': None, 'errors': [exc.code]}
        except Exception:
            return {'prediction': None, 'errors': ['PREDICTION_BACKEND_ERROR']}

    def knowledge_agent(state: Step5State) -> dict[str, Any]:
        if state.get('errors'):
            return {'evidence_metadata': []}
        if state['route'] == OP_ATLAS:
            # Only Step 4's pinned synthetic corpus can be accessed in Atlas branch.
            try:
                load_synthetic_documents()
                return {'evidence_metadata': []}
            except ConsultationError as exc:
                return {'errors': [exc.code], 'evidence_metadata': []}
        try:
            req = state['request']
            validate_audit(knowledge_backend.audit())
            evidence = project_evidence(knowledge_backend.retrieve(req['query_id']))
            return {'evidence_metadata': [x.model_dump() for x in evidence]}
        except KnowledgeIntegrationFailure as exc:
            return {'errors': [exc.code], 'evidence_metadata': []}
        except Exception:
            return {'errors': ['KNOWLEDGE_BACKEND_ERROR'], 'evidence_metadata': []}

    def consultation_agent(state: Step5State) -> dict[str, Any]:
        request = state.get('request', {})
        route = state.get('route')
        errors = list(state.get('errors', []))
        base = {'request_id': str(request.get('request_id','invalid')),
                'medical_gate': MEDICAL_GATE, 'error_codes': errors, 'llm_called': False}
        if route == OP_PRED:
            prediction = state.get('prediction')
            response = Step5Response(operation=OP_PRED,
                    status='ok' if prediction is not None and not errors else 'failed',
                    prediction=prediction if not errors else None, **base)
        elif route == OP_KNOW:
            response = Step5Response(operation=OP_KNOW,
                    status='blocked_research_only' if not errors else 'failed',
                    evidence_metadata=state.get('evidence_metadata', []) if not errors else [], **base)
        elif route == OP_ATLAS:
            if errors:
                response = Step5Response(operation=OP_ATLAS,status='failed',**base)
            else:
                try:
                    kwargs = {'mode': consultation_mode, 'model': model}
                    if llm_call is not None:
                        kwargs['llm_call'] = llm_call
                    result = execute_consultation(request['case_id'], **kwargs)
                    status = ('llm_output_needs_human_review' if result['status'] == 'LLM_OUTPUT_NEEDS_HUMAN_REVIEW'
                              else 'mock_response_not_llm' if result['status'] == 'MOCK_RESPONSE_NOT_LLM'
                              else 'abstained' if result['status'].startswith('ABSTAIN_') and not result['error_codes']
                              else 'failed')
                    response = Step5Response(operation=OP_ATLAS, status=status,
                            synthetic_answer=result['answer'] if status in {'llm_output_needs_human_review','mock_response_not_llm'} else None,
                            synthetic_citations=result['citations'] if status in {'llm_output_needs_human_review','mock_response_not_llm'} else [],
                            **{**base, 'llm_called': result['llm_called'], 'error_codes': result['error_codes']})
                except ConsultationError as exc:
                    response = Step5Response(operation=OP_ATLAS,status='failed',
                            **{**base, 'error_codes':[exc.code]})
        else:
            # This branch is unreachable for valid Step5Request, but fail closed.
            response = Step5Response(operation=OP_ATLAS, status='failed',
                            **{**base,'error_codes':['INVALID_INPUT']})
        return {'final': response.model_dump()}

    builder = StateGraph(Step5State)
    for key, node in [
        ('orchestrator_agent', orchestrator_agent),
        ('data_analysis_agent', data_analysis_agent),
        ('prediction_agent', prediction_agent),
        ('knowledge_agent', knowledge_agent),
        ('consultation_agent', consultation_agent),
    ]:
        builder.add_node(key, node)
    builder.add_edge(START, 'orchestrator_agent')
    builder.add_conditional_edges('orchestrator_agent', routing,
                 {'data_analysis_agent':'data_analysis_agent',
                  'knowledge_agent':'knowledge_agent', 'consultation_agent':'consultation_agent'})
    builder.add_edge('data_analysis_agent', 'prediction_agent')
    builder.add_edge('prediction_agent', 'consultation_agent')
    builder.add_edge('knowledge_agent', 'consultation_agent')
    builder.add_edge('consultation_agent', END)
    return builder.compile()


def invoke_step5(graph, request: Step5Request) -> Step5Response:
    # Explicitly build state from validated fields; no user-controlled gate or agent errors.
    state: Step5State = {'request': request.model_dump(exclude_none=True), 'errors': []}
    result = graph.invoke(state)
    return Step5Response.model_validate(result['final'])

"""5-agent LangGraph SKELETON for Step 1 — no integrations yet.

No FastAPI/model/Neo4j/Chroma/Ollama connection is made. This is NOT the
production workflow. Steps 2-5 will replace the stubs incrementally.
"""
from __future__ import annotations
from typing import Any

from .contracts import (
    AgentState, WorkflowRequest, WorkflowResponse, ResearchFeatures,
    RESEARCH_WARNING, make_initial_state,
)


def orchestrator_agent(state: AgentState) -> dict[str, Any]:
    return {"llm_called": False}


def data_analysis_agent(state: AgentState) -> dict[str, Any]:
    if state["operation"] == "synthetic_rag_demo":
        return {}
    # This is only schema validation; no model fitting or real inference.
    validated = ResearchFeatures.model_validate(state["raw_input"]["features"])
    return {"validated_input": validated.model_dump()}


def prediction_agent(state: AgentState) -> dict[str, Any]:
    # Not a fake model score: API not yet connected in Step 1.
    return {"prediction_status": "NOT_CONNECTED", "prediction_result": None}


def knowledge_agent(state: AgentState) -> dict[str, Any]:
    # Never use an unverified medical relation to authorize LLM answering.
    gate = "BLOCKED_RESEARCH_ONLY" if state["operation"] == "research_prediction" else "NOT_EVALUATED"
    return {"knowledge_gate": gate, "evidence_metadata": [], "knowledge_status": "NOT_CONNECTED"}


def consultation_agent(state: AgentState) -> dict[str, Any]:
    # This is a non-LLM formatter only. No medical advice or invented prediction.
    response = WorkflowResponse(
        request_id=state["request_id"],
        operation=state["operation"],
        status="not_connected",
        knowledge_gate=state["knowledge_gate"],
        llm_called=False,
        warning=RESEARCH_WARNING,
    )
    return {"final_response": response.model_dump(), "llm_called": False}


def build_step1_graph():
    # Delayed import lets contract tests run without optional LangGraph.
    from langgraph.graph import END, START, StateGraph

    builder = StateGraph(AgentState)
    builder.add_node("orchestrator_agent", orchestrator_agent)
    builder.add_node("data_analysis_agent", data_analysis_agent)
    builder.add_node("prediction_agent", prediction_agent)
    builder.add_node("knowledge_agent", knowledge_agent)
    builder.add_node("consultation_agent", consultation_agent)
    builder.add_edge(START, "orchestrator_agent")
    builder.add_edge("orchestrator_agent", "data_analysis_agent")
    builder.add_edge("data_analysis_agent", "prediction_agent")
    builder.add_edge("prediction_agent", "knowledge_agent")
    builder.add_edge("knowledge_agent", "consultation_agent")
    builder.add_edge("consultation_agent", END)
    return builder.compile()


def run_synthetic_smoke() -> dict[str, Any]:
    graph = build_step1_graph()
    req = WorkflowRequest.model_validate({
        "request_id": "phase5step1-synthetic-001", "operation": "research_prediction",
        "features": {"RIDAGEYR": 45, "RIAGENDR": 1, "BMXBMI": 28.5},
    })
    outcome = graph.invoke(make_initial_state(req))
    result = WorkflowResponse.model_validate(outcome["final_response"])
    assert result.prediction is None
    assert result.knowledge_gate == "BLOCKED_RESEARCH_ONLY"
    assert result.llm_called is False
    return {
        "graph_compiled": True,
        "agent_nodes": 5,
        "status": result.status,
        "prediction": None,
        "knowledge_gate": result.knowledge_gate,
        "llm_called": result.llm_called,
        "db_writes": False,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run_synthetic_smoke(), ensure_ascii=False, indent=2))

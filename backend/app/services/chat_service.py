from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ai_services.ml.predictor import NHANESPredictor
from ai_services.orchestration.graph import MultiAgentOrchestrator
from backend.app.core.logging_utils import get_logger, sanitize_log_context
from backend.app.db.base import utcnow
from backend.app.db.models import AgentRun, ChatMessage, ChatSession, User
from backend.app.schemas.chat import (
    ChatMessageCreateRequest,
    ChatMessageOut,
    ChatSessionCreateRequest,
    ChatSessionOut,
)
from backend.app.services import (
    get_active_source_ids,
    get_owned_assessment,
    persist_agent_run,
    serialize_agent_steps,
    serialize_prediction_row,
)

logger = get_logger(__name__)


def _to_session_out(session: ChatSession) -> ChatSessionOut:
    return ChatSessionOut(
        id=session.id,
        title=session.title,
        linked_assessment_id=session.linked_assessment_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _get_owned_session(db: Session, session_id: str, user_id: str) -> ChatSession:
    session = db.scalar(select(ChatSession).where(ChatSession.id == session_id))
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this chat session",
        )
    return session


def _to_message_out(
    msg: ChatMessage,
    *,
    agent_run: AgentRun | None = None,
    kg_source: str | None = None,
    llm_used: bool = False,
    llm_fallback: bool = False,
) -> ChatMessageOut:
    steps = serialize_agent_steps(list(agent_run.steps)) if agent_run is not None else []
    return ChatMessageOut(
        id=msg.id,
        session_id=msg.session_id,
        role=msg.role,
        content=msg.content,
        answer=msg.content if msg.role == "assistant" else None,
        intent=msg.intent,
        citations=list(msg.citations_json or []),
        kg_relations=list(msg.kg_relations_json or []),
        kg_source=kg_source,
        redirect_to_assessment=(msg.intent == "risk_assessment_redirect"),
        safety_flag=msg.safety_flag,
        llm_used=llm_used,
        llm_fallback=llm_fallback,
        agent_steps=steps,
        total_latency_ms=agent_run.total_latency_ms if agent_run is not None else 0,
        created_at=msg.created_at,
    )


def list_user_sessions(db: Session, *, user_id: str) -> list[ChatSessionOut]:
    """List chat sessions owned by `user_id` ordered by most recently updated."""
    rows = list(
        db.scalars(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
        ).all()
    )
    return [_to_session_out(row) for row in rows]


def create_chat_session(
    db: Session,
    *,
    current_user: User,
    payload: ChatSessionCreateRequest,
) -> ChatSessionOut:
    """Create a chat session for `current_user`, validating any linked assessment ownership."""
    linked_id = payload.linked_assessment_id
    if linked_id is not None:
        get_owned_assessment(db, linked_id, current_user.id)

    session = ChatSession(
        user_id=current_user.id,
        title=payload.title,
        linked_assessment_id=linked_id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _to_session_out(session)


def list_session_messages(
    db: Session,
    *,
    session_id: str,
    user_id: str,
) -> list[ChatMessageOut]:
    """List messages inside an owned chat session in chronological order."""
    _get_owned_session(db, session_id, user_id)
    messages = list(
        db.scalars(
            select(ChatMessage)
            .options(joinedload(ChatMessage.agent_run).joinedload(AgentRun.steps))
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        .unique()
        .all()
    )
    return [
        _to_message_out(msg, agent_run=msg.agent_run)
        for msg in messages
    ]


def send_chat_message(
    db: Session,
    *,
    session_id: str,
    current_user: User,
    payload: ChatMessageCreateRequest,
    orchestrator: MultiAgentOrchestrator,
    predictor: NHANESPredictor | None = None,
) -> ChatMessageOut:
    """Persist user message, run multi-agent chat pipeline, and return assistant reply."""
    session = _get_owned_session(db, session_id, current_user.id)

    if "linked_assessment_id" in payload.model_fields_set:
        effective_assessment_id = payload.linked_assessment_id
    else:
        effective_assessment_id = session.linked_assessment_id

    linked_assessment_dict: dict[str, Any] | None = None
    if effective_assessment_id is not None:
        assessment = get_owned_assessment(db, effective_assessment_id, current_user.id)
        linked_assessment_dict = {
            "id": assessment.id,
            "status": assessment.status,
            "derived_features": assessment.derived_features_json,
            "prediction": serialize_prediction_row(
                assessment.prediction_result, predictor=predictor
            ),
        }

    if "linked_assessment_id" in payload.model_fields_set:
        session.linked_assessment_id = effective_assessment_id

    prior_messages = list(
        db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.asc())
        ).all()
    )
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in prior_messages[-8:]
    ]

    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=payload.content,
    )
    db.add(user_msg)
    db.flush()

    request_id = f"chat_{uuid4().hex[:16]}"
    active_source_ids = get_active_source_ids(db)
    result = orchestrator.run_chat(
        request_id=request_id,
        message=payload.content,
        linked_assessment=linked_assessment_dict,
        history=history,
        active_source_ids=active_source_ids,
    )

    agent_run = persist_agent_run(
        db,
        request_id=request_id,
        user_id=current_user.id,
        task_type="chat",
        result=result,
    )

    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=str(result.get("answer") or ""),
        intent=result.get("intent"),
        citations_json=list(result.get("citations") or []),
        kg_relations_json=list(result.get("kg_relations") or []),
        agent_run_id=agent_run.id,
        safety_flag=result.get("safety_flag"),
    )
    db.add(assistant_msg)
    session.updated_at = utcnow()
    db.commit()
    db.refresh(assistant_msg)
    db.refresh(agent_run)

    logger.info(
        "Chat turn processed: %s",
        sanitize_log_context(
            {
                "request_id": request_id,
                "user_id": current_user.id,
                "session_id": session.id,
                "intent": assistant_msg.intent,
                "safety_flag": assistant_msg.safety_flag,
                "total_latency_ms": agent_run.total_latency_ms,
            }
        ),
    )

    return _to_message_out(
        assistant_msg,
        agent_run=agent_run,
        kg_source=result.get("kg_source"),
        llm_used=bool(result.get("llm_used", False)),
        llm_fallback=bool(result.get("llm_fallback", False)),
    )

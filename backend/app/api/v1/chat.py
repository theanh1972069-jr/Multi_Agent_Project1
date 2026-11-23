from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ai_services.orchestration.graph import MultiAgentOrchestrator
from backend.app.api.deps import get_current_user, get_db, get_orchestrator
from backend.app.db.models import User
from backend.app.schemas.chat import (
    ChatMessageCreateRequest,
    ChatMessageOut,
    ChatSessionCreateRequest,
    ChatSessionOut,
)
from backend.app.services.chat_service import (
    create_chat_session,
    list_session_messages,
    list_user_sessions,
    send_chat_message,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/sessions", response_model=list[ChatSessionOut])
def get_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChatSessionOut]:
    """List chat sessions belonging to the authenticated user."""
    return list_user_sessions(db, user_id=current_user.id)


@router.post(
    "/sessions",
    response_model=ChatSessionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    payload: ChatSessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatSessionOut:
    """Create a new chat session, verifying ownership of any linked assessment."""
    return create_chat_session(db, current_user=current_user, payload=payload)


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
def get_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChatMessageOut]:
    """List chronological messages for an owned chat session."""
    return list_session_messages(db, session_id=session_id, user_id=current_user.id)


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageOut)
def post_message(
    session_id: str,
    payload: ChatMessageCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    orchestrator: MultiAgentOrchestrator = Depends(get_orchestrator),
) -> ChatMessageOut:
    """Submit a user chat message and receive the grounded multi-agent response."""
    return send_chat_message(
        db,
        session_id=session_id,
        current_user=current_user,
        payload=payload,
        orchestrator=orchestrator,
        predictor=orchestrator.predictor,
    )

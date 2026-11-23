from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ai_services.knowledge.service import HybridKnowledgeService
from ai_services.orchestration.graph import MultiAgentOrchestrator
from backend.app.core.config import Settings
from backend.app.core.security import decode_access_token
from backend.app.db.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_app_settings(request: Request) -> Settings:
    """Return the active application Settings attached to `app.state`."""
    return request.app.state.settings


def get_db(request: Request) -> Iterator[Session]:
    """Yield a per-request SQLAlchemy Session and close it after completion."""
    session_factory = request.app.state.session_factory
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def get_knowledge_service(request: Request) -> HybridKnowledgeService:
    """Return the initialized HybridKnowledgeService from `app.state`."""
    return request.app.state.knowledge_service


def get_orchestrator(request: Request) -> MultiAgentOrchestrator:
    """Return the initialized MultiAgentOrchestrator from `app.state`."""
    return request.app.state.orchestrator


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> User:
    """Authenticate Bearer JWT and load the corresponding active User."""
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not credentials.credentials
    ):
        raise auth_error

    try:
        payload = decode_access_token(credentials.credentials, settings)
    except JWTError as exc:
        raise auth_error from exc

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise auth_error

    user = db.scalar(
        select(User).options(joinedload(User.profile)).where(User.id == user_id)
    )
    if user is None:
        raise auth_error
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require that the authenticated user holds the `admin` role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user

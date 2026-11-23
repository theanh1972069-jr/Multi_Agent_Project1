from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from ai_services.knowledge.service import HybridKnowledgeService
from backend.app.api.deps import (
    get_app_settings,
    get_db,
    get_knowledge_service,
    require_admin,
)
from backend.app.core.config import Settings
from backend.app.db.models import User
from backend.app.schemas.admin import (
    AdminAgentRunOut,
    AdminDocumentDeleteOut,
    AdminDocumentOut,
    AdminDocumentStatusUpdateRequest,
    AdminStatsOut,
    AdminUserUpdateRequest,
)
from backend.app.schemas.auth import UserOut
from backend.app.services.admin_service import (
    delete_document,
    get_admin_stats,
    list_all_documents,
    list_all_users,
    list_recent_agent_runs,
    set_document_status,
    update_user_account,
    upload_and_ingest_document,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsOut)
def read_admin_stats(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminStatsOut:
    """Return system-wide user, assessment, knowledge base, and agent latency statistics."""
    return get_admin_stats(db)


@router.get("/agent-runs", response_model=list[AdminAgentRunOut])
def read_agent_runs(
    limit: int = Query(default=50, ge=1, le=200),
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AdminAgentRunOut]:
    """List recent sanitized multi-agent execution runs and per-step traces."""
    return list_recent_agent_runs(db, limit=limit)


@router.get("/documents", response_model=list[AdminDocumentOut])
def read_documents(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AdminDocumentOut]:
    """List all knowledge documents (both active and inactive)."""
    return list_all_documents(db)


@router.post(
    "/documents/upload",
    response_model=AdminDocumentOut,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    title: str = Form(...),
    publisher: str = Form(...),
    language: str = Form("vi"),
    source_url: str | None = Form(None),
    source_id: str | None = Form(None),
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    knowledge_service: HybridKnowledgeService = Depends(get_knowledge_service),
) -> AdminDocumentOut:
    """Upload and ingest a `.txt`, `.md`, or `.pdf` document into ChromaDB and SQL."""
    return upload_and_ingest_document(
        db,
        current_user=admin,
        settings=settings,
        knowledge_service=knowledge_service,
        title=title,
        publisher=publisher,
        language=language,
        source_url=source_url,
        source_id=source_id,
        file=file,
    )


@router.patch("/documents/{doc_id}/status", response_model=AdminDocumentOut)
def toggle_document_status(
    doc_id: str,
    payload: AdminDocumentStatusUpdateRequest,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    knowledge_service: HybridKnowledgeService = Depends(get_knowledge_service),
) -> AdminDocumentOut:
    """Activate or deactivate a knowledge document across SQL, ChromaDB, and KG."""
    return set_document_status(
        db,
        knowledge_service=knowledge_service,
        doc_id=doc_id,
        new_status=payload.status,
    )


@router.delete("/documents/{doc_id}", response_model=AdminDocumentDeleteOut)
def remove_document(
    doc_id: str,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    knowledge_service: HybridKnowledgeService = Depends(get_knowledge_service),
) -> AdminDocumentDeleteOut:
    """Delete a knowledge document and its chunks from ChromaDB, KG, and SQL."""
    return delete_document(
        db,
        knowledge_service=knowledge_service,
        settings=settings,
        doc_id=doc_id,
    )


@router.get("/users", response_model=list[UserOut])
def read_users(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[UserOut]:
    """List all user accounts for administration."""
    return list_all_users(db)


@router.patch("/users/{user_id}", response_model=UserOut)
def patch_user(
    user_id: str,
    payload: AdminUserUpdateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserOut:
    """Enable/disable a user account or change its role."""
    return update_user_account(
        db,
        current_user=admin,
        user_id=user_id,
        payload=payload,
    )

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ai_services.knowledge.chunking import extract_text_from_file
from ai_services.knowledge.service import HybridKnowledgeService
from backend.app.api.v1.auth import _to_user_out
from backend.app.core.config import Settings
from backend.app.db.models import (
    AgentRun,
    AgentStep,
    HealthAssessment,
    KnowledgeChunk,
    KnowledgeDocument,
    User,
)
from backend.app.schemas.admin import (
    AdminAgentRunOut,
    AdminDocumentDeleteOut,
    AdminDocumentOut,
    AdminStatsOut,
    AdminUserUpdateRequest,
)
from backend.app.schemas.auth import UserOut
from backend.app.services import serialize_agent_steps

ALLOWED_DOCUMENT_EXTENSIONS: frozenset[str] = frozenset({".txt", ".md", ".pdf"})
MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024
MAX_TITLE_LENGTH: int = 512
MAX_PUBLISHER_LENGTH: int = 255
MAX_LANGUAGE_LENGTH: int = 16
MAX_SOURCE_URL_LENGTH: int = 1024
_SOURCE_ID_RE = re.compile(r"[^A-Za-z0-9_-]+")


def _to_admin_document_out(doc: KnowledgeDocument) -> AdminDocumentOut:
    return AdminDocumentOut(
        id=doc.id,
        source_id=doc.source_id,
        title=doc.title,
        publisher=doc.publisher,
        source_url=doc.source_url,
        language=doc.language,
        status=doc.status,
        chunk_count=doc.chunk_count,
        uploaded_by=doc.uploaded_by,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


def get_admin_stats(db: Session) -> AdminStatsOut:
    """Compute aggregated user, assessment, knowledge base, and multi-agent telemetry stats."""
    total_users = int(db.scalar(select(func.count(User.id))) or 0)
    total_assessments = int(db.scalar(select(func.count(HealthAssessment.id))) or 0)
    total_documents = int(db.scalar(select(func.count(KnowledgeDocument.id))) or 0)
    active_documents = int(
        db.scalar(
            select(func.count(KnowledgeDocument.id)).where(
                KnowledgeDocument.status == "active"
            )
        )
        or 0
    )
    total_chunks = int(db.scalar(select(func.count(KnowledgeChunk.id))) or 0)
    total_agent_runs = int(db.scalar(select(func.count(AgentRun.id))) or 0)

    status_rows = db.execute(
        select(AgentRun.status, func.count(AgentRun.id)).group_by(AgentRun.status)
    ).all()
    agent_status_counts = {str(row[0]): int(row[1]) for row in status_rows}

    avg_latency_raw = db.scalar(select(func.avg(AgentRun.total_latency_ms)))
    avg_latency_ms = round(float(avg_latency_raw), 2) if avg_latency_raw is not None else 0.0

    per_agent_rows = db.execute(
        select(AgentStep.agent_name, func.avg(AgentStep.latency_ms)).group_by(
            AgentStep.agent_name
        )
    ).all()
    per_agent_latency_ms = {
        str(row[0]): round(float(row[1] or 0.0), 2) for row in per_agent_rows
    }

    return AdminStatsOut(
        total_users=total_users,
        total_assessments=total_assessments,
        active_documents=active_documents,
        total_documents=total_documents,
        total_chunks=total_chunks,
        total_agent_runs=total_agent_runs,
        agent_status_counts=agent_status_counts,
        avg_latency_ms=avg_latency_ms,
        per_agent_latency_ms=per_agent_latency_ms,
    )


def list_recent_agent_runs(db: Session, *, limit: int = 50) -> list[AdminAgentRunOut]:
    """Return recent multi-agent runs with ordered sanitized step traces."""
    safe_limit = max(1, min(limit, 200))
    runs = list(
        db.scalars(
            select(AgentRun)
            .options(joinedload(AgentRun.steps))
            .order_by(AgentRun.created_at.desc())
            .limit(safe_limit)
        )
        .unique()
        .all()
    )
    return [
        AdminAgentRunOut(
            id=run.id,
            request_id=run.request_id,
            user_id=run.user_id,
            task_type=run.task_type,
            status=run.status,
            total_latency_ms=run.total_latency_ms,
            llm_provider=run.llm_provider,
            llm_model=run.llm_model,
            error_code=run.error_code,
            created_at=run.created_at,
            agent_steps=serialize_agent_steps(list(run.steps)),
        )
        for run in runs
    ]


def list_all_documents(db: Session) -> list[AdminDocumentOut]:
    """List all knowledge documents regardless of active/inactive status."""
    docs = list(
        db.scalars(
            select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
        ).all()
    )
    return [_to_admin_document_out(doc) for doc in docs]


def _build_source_id(raw_source_id: str | None) -> str:
    if raw_source_id and raw_source_id.strip():
        cleaned = _SOURCE_ID_RE.sub("-", raw_source_id.strip()).strip("-_")
        if cleaned:
            return cleaned[:128]
    return f"DOC-{uuid4().hex[:10].upper()}"


def upload_and_ingest_document(
    db: Session,
    *,
    current_user: User,
    settings: Settings,
    knowledge_service: HybridKnowledgeService,
    title: str,
    publisher: str,
    language: str,
    source_url: str | None,
    source_id: str | None,
    file: UploadFile,
) -> AdminDocumentOut:
    """Validate, store, extract, chunk, embed, and persist an uploaded knowledge file."""
    cleaned_title = title.strip()
    cleaned_publisher = publisher.strip()
    if not cleaned_title or not cleaned_publisher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title and publisher are required",
        )
    if len(cleaned_title) > MAX_TITLE_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Title exceeds maximum length of {MAX_TITLE_LENGTH} characters",
        )
    if len(cleaned_publisher) > MAX_PUBLISHER_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Publisher exceeds maximum length of {MAX_PUBLISHER_LENGTH} characters",
        )

    cleaned_lang = (language.strip() or "vi").lower()
    if len(cleaned_lang) > MAX_LANGUAGE_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Language exceeds maximum length of {MAX_LANGUAGE_LENGTH} characters",
        )

    cleaned_url = source_url.strip() if source_url and source_url.strip() else None
    if cleaned_url is not None and len(cleaned_url) > MAX_SOURCE_URL_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"source_url exceeds maximum length of {MAX_SOURCE_URL_LENGTH} characters",
        )

    filename = Path(file.filename or "").name
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file extension. Only .txt, .md, and .pdf files are allowed.",
        )

    raw_bytes = file.file.read(MAX_UPLOAD_BYTES + 1)
    if not raw_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 5 MB maximum limit",
        )

    effective_source_id = _build_source_id(source_id)
    existing = db.scalar(
        select(KnowledgeDocument.id).where(
            KnowledgeDocument.source_id == effective_source_id
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"source_id '{effective_source_id}' already exists",
        )

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest_path = upload_dir / f"{effective_source_id}{ext}"
    dest_path.write_bytes(raw_bytes)

    try:
        extracted_text = extract_text_from_file(dest_path)
    except Exception as exc:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to extract readable text from uploaded file",
        ) from exc

    if not extracted_text or not extracted_text.strip():
        dest_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file contains no readable text",
        )

    try:
        chunks = knowledge_service.ingest_document(
            source_id=effective_source_id,
            title=cleaned_title,
            publisher=cleaned_publisher,
            source_url=cleaned_url,
            language=cleaned_lang,
            text=extracted_text,
        )
        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file produced no valid text chunks",
            )

        doc = KnowledgeDocument(
            source_id=effective_source_id,
            title=cleaned_title,
            publisher=cleaned_publisher,
            source_url=cleaned_url,
            language=cleaned_lang,
            file_path=str(dest_path),
            status="active",
            chunk_count=len(chunks),
            uploaded_by=current_user.id,
        )
        for idx, chunk in enumerate(chunks):
            preview = str(chunk.get("content_preview") or chunk.get("text") or "")[:512]
            token_est = int(chunk.get("token_estimate") or max(1, len(preview.split())))
            doc.chunks.append(
                KnowledgeChunk(
                    chunk_index=int(chunk.get("chunk_index", idx)),
                    chroma_id=str(chunk["chunk_id"]),
                    content_preview=preview,
                    token_estimate=token_est,
                )
            )

        db.add(doc)
        db.commit()
        db.refresh(doc)
    except Exception:
        db.rollback()
        knowledge_service.delete_source(effective_source_id)
        dest_path.unlink(missing_ok=True)
        raise

    return _to_admin_document_out(doc)


def set_document_status(
    db: Session,
    *,
    knowledge_service: HybridKnowledgeService,
    doc_id: str,
    new_status: str,
) -> AdminDocumentOut:
    """Toggle a knowledge document between `active` and `inactive` across DB, ChromaDB, and KG."""
    doc = db.scalar(select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id))
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge document not found",
        )

    doc.status = new_status
    knowledge_service.set_source_active(doc.source_id, new_status == "active")
    db.commit()
    db.refresh(doc)
    return _to_admin_document_out(doc)


def delete_document(
    db: Session,
    *,
    knowledge_service: HybridKnowledgeService,
    settings: Settings,
    doc_id: str,
) -> AdminDocumentDeleteOut:
    """Delete a knowledge document and its chunks from ChromaDB, KG, disk uploads, and DB."""
    doc = db.scalar(select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id))
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge document not found",
        )

    source_id = doc.source_id
    knowledge_service.delete_source(source_id)

    try:
        upload_root = Path(settings.upload_dir).resolve()
        file_path = Path(doc.file_path).resolve()
        if file_path.is_file() and upload_root in file_path.parents:
            file_path.unlink(missing_ok=True)
    except OSError:
        pass

    db.delete(doc)
    db.commit()
    return AdminDocumentDeleteOut(deleted=True, id=doc_id, source_id=source_id)


def list_all_users(db: Session) -> list[UserOut]:
    """Return all user accounts with their profile metadata."""
    users = list(
        db.scalars(
            select(User)
            .options(joinedload(User.profile))
            .order_by(User.created_at.desc())
        ).all()
    )
    return [_to_user_out(user) for user in users]


def update_user_account(
    db: Session,
    *,
    current_user: User,
    user_id: str,
    payload: AdminUserUpdateRequest,
) -> UserOut:
    """Update a user's `is_active` status or `role`, preventing admin self-lockout."""
    user = db.scalar(
        select(User).options(joinedload(User.profile)).where(User.id == user_id)
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    fields = payload.model_fields_set
    if user.id == current_user.id:
        if "is_active" in fields and payload.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own admin account",
            )
        if "role" in fields and payload.role is not None and payload.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote your own admin account",
            )

    if "is_active" in fields and payload.is_active is not None:
        user.is_active = payload.is_active
    if "role" in fields and payload.role is not None:
        user.role = payload.role

    db.commit()
    db.refresh(user)
    return _to_user_out(user)

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_services.knowledge.service import HybridKnowledgeService
from backend.app.api.deps import get_current_user, get_db, get_knowledge_service
from backend.app.db.models import KnowledgeDocument, User
from backend.app.schemas.knowledge import KnowledgeGraphOut, KnowledgeSourceOut
from backend.app.services import get_active_source_ids

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/sources", response_model=list[KnowledgeSourceOut])
def list_active_sources(
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[KnowledgeSourceOut]:
    """List all currently active diabetes knowledge documents."""
    docs = list(
        db.scalars(
            select(KnowledgeDocument)
            .where(KnowledgeDocument.status == "active")
            .order_by(KnowledgeDocument.created_at.asc())
        ).all()
    )
    return [
        KnowledgeSourceOut(
            id=doc.id,
            source_id=doc.source_id,
            title=doc.title,
            publisher=doc.publisher,
            source_url=doc.source_url,
            language=doc.language,
            status=doc.status,
            chunk_count=doc.chunk_count,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
        for doc in docs
    ]


@router.get("/graph", response_model=KnowledgeGraphOut)
def get_knowledge_graph(
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    knowledge_service: HybridKnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeGraphOut:
    """Return Diabetes Knowledge Graph nodes and edges filtered to active sources."""
    active_source_ids = get_active_source_ids(db)
    payload = knowledge_service.get_graph_payload(active_source_ids=active_source_ids)
    return KnowledgeGraphOut(
        nodes=list(payload.get("nodes") or []),
        edges=list(payload.get("edges") or []),
        kg_source=str(payload.get("kg_source") or "local_mirror"),
    )

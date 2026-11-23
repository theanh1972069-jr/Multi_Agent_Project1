from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ai_services.knowledge.service import HybridKnowledgeService
from backend.app.api.deps import get_app_settings, get_db, get_knowledge_service
from backend.app.core.config import Settings
from backend.app.db.models import KnowledgeChunk, KnowledgeDocument

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    knowledge_service: HybridKnowledgeService = Depends(get_knowledge_service),
) -> dict[str, Any]:
    """Report backend, database, ML model, knowledge base, and LLM readiness."""
    db_connected = False
    active_documents = 0
    total_chunks = 0
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
        active_documents = int(
            db.scalar(
                select(func.count(KnowledgeDocument.id)).where(
                    KnowledgeDocument.status == "active"
                )
            )
            or 0
        )
        total_chunks = int(
            db.scalar(
                select(func.count(KnowledgeChunk.id))
                .join(
                    KnowledgeDocument,
                    KnowledgeChunk.document_id == KnowledgeDocument.id,
                )
                .where(KnowledgeDocument.status == "active")
            )
            or 0
        )
    except Exception:
        db_connected = False

    predictor = getattr(request.app.state, "predictor", None)
    if predictor is not None:
        manifest = predictor.manifest
        ml_model = {
            "loaded": True,
            "model_version": manifest.get("model_version"),
            "model_name": manifest.get("model_name"),
            "model_sha256": getattr(predictor, "_actual_sha256", manifest.get("model_sha256")),
        }
    else:
        ml_model = {
            "loaded": False,
            "model_version": None,
            "model_name": None,
            "model_sha256": None,
        }

    kg_health = knowledge_service.kg_store.health_check()

    llm_provider = getattr(request.app.state, "llm_provider", None)
    llm_reachable = bool(llm_provider.health_check()) if llm_provider is not None else False
    llm_info = {
        "provider": getattr(llm_provider, "provider_name", settings.llm_provider),
        "model": getattr(llm_provider, "model_name", ""),
        "reachable": llm_reachable,
    }

    overall_ok = db_connected and bool(ml_model["loaded"])
    return {
        "status": "ok" if overall_ok else "degraded",
        "database": {"connected": db_connected},
        "ml_model": ml_model,
        "knowledge_base": {
            "active_documents": active_documents,
            "total_chunks": total_chunks,
            "kg_source": kg_health["kg_source"],
            "neo4j_configured": kg_health["neo4j_configured"],
            "neo4j_reachable": kg_health["neo4j_reachable"],
        },
        "llm": llm_info,
    }

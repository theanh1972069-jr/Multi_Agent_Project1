from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_services.knowledge.chunking import chunk_text, extract_text_from_file
from ai_services.knowledge.kg_seed import REPO_ROOT
from ai_services.knowledge.service import HybridKnowledgeService
from backend.app.core.security import hash_password
from backend.app.db.models import KnowledgeChunk, KnowledgeDocument, User, UserProfile

DEMO_ACCOUNTS: tuple[dict[str, str], ...] = (
    {
        "email": "user@demo.local",
        "password": "DemoUser123!",
        "full_name": "Người dùng Demo",
        "role": "user",
    },
    {
        "email": "admin@demo.local",
        "password": "DemoAdmin123!",
        "full_name": "Quản trị viên Demo",
        "role": "admin",
    },
)


def seed_demo_users(db: Session) -> None:
    """Seed the default demo user and admin accounts when `users` is empty."""
    has_users = db.scalar(select(User.id).limit(1)) is not None
    if has_users:
        return

    for account in DEMO_ACCOUNTS:
        user = User(
            email=account["email"],
            password_hash=hash_password(account["password"]),
            full_name=account["full_name"],
            role=account["role"],
            is_active=True,
        )
        user.profile = UserProfile(preferred_language="vi")
        db.add(user)
    db.commit()


def _load_chunks_for_source(
    knowledge_service: HybridKnowledgeService,
    entry: dict[str, Any],
) -> list[dict[str, Any]]:
    if isinstance(entry.get("chunks"), list) and entry["chunks"]:
        return list(entry["chunks"])

    source_id = str(entry["source_id"])
    stored = knowledge_service.rag_store._collection.get(
        where={"source_id": source_id},
        include=["documents", "metadatas"],
    )
    ids = stored.get("ids") or []
    docs = stored.get("documents") or []
    metas = stored.get("metadatas") or []
    if ids:
        rows: list[dict[str, Any]] = []
        for idx, (cid, doc_text, meta) in enumerate(zip(ids, docs, metas)):
            text = str(doc_text or "")
            meta_dict = meta or {}
            rows.append(
                {
                    "chunk_id": str(cid),
                    "chunk_index": int(meta_dict.get("chunk_index", idx)),
                    "content_preview": text[:200],
                    "token_estimate": max(1, len(text.split())),
                }
            )
        rows.sort(key=lambda item: item["chunk_index"])
        return rows

    raw_path = Path(entry["file_path"])
    file_path = raw_path if raw_path.is_absolute() else (REPO_ROOT / raw_path)
    text = extract_text_from_file(file_path)
    return chunk_text(text, source_id=source_id, chunk_size=650, overlap=100)


def seed_knowledge_documents(
    db: Session,
    knowledge_service: HybridKnowledgeService,
) -> None:
    """Ensure ChromaDB default sources exist and seed SQL knowledge tables if empty."""
    seeded_meta = knowledge_service.seed_default_sources_if_empty()

    has_docs = db.scalar(select(KnowledgeDocument.id).limit(1)) is not None
    if has_docs:
        return

    for entry in seeded_meta:
        chunks = _load_chunks_for_source(knowledge_service, entry)
        doc = KnowledgeDocument(
            source_id=str(entry["source_id"]),
            title=str(entry["title"]),
            publisher=str(entry["publisher"]),
            source_url=entry.get("source_url"),
            language=str(entry.get("language") or "en"),
            file_path=str(entry["file_path"]),
            status=str(entry.get("status") or "active"),
            chunk_count=len(chunks),
        )
        for idx, chunk in enumerate(chunks):
            preview = str(chunk.get("content_preview") or chunk.get("text") or "")[:200]
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


def seed_initial_data(
    db: Session,
    knowledge_service: HybridKnowledgeService,
) -> None:
    """Seed initial demo accounts and default diabetes knowledge documents."""
    seed_demo_users(db)
    seed_knowledge_documents(db, knowledge_service)

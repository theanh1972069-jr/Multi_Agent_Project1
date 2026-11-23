from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from ai_services.knowledge.chunking import chunk_text, extract_text_from_file
from ai_services.knowledge.kg_seed import REPO_ROOT, load_default_source_registry
from ai_services.knowledge.kg_store import DiabetesKGStore, KGRelation
from ai_services.knowledge.rag_store import ChromaRAGStore
from ai_services.safety.guardrails import sanitize_untrusted_text


class CitationItem(BaseModel):
    """Single retrieved evidence chunk from ChromaDB."""

    index: int
    chunk_id: str
    source_id: str
    title: str
    publisher: str
    url: str | None = None
    snippet: str
    score: float


class EvidenceBundle(BaseModel):
    """Combined RAG citations and Knowledge Graph relations for downstream Consultation Agent."""

    citations: list[CitationItem]
    kg_relations: list[KGRelation]
    kg_source: Literal["neo4j", "local_mirror"]
    has_relevant_evidence: bool


class HybridKnowledgeService:
    """Unified Hybrid Knowledge Service combining ChromaDB RAG and Neo4j/Local-Mirror KG."""

    def __init__(
        self,
        chroma_dir: Path,
        kg_mirror_path: Path,
        *,
        use_lightweight_embedder: bool = False,
        neo4j_uri: str | None = None,
        neo4j_username: str | None = None,
        neo4j_password: str | None = None,
        neo4j_database: str | None = None,
        embed_model_name: str = "intfloat/multilingual-e5-small",
    ) -> None:
        self.chroma_dir = Path(chroma_dir)
        self.kg_mirror_path = Path(kg_mirror_path)
        self.rag_store = ChromaRAGStore(
            chroma_dir=self.chroma_dir,
            use_lightweight_embedder=use_lightweight_embedder,
            embed_model_name=embed_model_name,
        )
        self.kg_store = DiabetesKGStore(
            kg_mirror_path=self.kg_mirror_path,
            neo4j_uri=neo4j_uri,
            neo4j_username=neo4j_username,
            neo4j_password=neo4j_password,
            neo4j_database=neo4j_database,
        )
        self._inactive_source_ids: set[str] = set()
        self._deleted_source_ids: set[str] = set()

    def _effective_active_ids(self, active_source_ids: set[str] | None) -> set[str] | None:
        blocked = self._inactive_source_ids | self._deleted_source_ids
        if active_source_ids is not None:
            return {sid for sid in active_source_ids if sid not in blocked}
        if not blocked:
            return None
        return self.kg_store.known_source_ids() - blocked

    def seed_default_sources_if_empty(self) -> list[dict]:
        """Seed the 7 vetted diabetes documents into ChromaDB if the vector store is empty."""
        registry = load_default_source_registry()
        already_populated = self.rag_store.count_chunks() > 0

        seeded_meta: list[dict] = []
        for entry in registry:
            raw_path = Path(entry["file_path"])
            file_path = raw_path if raw_path.is_absolute() else (REPO_ROOT / raw_path)
            if already_populated:
                seeded_meta.append({**entry, "status": "active"})
                continue

            text = extract_text_from_file(file_path)
            chunks = self.ingest_document(
                source_id=entry["source_id"],
                title=entry["title"],
                publisher=entry["publisher"],
                source_url=entry["source_url"],
                language=entry["language"],
                text=text,
            )
            seeded_meta.append(
                {
                    **entry,
                    "status": "active",
                    "chunk_count": len(chunks),
                }
            )
        return seeded_meta

    def ingest_document(
        self,
        source_id: str,
        title: str,
        publisher: str,
        source_url: str | None,
        language: str,
        text: str,
    ) -> list[dict]:
        """Chunk and embed a document into ChromaDB as active."""
        self._inactive_source_ids.discard(source_id)
        self._deleted_source_ids.discard(source_id)

        chunks = chunk_text(text, source_id=source_id, chunk_size=650, overlap=100)
        enriched = [
            {
                **chunk,
                "source_id": source_id,
                "title": title,
                "publisher": publisher,
                "source_url": source_url,
                "language": language,
                "status": "active",
            }
            for chunk in chunks
        ]
        self.rag_store.upsert_chunks(enriched)
        return chunks

    def set_source_active(self, source_id: str, active: bool) -> None:
        """Toggle source active/inactive status across RAG and KG queries."""
        if active:
            self._inactive_source_ids.discard(source_id)
            self.rag_store.set_source_status(source_id, "active")
        else:
            self._inactive_source_ids.add(source_id)
            self.rag_store.set_source_status(source_id, "inactive")

    def delete_source(self, source_id: str) -> None:
        """Delete a source's chunks from ChromaDB and exclude it from KG results."""
        self._deleted_source_ids.add(source_id)
        self._inactive_source_ids.discard(source_id)
        self.rag_store.delete_source(source_id)

    def get_graph_payload(self, active_source_ids: set[str] | None = None) -> dict:
        """Return Diabetes Knowledge Graph nodes and edges filtered to active sources."""
        effective_ids = self._effective_active_ids(active_source_ids)
        return self.kg_store.get_graph_payload(active_source_ids=effective_ids)

    def retrieve(
        self,
        query: str,
        active_source_ids: set[str] | None = None,
        top_k: int = 4,
        min_score: float = 0.25,
    ) -> EvidenceBundle:
        """Retrieve relevant RAG citations (sanitized) and matching KG relations."""
        effective_ids = self._effective_active_ids(active_source_ids)
        raw_hits = self.rag_store.query(
            query,
            top_k=top_k,
            active_source_ids=effective_ids,
        )

        filtered_hits = [hit for hit in raw_hits if float(hit["score"]) >= min_score]
        citations: list[CitationItem] = []
        for idx, hit in enumerate(filtered_hits, start=1):
            clean_snippet = sanitize_untrusted_text(hit["text"])
            citations.append(
                CitationItem(
                    index=idx,
                    chunk_id=hit["chunk_id"],
                    source_id=hit["source_id"],
                    title=hit["title"],
                    publisher=hit["publisher"],
                    url=hit["url"],
                    snippet=clean_snippet,
                    score=float(hit["score"]),
                )
            )

        kg_relations, kg_source = self.kg_store.query_relations(
            query,
            active_source_ids=effective_ids,
            limit=8,
        )

        has_relevant_evidence = len(citations) > 0
        if not has_relevant_evidence:
            kg_relations = []

        return EvidenceBundle(
            citations=citations,
            kg_relations=kg_relations,
            kg_source=kg_source,
            has_relevant_evidence=has_relevant_evidence,
        )

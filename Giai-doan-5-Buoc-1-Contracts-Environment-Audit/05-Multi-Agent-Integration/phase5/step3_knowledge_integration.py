"""Phase 5 / Step 3: research-only Knowledge Agent retrieval adapter.

- Preselected queries; NO arbitrary user/clinical question is accepted by this prototype.
- Chroma collection metadata + Neo4j provenance; NO Chroma document text enters graph/state.
- FAIL CLOSED: allowed_to_answer is always False; no LLM, no approvals, no training.
- Only *read* methods are used, but use read-only database credentials in real setups.
- Graph here is a Knowledge Agent subgraph; Step 5 will handle cross-agent orchestration.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Protocol, TypedDict
from urllib.parse import urlparse

from .contracts import (
    CHROMA_COLLECTION, CHROMA_SNAPSHOT_SHA256, EvidenceMetadata,
)

EXPECTED_MODEL_ID = "intfloat/multilingual-e5-small"
EXPECTED_COUNTS: dict[str, int] = {
    "sources": 7, "chunks": 66, "chunk_links": 66, "orphans": 0,
    "candidates": 4, "technical_reviews": 4,
    "approved_relations": 0, "approved_claims": 0,
}
# Fixed benchmark requests, not arbitrary medical advice; never include answers or full text.
QUESTIONS = {
    "Q01": "Những yếu tố nào liên quan đến tiểu đường type 2?",
    "Q02": "HbA1c dùng để đánh giá tình trạng đường huyết như thế nào?",
    "Q03": "What are the common risk factors for type 2 diabetes?",
}
TOP_K = 3

NEO4J_AUDIT_CYPHER = """
CALL { MATCH (s:SourceDocument) RETURN count(s) AS sources }
CALL { MATCH (c:ChunkRef) RETURN count(c) AS chunks }
CALL { MATCH (:ChunkRef)-[p:PART_OF]->(:SourceDocument) RETURN count(p) AS chunk_links }
CALL { MATCH (c:ChunkRef) WHERE NOT (c)-[:PART_OF]->(:SourceDocument) RETURN count(c) AS orphans }
CALL { MATCH (r:RelationCandidate) RETURN count(r) AS candidates }
CALL { MATCH (r:TechnicalReview) RETURN count(r) AS technical_reviews }
CALL { MATCH (r:RelationCandidate {review_status:'approved'}) RETURN count(r) AS approved_relations }
CALL { MATCH (m:MedicalClaim {review_status:'approved'}) RETURN count(m) AS approved_claims }
RETURN sources, chunks, chunk_links, orphans, candidates, technical_reviews,
       approved_relations, approved_claims
"""

NEO4J_JOIN_CYPHER = """
UNWIND $ids AS wanted
OPTIONAL MATCH (c:ChunkRef {chunk_id:wanted})-[:PART_OF]->(s:SourceDocument)
RETURN wanted AS chunk_id,
       c.chunk_id AS found_chunk_id,
       c.source_id AS chunk_source_id,
       c.canonical_url AS chunk_url,
       c.source_snapshot_sha256 AS snapshot,
       c.metadata_sync_status AS sync_status,
       s.source_id AS source_id,
       s.url AS source_url
"""

class KnowledgeIntegrationFailure(Exception):
    """Sanitized fixed codes only; never echo secrets or source text."""
    ALLOWED = {
        "INVALID_QUERY_ID", "UNSAFE_NEO4J_URI", "INVALID_DATABASE",
        "CHROMA_SNAPSHOT_MISMATCH", "GRAPH_STATE_MISMATCH", "MISSING_DEPENDENCY",
        "BACKEND_UNAVAILABLE", "RETRIEVAL_SCHEMA_ERROR", "PROVENANCE_MISMATCH",
        "INTERNAL_ERROR",
    }

    def __init__(self, code: str):
        self.code = code if code in self.ALLOWED else "INTERNAL_ERROR"
        super().__init__(self.code)


def validate_neo4j_uri(uri: str) -> str:
    try:
        parsed = urlparse(uri)
        valid = (parsed.scheme == "neo4j+s" and bool(parsed.hostname)
                 and not parsed.username and not parsed.password and not parsed.path.strip("/")
                 and not parsed.query and not parsed.fragment and parsed.port is None)
    except ValueError:
        valid = False
    if not valid:
        raise KnowledgeIntegrationFailure("UNSAFE_NEO4J_URI")
    return uri


def validate_database(database: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,62}", database):
        raise KnowledgeIntegrationFailure("INVALID_DATABASE")
    return database


def validate_audit(counts: dict[str, Any]) -> bool:
    """Locked Phase 4 research checkpoint; any count change requires human re-audit."""
    if any(type(counts.get(k)) is not int or counts[k] != v for k, v in EXPECTED_COUNTS.items()):
        raise KnowledgeIntegrationFailure("GRAPH_STATE_MISMATCH")
    return True


class KnowledgeBackend(Protocol):
    def audit(self) -> dict[str, int]: ...
    def retrieve(self, query_id: str) -> list[dict[str, Any]]: ...
    def close(self) -> None: ...


class MockKnowledgeBackend:
    """Synthetic metadata only; NOT retrieval from the clinical knowledge base."""
    def __init__(self, tamper: str | None = None) -> None:
        self.tamper = tamper
        self.queries_run = 0

    def audit(self) -> dict[str, int]:
        result = dict(EXPECTED_COUNTS)
        if self.tamper == "audit":
            result["approved_claims"] = 1
        return result

    def retrieve(self, query_id: str) -> list[dict[str, Any]]:
        if query_id not in QUESTIONS:
            raise KnowledgeIntegrationFailure("INVALID_QUERY_ID")
        self.queries_run += 1
        items = []
        for n in range(1, TOP_K + 1):
            item = {
                "rank": n,
                "chunk_id": f"MOCK-{query_id}-{n:02d}",
                "source_id": "MOCK-SOURCE",
                "source_url": "https://example.invalid/mock-source",
                "provenance_match": True,
            }
            items.append(item)
        if self.tamper == "provenance":
            items[0]["provenance_match"] = False
        if self.tamper == "missing":
            items.pop()
        if self.tamper == "duplicate":
            items[1]["chunk_id"] = items[0]["chunk_id"]
        return items

    def close(self) -> None:
        pass


def project_evidence(raw_hits: list[dict[str, Any]]) -> list[EvidenceMetadata]:
    """Allowlisted metadata -> existing Pydantic contract, always blocked."""
    if len(raw_hits) != TOP_K:
        raise KnowledgeIntegrationFailure("RETRIEVAL_SCHEMA_ERROR")
    ids = [hit.get("chunk_id") for hit in raw_hits if isinstance(hit, dict)]
    if len(ids) != TOP_K or any(not isinstance(x, str) or not x for x in ids) or len(set(ids)) != TOP_K:
        raise KnowledgeIntegrationFailure("RETRIEVAL_SCHEMA_ERROR")
    output = []
    for expected_rank, hit in enumerate(raw_hits, start=1):
        if hit.get("rank") != expected_rank or hit.get("provenance_match") is not True:
            raise KnowledgeIntegrationFailure("PROVENANCE_MISMATCH")
        if (not isinstance(hit.get("source_id"), str) or not hit["source_id"]
                or not isinstance(hit.get("source_url"), str) or not hit["source_url"].startswith("https://")):
            raise KnowledgeIntegrationFailure("RETRIEVAL_SCHEMA_ERROR")
        try:
            output.append(EvidenceMetadata(
                chunk_id=hit["chunk_id"], source_id=hit["source_id"],
                source_url=hit["source_url"], provenance_match=True,
                review_status="unverified_research_only", allowed_to_answer=False,
            ))
        except ValueError:
            raise KnowledgeIntegrationFailure("RETRIEVAL_SCHEMA_ERROR") from None
    return output


class LiveKnowledgeBackend:
    """Chroma query + Neo4j execute_read only; no answer text returned."""
    def __init__(self, *, chroma_dir: Path, uri: str, username: str,
                 password: str, database: str) -> None:
        validate_neo4j_uri(uri)
        self.database = validate_database(database)
        if not chroma_dir.is_dir() or not (chroma_dir / "chroma.sqlite3").is_file():
            raise KnowledgeIntegrationFailure("BACKEND_UNAVAILABLE")
        try:
            import chromadb
            from neo4j import GraphDatabase
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise KnowledgeIntegrationFailure("MISSING_DEPENDENCY") from None
        self.driver = None
        try:
            chroma = chromadb.PersistentClient(path=str(chroma_dir))
            self.collection = chroma.get_collection(CHROMA_COLLECTION)
            metadata = self.collection.metadata or {}
            if (metadata.get("source_snapshot") != CHROMA_SNAPSHOT_SHA256
                    or metadata.get("model_id") != EXPECTED_MODEL_ID
                    or self.collection.count() != 66):
                raise KnowledgeIntegrationFailure("CHROMA_SNAPSHOT_MISMATCH")
            self.driver = GraphDatabase.driver(uri, auth=(username, password), connection_timeout=15)
            self.driver.verify_connectivity()
            # Model already downloaded during Stage 4. HF local cache is preferred;
            # installing missing weights requires separate user action and review.
            self.encoder = SentenceTransformer(EXPECTED_MODEL_ID, local_files_only=True)
        except KnowledgeIntegrationFailure:
            self.close()
            raise
        except Exception:
            self.close()
            raise KnowledgeIntegrationFailure("BACKEND_UNAVAILABLE") from None

    def _read(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        try:
            with self.driver.session(database=self.database) as session:
                return session.execute_read(lambda tx: tx.run(cypher, params or {}).data())
        except Exception:
            raise KnowledgeIntegrationFailure("BACKEND_UNAVAILABLE") from None

    def audit(self) -> dict[str, int]:
        rows = self._read(NEO4J_AUDIT_CYPHER)
        if len(rows) != 1:
            raise KnowledgeIntegrationFailure("GRAPH_STATE_MISMATCH")
        validate_audit(rows[0])
        return {k: rows[0][k] for k in EXPECTED_COUNTS}

    def retrieve(self, query_id: str) -> list[dict[str, Any]]:
        if query_id not in QUESTIONS:
            raise KnowledgeIntegrationFailure("INVALID_QUERY_ID")
        try:
            vector = self.encoder.encode(["query: " + QUESTIONS[query_id]], normalize_embeddings=True)[0]
            result = self.collection.query(query_embeddings=[vector.tolist()],
                                           n_results=TOP_K, include=["metadatas", "distances"])
            ids = result["ids"][0]
            metas = result["metadatas"][0]
        except Exception:
            raise KnowledgeIntegrationFailure("BACKEND_UNAVAILABLE") from None
        if len(ids) != TOP_K or len(metas) != TOP_K:
            raise KnowledgeIntegrationFailure("RETRIEVAL_SCHEMA_ERROR")
        joined = self._read(NEO4J_JOIN_CYPHER, {"ids": ids})
        # Duplicate rows are considered an invalid source graph, not silently overwritten.
        if len(joined) != TOP_K or len({x.get("chunk_id") for x in joined}) != TOP_K:
            raise KnowledgeIntegrationFailure("RETRIEVAL_SCHEMA_ERROR")
        by_id = {r["chunk_id"]: r for r in joined}
        rows = []
        for rank, (chunk_id, meta) in enumerate(zip(ids, metas), start=1):
            neo = by_id.get(chunk_id) or {}
            if not isinstance(meta, dict):
                raise KnowledgeIntegrationFailure("RETRIEVAL_SCHEMA_ERROR")
            matches = (
                neo.get("found_chunk_id") == chunk_id
                and neo.get("chunk_source_id") == meta.get("source_id")
                and neo.get("source_id") == meta.get("source_id")
                and neo.get("chunk_url") == meta.get("canonical_url")
                and neo.get("source_url") == meta.get("canonical_url")
                and neo.get("snapshot") == CHROMA_SNAPSHOT_SHA256
                and neo.get("sync_status") == "imported_unverified"
            )
            rows.append({
                "rank": rank, "chunk_id": chunk_id,
                "source_id": meta.get("source_id"),
                "source_url": neo.get("source_url"),
                "provenance_match": matches,
            })
        return rows

    def close(self) -> None:
        if getattr(self, "driver", None) is not None:
            self.driver.close()


class KnowledgeResearchState(TypedDict):
    query_id: str
    knowledge_gate: str
    llm_called: bool
    evidence_metadata: list[dict[str, Any]]
    errors: list[str]
    final_result: dict[str, Any]


def make_step3_knowledge_graph(backend: KnowledgeBackend):
    """3-node LangGraph subgraph: Orchestrator -> Knowledge -> blocked Consultation.

    This is NOT yet the unified 5-agent orchestrator (planned Step 5).
    """
    from langgraph.graph import START, END, StateGraph

    def orchestrator_agent(state: KnowledgeResearchState) -> dict[str, Any]:
        if state.get("query_id") not in QUESTIONS:
            return {"errors": ["INVALID_QUERY_ID"], "knowledge_gate": "BLOCKED_RESEARCH_ONLY"}
        return {"knowledge_gate": "BLOCKED_RESEARCH_ONLY", "llm_called": False}

    def knowledge_agent(state: KnowledgeResearchState) -> dict[str, Any]:
        if state.get("errors"):
            return {"evidence_metadata": []}
        try:
            evidence = project_evidence(backend.retrieve(state["query_id"]))
            return {"evidence_metadata": [e.model_dump() for e in evidence]}
        except KnowledgeIntegrationFailure as exc:
            return {"evidence_metadata": [], "errors": [exc.code]}
        except Exception:
            return {"evidence_metadata": [], "errors": ["INTERNAL_ERROR"]}

    def consultation_agent_blocked(state: KnowledgeResearchState) -> dict[str, Any]:
        evidence = state.get("evidence_metadata", [])
        errors = state.get("errors", [])
        result = {
            "query_id": state.get("query_id"),
            "status": "blocked_research_only" if not errors else "error_blocked",
            "knowledge_gate": "BLOCKED_RESEARCH_ONLY",
            "llm_called": False,
            "hits": evidence,
            "error_codes": errors,
            "answer_generated": False,
        }
        return {"final_result": result, "knowledge_gate": "BLOCKED_RESEARCH_ONLY", "llm_called": False}

    builder = StateGraph(KnowledgeResearchState)
    builder.add_node("orchestrator_agent", orchestrator_agent)
    builder.add_node("knowledge_agent", knowledge_agent)
    builder.add_node("consultation_agent_blocked", consultation_agent_blocked)
    builder.add_edge(START, "orchestrator_agent")
    builder.add_edge("orchestrator_agent", "knowledge_agent")
    builder.add_edge("knowledge_agent", "consultation_agent_blocked")
    builder.add_edge("consultation_agent_blocked", END)
    return builder.compile()


def execute_knowledge_query(backend: KnowledgeBackend, query_id: str) -> dict[str, Any]:
    """Server-owned gate; no caller-supplied raw question or gate accepted."""
    if query_id not in QUESTIONS:
        raise KnowledgeIntegrationFailure("INVALID_QUERY_ID")
    initial: KnowledgeResearchState = {
        "query_id": query_id, "knowledge_gate": "BLOCKED_RESEARCH_ONLY",
        "llm_called": False, "evidence_metadata": [], "errors": [], "final_result": {},
    }
    result = make_step3_knowledge_graph(backend).invoke(initial)
    final = result["final_result"]
    if (final.get("knowledge_gate") != "BLOCKED_RESEARCH_ONLY"
            or final.get("llm_called") is not False or final.get("answer_generated") is not False
            or any(hit.get("allowed_to_answer") is not False for hit in final.get("hits", []))):
        raise KnowledgeIntegrationFailure("INTERNAL_ERROR")
    return final

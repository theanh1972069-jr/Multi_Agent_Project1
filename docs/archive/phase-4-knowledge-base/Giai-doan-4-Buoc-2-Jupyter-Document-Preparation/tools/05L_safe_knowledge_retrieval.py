#!/usr/bin/env python3
"""Phase 4 / Step 5L: research-only ChromaDB + Neo4j read-only evidence gate.

Never generates medical answers, writes to databases, approves claims, or calls an LLM.
No chunks' full text is printed or saved. Run by the user on their own machine.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
from datetime import datetime, timezone
from pathlib import Path

COLLECTION = "diabetes_kb_step3_e5small_v1"
SNAPSHOT = "cc064ec7187192c999418051cb2125a0510412843f8d0908e3d6842e4a71c7cd"
MODEL_ID = "intfloat/multilingual-e5-small"
DEFAULT_QUESTIONS = [
    "Những yếu tố nào liên quan đến tiểu đường type 2?",
    "HbA1c dùng để đánh giá tình trạng đường huyết như thế nào?",
    "What are the common risk factors for type 2 diabetes?",
]

AUDIT_CYPHER = """
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

JOIN_CYPHER = """
UNWIND $ids AS wanted
OPTIONAL MATCH (c:ChunkRef {chunk_id:wanted})-[:PART_OF]->(s:SourceDocument)
OPTIONAL MATCH (m:MedicalClaim)-[:HAS_EVIDENCE_CANDIDATE]->(c)
OPTIONAL MATCH (r:RelationCandidate)-[:SUPPORTED_BY_CLAIM]->(m)
WITH wanted, c, s, m, r,
     EXISTS {
        MATCH (r)-[:HAS_INDEPENDENT_MEDICAL_REVIEW]->(mr:IndependentMedicalReview)
        WHERE mr.decision = 'approved'
     } AS independent_medical_ok,
     EXISTS {
        MATCH (s)-[:HAS_INDEPENDENT_RIGHTS_REVIEW]->(rr:IndependentRightsReview)
        WHERE rr.decision = 'approved'
     } AS independent_rights_ok
RETURN wanted AS chunk_id,
       c.chunk_id AS found_chunk_id,
       c.source_id AS chunk_source_id,
       c.canonical_url AS chunk_url,
       c.source_snapshot_sha256 AS snapshot,
       c.metadata_sync_status AS sync_status,
       s.source_id AS source_id,
       s.url AS source_url,
       collect(DISTINCT CASE WHEN r IS NOT NULL THEN {
          relation_id: r.relation_id,
          claim_id: m.claim_id,
          relation_review: r.review_status,
          relation_usage: r.usage_status,
          claim_review: m.review_status,
          claim_usage: m.usage_status,
          independent_medical_ok: independent_medical_ok,
          independent_rights_ok: independent_rights_ok
       } ELSE null END) AS candidate_links
"""


def reviewed_evidence_allowed(link: dict, provenance_ok: bool) -> bool:
    """Conservative metadata eligibility check; NOT a clinical approval procedure."""
    return bool(provenance_ok and
                link.get("relation_review") == "approved" and
                link.get("relation_usage") == "allowed_for_answering" and
                link.get("claim_review") == "approved" and
                link.get("claim_usage") == "allowed_for_answering" and
                link.get("independent_medical_ok") is True and
                link.get("independent_rights_ok") is True)


def run_self_tests() -> None:
    base = dict(relation_review="draft_unverified",
                relation_usage="blocked_for_answering",
                claim_review="draft_unverified",
                claim_usage="blocked_for_answering",
                independent_medical_ok=False,
                independent_rights_ok=False)
    assert not reviewed_evidence_allowed(base, True)
    assert not reviewed_evidence_allowed({}, True)
    reviewed = dict(base, relation_review="approved", relation_usage="allowed_for_answering",
                    claim_review="approved", claim_usage="allowed_for_answering",
                    independent_medical_ok=True, independent_rights_ok=True)
    assert not reviewed_evidence_allowed(reviewed, False)
    assert reviewed_evidence_allowed(reviewed, True)
    for field in reviewed:
        altered = dict(reviewed)
        altered[field] = False if field.startswith("independent_") else "pending"
        assert not reviewed_evidence_allowed(altered, True), field
    print("SELF-TEST: PASS — 9 blocked cases + one all-conditions check; no DB connection")


def read_neo(driver, database: str, cypher: str, params: dict | None = None) -> list[dict]:
    with driver.session(database=database) as session:
        return session.execute_read(lambda tx: tx.run(cypher, params or {}).data())


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only, research-only retrieval evidence gate")
    parser.add_argument("--self-test", action="store_true", help="Run purely local policy tests, no dependencies")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--chroma-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--query", action="append", help="Optional question; can repeat")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()
    if args.self_test:
        run_self_tests()
        return
    if not (1 <= args.top_k <= 10):
        parser.error("--top-k must be between 1 and 10")

    root = args.project_root.resolve()
    chroma_dir = (args.chroma_dir or root / "data/vector_store/chroma_step3").resolve()
    output_dir = (args.output_dir or root / "data/outputs/safe_retrieval_step5l").resolve()
    if not chroma_dir.is_dir():
        raise SystemExit(f"STOP: local ChromaDB directory missing: {chroma_dir}")

    uri = os.getenv("NEO4J_URI", "").strip()
    username = os.getenv("NEO4J_USERNAME", "neo4j").strip()
    database = os.getenv("NEO4J_DATABASE", "neo4j").strip()
    if not uri.startswith("neo4j+s://"):
        raise SystemExit("STOP: set NEO4J_URI to the Aura Bolt URI neo4j+s://..., not console.neo4j.io")
    password = os.getenv("NEO4J_PASSWORD") or getpass.getpass("Neo4j password (hidden): ")
    if not password:
        raise SystemExit("STOP: Neo4j password not supplied")

    try:
        import chromadb
        from neo4j import GraphDatabase
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit("Missing dependency: python -m pip install chromadb neo4j sentence-transformers") from exc

    client = chromadb.PersistentClient(path=str(chroma_dir))
    col = client.get_collection(COLLECTION)
    meta = col.metadata or {}
    if meta.get("source_snapshot") != SNAPSHOT or meta.get("model_id") != MODEL_ID:
        raise SystemExit("STOP: unexpected collection snapshot or embedding model; do not query the wrong index")
    if col.count() != 66:
        raise SystemExit(f"STOP: expected 66 indexed chunks, got {col.count()}")

    questions = args.query or DEFAULT_QUESTIONS
    output = []
    with GraphDatabase.driver(uri, auth=(username, password), connection_timeout=15) as driver:
        driver.verify_connectivity()
        preflight = read_neo(driver, database, AUDIT_CYPHER)
        if len(preflight) != 1:
            raise SystemExit("STOP: unexpected Neo4j audit result")
        counts = preflight[0]
        expected = {"sources": 7, "chunks": 66, "chunk_links": 66, "orphans": 0,
                    "candidates": 4, "technical_reviews": 4,
                    "approved_relations": 0, "approved_claims": 0}
        if any(counts.get(key) != value for key, value in expected.items()):
            raise SystemExit(f"STOP: unexpected Neo4j graph state: {counts}; preserve the current research checkpoint")

        encoder = SentenceTransformer(MODEL_ID)
        for i, question in enumerate(questions, start=1):
            vector = encoder.encode(["query: " + question], normalize_embeddings=True)[0]
            result = col.query(query_embeddings=[vector.tolist()], n_results=args.top_k,
                               include=["metadatas", "distances"])
            ids = result["ids"][0]
            metas = result["metadatas"][0]
            dists = result["distances"][0]
            rows = read_neo(driver, database, JOIN_CYPHER, {"ids": ids})
            by_id = {r["chunk_id"]: r for r in rows}
            hits = []
            for rank, (chunk_id, cm, dist) in enumerate(zip(ids, metas, dists), start=1):
                gm = by_id.get(chunk_id, {})
                provenance_ok = all([
                    gm.get("found_chunk_id") == chunk_id,
                    gm.get("chunk_source_id") == cm.get("source_id"),
                    gm.get("source_id") == cm.get("source_id"),
                    gm.get("chunk_url") == cm.get("canonical_url"),
                    gm.get("source_url") == cm.get("canonical_url"),
                    gm.get("snapshot") == SNAPSHOT,
                    gm.get("sync_status") == "imported_unverified",
                ])
                links = gm.get("candidate_links") or []
                eligible = [x for x in links if reviewed_evidence_allowed(x, provenance_ok)]
                hits.append({
                    "rank": rank, "chunk_id": chunk_id,
                    "source_id": cm.get("source_id"), "section": cm.get("section"),
                    "source_url": gm.get("source_url"), "cosine_distance": float(dist),
                    "graph_provenance_match": provenance_ok,
                    "candidate_claim_links": len(links),
                    "eligible_reviewed_links": len(eligible),
                    "allowed_to_answer": False,  # hard-disable answers at research prototype stage
                })
            output.append({"question_id": f"Q{i:02d}", "question": question, "hits": hits,
                           "answer_gate": "BLOCKED_RESEARCH_ONLY"})

    audit = {
        "experiment": "EXP-RAG-STEP5L-001",
        "stage": "phase4_step5l_safe_retrieval_prototype",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "technical_retrieval_checked_answers_disabled",
        "collection": COLLECTION,
        "source_snapshot_sha256": SNAPSHOT,
        "neo4j_audit": counts,
        "queries": output,
        "joined_hits": sum(len(x["hits"]) for x in output),
        "provenance_matches": sum(int(h["graph_provenance_match"]) for q in output for h in q["hits"]),
        "answers_generated": 0, "llm_called": False,
        "medical_claims_approved": False,
        "chroma_modified": False, "neo4j_modified": False, "model_retrained": False,
        "caution": "No clinical or copyright verification; this is not an authorization boundary for production.",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "step5l_safe_retrieval_report.json"
    report_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print("===== GIAI ĐOẠN 4 — BƯỚC 5L: SAFE RETRIEVAL =====")
    print(f"Neo4j: {counts['chunks']} ChunkRef | {counts['candidates']} RelationCandidate | {counts['approved_claims']} approved claims")
    print("Joined hits:", audit["joined_hits"], "| provenance matches:", audit["provenance_matches"])
    print("Answer gate: BLOCKED_RESEARCH_ONLY | LLM: NO | DB writes: NO")
    print("Saved report:", report_path)
    print("===== GỬI OUTPUT VÀ JSON CHO TÔI =====")


if __name__ == "__main__":
    main()

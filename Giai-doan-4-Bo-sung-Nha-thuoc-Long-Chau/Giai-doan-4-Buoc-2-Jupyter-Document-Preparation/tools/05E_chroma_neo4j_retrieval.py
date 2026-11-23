#!/usr/bin/env python3
"""Step 5E — local read-only ChromaDB -> Neo4j Aura provenance retrieval.

Run only on the user's machine with the previously created ChromaDB and Neo4j Aura.
Never writes ChromaDB/Neo4j, calls an LLM, tunes a model, or changes a medical claim.
The result is a *research retrieval diagnostic*, NOT medical evidence approval.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_COLLECTION = "diabetes_kb_step3_e5small_v1"
EXPECTED_SNAPSHOT = "cc064ec7187192c999418051cb2125a0510412843f8d0908e3d6842e4a71c7cd"
EXPECTED_EMBEDDING = "intfloat/multilingual-e5-small"
EXPECTED_COUNTS = {
    "CDC-T2D-001": 4,
    "CDC-RISK-002": 3,
    "NIDDK-DIAG-003": 19,
    "NIDDK-T2D-004": 11,
    "WHO-DIAB-005": 5,
    "LC-HBA1C-006": 11,
    "LC-STAGES-007": 13,
}
DEFAULT_QUERIES = [
    "Những yếu tố nào liên quan đến tiểu đường type 2?",
    "HbA1c dùng để đánh giá tình trạng đường huyết như thế nào?",
    "What are the common risk factors for type 2 diabetes?",
]

GRAPH_COUNTS = """
CALL { MATCH (s:SourceDocument) RETURN count(s) AS source_documents }
CALL { MATCH (t:Topic) RETURN count(t) AS topics }
CALL { MATCH ()-[r:COVERS_TOPIC]->() RETURN count(r) AS topic_links }
CALL { MATCH (c:ChunkRef) RETURN count(c) AS chunk_refs }
CALL { MATCH (:ChunkRef)-[r:PART_OF]->(:SourceDocument) RETURN count(r) AS chunk_links }
CALL { MATCH (c:ChunkRef) WHERE NOT (c)-[:PART_OF]->(:SourceDocument) RETURN count(c) AS orphans }
CALL { MATCH (c:MedicalClaim) WHERE c.review_status = 'approved' RETURN count(c) AS approved_claims }
RETURN source_documents, topics, topic_links, chunk_refs, chunk_links, orphans, approved_claims
"""

GRAPH_BY_SOURCE = """
MATCH (c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
RETURN s.source_id AS source_id, count(DISTINCT c) AS chunk_count
ORDER BY source_id
"""

GRAPH_METADATA_FOR_IDS = """
UNWIND $ids AS wanted
OPTIONAL MATCH (c:ChunkRef {chunk_id: wanted})
OPTIONAL MATCH (c)-[:PART_OF]->(s:SourceDocument)
OPTIONAL MATCH (s)-[:COVERS_TOPIC]->(t:Topic)
RETURN wanted AS chunk_id,
       c.chunk_id AS found_chunk_id,
       c.source_id AS chunk_source_id,
       c.canonical_url AS chunk_url,
       c.source_snapshot_sha256 AS snapshot,
       c.metadata_sync_status AS metadata_sync_status,
       s.source_id AS source_id,
       s.title AS title,
       s.url AS source_url,
       s.rights_status AS rights_status,
       s.medical_review_status AS medical_review_status,
       collect(DISTINCT t.name) AS topics
"""


def fetch_read(driver, cypher: str, *, database: str, params: dict | None = None) -> list[dict]:
    """Explicit read transaction — none of this script's queries writes data."""
    with driver.session(database=database) as session:
        return session.execute_read(lambda tx: tx.run(cypher, params or {}).data())


def validate_counts(graph_counts: dict, chroma_count: int, graph_sources: dict) -> None:
    expected = {
        "source_documents": 7,
        "topics": 6,
        "topic_links": 7,
        "chunk_refs": 66,
        "chunk_links": 66,
        "orphans": 0,
        "approved_claims": 0,
    }
    for key, target in expected.items():
        found = graph_counts.get(key)
        if found != target:
            raise RuntimeError(f"STOP: Neo4j {key}={found}, expected {target}; verify 5D before continuing")
    if chroma_count != 66 or graph_sources != EXPECTED_COUNTS:
        raise RuntimeError(f"STOP: Chroma count={chroma_count} or Neo4j counts-by-source differ from Step 3: {graph_sources}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only Chroma -> Neo4j graph provenance check")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Root containing data/ and registry/")
    parser.add_argument("--chroma-dir", type=Path, help="Override path to existing ChromaDB directory")
    parser.add_argument("--output-dir", type=Path, help="Output directory for local JSON report")
    parser.add_argument("--top-k", type=int, default=3, help="Number of vector hits per question (1..10)")
    parser.add_argument("--query", action="append", help="Repeat to specify one or more questions; default: 3 known sample questions")
    args = parser.parse_args()
    if not 1 <= args.top_k <= 10:
        parser.error("--top-k must be between 1 and 10")

    root = args.project_root.resolve()
    chroma_dir = (args.chroma_dir or root / "data/vector_store/chroma_step3").resolve()
    out_dir = (args.output_dir or root / "data/outputs/graph_retrieval_step5e").resolve()
    if not chroma_dir.is_dir():
        raise SystemExit(f"STOP: ChromaDB directory not found: {chroma_dir}")

    uri = os.getenv("NEO4J_URI", "").strip()
    username = os.getenv("NEO4J_USERNAME", "neo4j").strip()
    database = os.getenv("NEO4J_DATABASE", "neo4j").strip()
    if not uri.startswith("neo4j+s://"):
        raise SystemExit("STOP: Set NEO4J_URI to your Aura neo4j+s://... URI (not the console webpage)")
    password = os.getenv("NEO4J_PASSWORD") or getpass.getpass("Neo4j Aura password (hidden): ")
    if not password:
        raise SystemExit("STOP: No Neo4j password provided")

    try:
        import chromadb
        from neo4j import GraphDatabase
        from sentence_transformers import SentenceTransformer
    except ImportError as err:
        raise SystemExit("Missing package. Install: python -m pip install chromadb neo4j sentence-transformers") from err

    client = chromadb.PersistentClient(path=str(chroma_dir))
    col = client.get_collection(EXPECTED_COLLECTION)
    metadata = col.metadata or {}
    if metadata.get("source_snapshot") != EXPECTED_SNAPSHOT:
        raise SystemExit("STOP: Chroma snapshot differs from Step 3 report")
    if metadata.get("model_id") != EXPECTED_EMBEDDING:
        raise SystemExit("STOP: Chroma embedding model differs from expected multilingual-e5-small")
    chroma_count = col.count()
    if chroma_count != 66:
        raise SystemExit(f"STOP: expected 66 Chroma records, got {chroma_count}")

    print("===== STEP 5E — PREFLIGHT, READ ONLY =====")
    print("Chroma collection:", EXPECTED_COLLECTION, "| records:", chroma_count)
    print("Neo4j URI: configured (hidden) | database:", database)

    # Connect to Aura only after local Chroma snapshot checks succeed.
    with GraphDatabase.driver(uri, auth=(username, password), connection_timeout=15) as driver:
        driver.verify_connectivity()
        totals = fetch_read(driver, GRAPH_COUNTS, database=database)
        if len(totals) != 1:
            raise RuntimeError("STOP: expected one Neo4j preflight row")
        counts = totals[0]
        per_source_rows = fetch_read(driver, GRAPH_BY_SOURCE, database=database)
        by_source = {r["source_id"]: r["chunk_count"] for r in per_source_rows}
        validate_counts(counts, chroma_count, by_source)
        print("Neo4j preflight: PASS | ChunkRef=66 | PART_OF=66 | sources=7 | orphan=0")

        # Use the SAME multilingual E5 model as Step 3; never call Chroma's default embedding.
        embedding_model = SentenceTransformer(EXPECTED_EMBEDDING)
        queries = args.query if args.query else DEFAULT_QUERIES
        output_queries = []
        for i, question in enumerate(queries, 1):
            q_vector = embedding_model.encode(["query: " + question], normalize_embeddings=True)[0]
            results = col.query(
                query_embeddings=[q_vector.tolist()],
                n_results=args.top_k,
                include=["metadatas", "distances"],
            )
            ids = results["ids"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]
            graph_rows = fetch_read(driver, GRAPH_METADATA_FOR_IDS, database=database, params={"ids": ids})
            by_id = {r["chunk_id"]: r for r in graph_rows}
            matched_hits = []
            print(f"Q{i:02d}: {question}")
            for rank, (chunk_id, cm, dist) in enumerate(zip(ids, metas, distances), 1):
                gm = by_id.get(chunk_id, {})
                valid = all([
                    gm.get("found_chunk_id") == chunk_id,
                    gm.get("chunk_source_id") == cm.get("source_id"),
                    gm.get("source_id") == cm.get("source_id"),
                    gm.get("chunk_url") == cm.get("canonical_url"),
                    gm.get("source_url") == cm.get("canonical_url"),
                    gm.get("snapshot") == EXPECTED_SNAPSHOT,
                    gm.get("metadata_sync_status") == "imported_unverified",
                ])
                hit = {
                    "rank": rank,
                    "chunk_id": chunk_id,
                    "source_id": cm.get("source_id"),
                    "cosine_distance": float(dist),
                    "section": cm.get("section", ""),
                    "source_title": gm.get("title"),
                    "url": gm.get("source_url"),
                    "topics": gm.get("topics", []),
                    "graph_provenance_match": bool(valid),
                    "rights_status": gm.get("rights_status"),
                    "medical_review_status": gm.get("medical_review_status"),
                    "eligible_for_medical_answer": False,
                }
                matched_hits.append(hit)
                status = "OK" if valid else "MISMATCH"
                print(f"  {rank}. {chunk_id} [{status}] distance={dist:.4f}; source={hit['source_id']}")
            print(f"  Graph provenance matches: {sum(h['graph_provenance_match'] for h in matched_hits)}/{len(matched_hits)}")
            output_queries.append({"question_id": f"Q{i:02d}", "question": question, "hits": matched_hits})

    joined = [h for q in output_queries for h in q["hits"]]
    all_match = bool(joined) and all(h["graph_provenance_match"] for h in joined)
    report = {
        "experiment": "EXP-GRAPH-RETRIEVAL-STEP5E-001",
        "stage": "phase4_step5e_chroma_neo4j_provenance_retrieval",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "technical_join_pass" if all_match else "metadata_mismatch_needs_review",
        "collection": EXPECTED_COLLECTION,
        "source_snapshot_sha256": EXPECTED_SNAPSHOT,
        "embedding_model": EXPECTED_EMBEDDING,
        "chroma_records": chroma_count,
        "neo4j_counts": counts,
        "neo4j_chunks_by_source": by_source,
        "queries": output_queries,
        "top_k": args.top_k,
        "joined_hits": len(joined),
        "provenance_matches": sum(h["graph_provenance_match"] for h in joined),
        "no_medical_claims_approved": counts["approved_claims"] == 0,
        "evidence_gate_ready_for_llm": False,
        "independent_rights_or_clinical_review": False,
        "llm_called": False,
        "neo4j_modified": False,
        "chroma_modified": False,
        "model_retrained": False,
        "notes": "Metadata joins only. Topics come from document titles. Not medical claim verification or GraphRAG answer generation.",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "step5e_graph_retrieval_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("===== GIAI ĐOẠN 4 – BƯỚC 5E: GRAPH RETRIEVAL =====")
    print("Graph join matches:", report["provenance_matches"], "/", report["joined_hits"])
    print("Status:", report["status"])
    print("Saved report:", report_path)
    print("NEO4J WRITE: NO | CHROMA WRITE: NO | LLM: NO | MODEL TRAINING: NO")
    print("===== GỬI OUTPUT VÀ JSON CHO TÔI =====")


if __name__ == "__main__":
    main()

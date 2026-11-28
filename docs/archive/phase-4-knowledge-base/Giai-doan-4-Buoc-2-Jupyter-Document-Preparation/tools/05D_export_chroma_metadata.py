#!/usr/bin/env python3
"""Export existing ChromaDB metadata as a single reviewable Cypher import.

RUNS LOCALLY: does not connect to Neo4j, does not modify ChromaDB,
does not read or export document text or vector embeddings.

Expected input: the exact step-3 ChromaDB collection created by the user.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_COLLECTION = "diabetes_kb_step3_e5small_v1"
EXPECTED_SNAPSHOT = "cc064ec7187192c999418051cb2125a0510412843f8d0908e3d6842e4a71c7cd"
EXPECTED_MODEL = "intfloat/multilingual-e5-small"
EXPECTED_COUNTS = {
    "CDC-T2D-001": 4,
    "CDC-RISK-002": 3,
    "NIDDK-DIAG-003": 19,
    "NIDDK-T2D-004": 11,
    "WHO-DIAB-005": 5,
    "LC-HBA1C-006": 11,
    "LC-STAGES-007": 13,
}
REQUIRED = (
    "source_id", "canonical_url", "section", "document_version",
    "chunk_sha256", "document_sha256", "content_origin", "parent_chunk_id",
)
FIELDS = (
    "chunk_id", "source_id", "canonical_url", "section", "document_version",
    "chunk_sha256", "document_sha256", "content_origin", "parent_chunk_id", "language",
)


def cypher_value(value: str) -> str:
    """JSON double quoted strings are accepted as Cypher string literals."""
    return json.dumps(value, ensure_ascii=False)


def render_cypher(rows: list[dict[str, str]]) -> str:
    literal_rows = []
    for row in rows:
        inside = ", ".join(f"{name}: {cypher_value(row[name])}" for name in FIELDS)
        literal_rows.append("  {" + inside + "}")
    return "\n".join([
        "// STEP 5D: META ONLY — KHONG CO TEXT/VECTOR/CREDENTIALS.",
        "// Chay SAU KHI kiem tra 7 SourceDocument va unique constraint ChunkRef.",
        "// Giữ 0 MedicalClaim approved; quyền sử dụng vẫn pending independent review.",
        "UNWIND [",
        ",\n".join(literal_rows),
        "] AS row",
        "MATCH (s:SourceDocument {source_id: row.source_id})",
        "MERGE (c:ChunkRef {chunk_id: row.chunk_id})",
        "ON CREATE SET c.created_at = datetime(),",
        "              c.medical_review_status = 'pending',",
        "              c.rights_review_status = 'pending_independent_check',",
        "              c.research_only = true",
        "SET c.source_id = row.source_id,",
        "    c.canonical_url = row.canonical_url,",
        "    c.section = row.section,",
        "    c.document_version = row.document_version,",
        "    c.chunk_sha256 = row.chunk_sha256,",
        "    c.document_sha256 = row.document_sha256,",
        "    c.content_origin = row.content_origin,",
        "    c.parent_chunk_id = row.parent_chunk_id,",
        "    c.language = row.language,",
        f"    c.collection = '{EXPECTED_COLLECTION}',",
        f"    c.source_snapshot_sha256 = '{EXPECTED_SNAPSHOT}',",
        "    c.metadata_sync_status = 'imported_unverified'",
        "MERGE (c)-[:PART_OF]->(s)",
        "RETURN count(DISTINCT c) AS processed_chunks,",
        "       count(DISTINCT s) AS linked_sources;",
        "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Cypher import from local Chroma metadata")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Folder containing data/ and registry/")
    parser.add_argument("--chroma-dir", type=Path, help="Optional override for data/vector_store/chroma_step3")
    parser.add_argument("--out-dir", type=Path, help="Optional output folder")
    args = parser.parse_args()
    project = args.project_root.resolve()
    chroma_dir = (args.chroma_dir or project / "data/vector_store/chroma_step3").resolve()
    out_dir = (args.out_dir or project / "data/outputs/neo4j_sync_step5d").resolve()
    registry_path = project / "registry/source_registry.csv"
    if not chroma_dir.exists():
        raise SystemExit(f"Khong tim thay ChromaDB: {chroma_dir}")
    if not registry_path.is_file():
        raise SystemExit(f"Khong tim thay source registry: {registry_path}")
    try:
        import chromadb
    except ImportError as e:
        raise SystemExit("Chua cai chromadb. Chay: python -m pip install chromadb") from e

    with registry_path.open("r", encoding="utf-8-sig", newline="") as fp:
        reg_rows = list(csv.DictReader(fp))
    registry = {r["source_id"]: r for r in reg_rows}
    if set(registry) != set(EXPECTED_COUNTS) or len(reg_rows) != 7:
        raise SystemExit("Registry khong khop 7 source_id da xac nhan; DUNG DE KIEM TRA")

    client = chromadb.PersistentClient(path=str(chroma_dir))
    col = client.get_collection(EXPECTED_COLLECTION)
    meta = col.metadata or {}
    if meta.get("source_snapshot") != EXPECTED_SNAPSHOT:
        raise SystemExit(f"STOP: source_snapshot khac report Step 3: {meta.get('source_snapshot')}")
    if meta.get("model_id") != EXPECTED_MODEL:
        raise SystemExit(f"STOP: embedding model khac: {meta.get('model_id')}")
    if col.count() != 66:
        raise SystemExit(f"STOP: Chroma co {col.count()} records, khong phai 66")
    stored = col.get(include=["metadatas"])
    ids, metadatas = stored["ids"], stored["metadatas"]
    if len(ids) != 66 or len(set(ids)) != 66 or len(metadatas) != len(ids):
        raise SystemExit("STOP: IDs khong du / bi trung / metadata thieu")

    rows = []
    for chunk_id, m in zip(ids, metadatas):
        if not isinstance(m, dict):
            raise SystemExit(f"STOP: metadata khong hop le: {chunk_id}")
        for key in REQUIRED:
            if not isinstance(m.get(key), str) or not m[key].strip():
                raise SystemExit(f"STOP: {chunk_id} thieu metadata {key}")
        sid = m["source_id"]
        if sid not in registry or not chunk_id.startswith(sid + "__"):
            raise SystemExit(f"STOP: ID / source_id khong khop: {chunk_id}")
        if m["canonical_url"] != registry[sid]["canonical_url"]:
            raise SystemExit(f"STOP: URL khong khop registry: {sid}")
        if m["document_version"] != registry[sid]["document_version"]:
            raise SystemExit(f"STOP: document_version khac registry: {sid}")
        if any(c not in "0123456789abcdef" for c in m["chunk_sha256"].lower()) or len(m["chunk_sha256"]) != 64:
            raise SystemExit(f"STOP: chunk_sha256 khong hop le: {chunk_id}")
        rows.append({
            "chunk_id": chunk_id,
            "source_id": sid,
            "canonical_url": m["canonical_url"],
            "section": m["section"],
            "document_version": m["document_version"],
            "chunk_sha256": m["chunk_sha256"],
            "document_sha256": m["document_sha256"],
            "content_origin": m["content_origin"],
            "parent_chunk_id": m["parent_chunk_id"],
            "language": str(m.get("language", "")),
        })
    counts = dict(Counter(row["source_id"] for row in rows))
    if counts != EXPECTED_COUNTS:
        raise SystemExit(f"STOP: so chunks theo source khac Step 3: {counts}")
    rows.sort(key=lambda r: (r["source_id"], r["chunk_id"]))
    cypher = render_cypher(rows)

    out_dir.mkdir(parents=True, exist_ok=True)
    cypher_path = out_dir / "05D_import_66_chunks.cypher"
    manifest_path = out_dir / "05D_export_manifest.json"
    cypher_path.write_text(cypher, encoding="utf-8")
    manifest = {
        "stage": "phase4_step5d_metadata_export",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "prepared_not_imported",
        "chroma_collection": EXPECTED_COLLECTION,
        "source_snapshot_sha256": EXPECTED_SNAPSHOT,
        "chroma_record_count": 66,
        "counts_by_source": EXPECTED_COUNTS,
        "cypher_sha256": hashlib.sha256(cypher.encode("utf-8")).hexdigest(),
        "cypher_file": str(cypher_path),
        "contains_document_text": False,
        "contains_embeddings": False,
        "neo4j_connection_attempted": False,
        "chroma_modified": False,
        "medical_claims_approved": 0,
        "rights_independently_verified": False,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("===== GIAI DOAN 4 - BUOC 5D: EXPORT METADATA =====")
    print("Collection:", EXPECTED_COLLECTION)
    print("Source snapshot:", EXPECTED_SNAPSHOT)
    print("Prepared ChunkRefs:", len(rows), "| Sources:", len(counts))
    print("Cypher:", cypher_path)
    print("Manifest:", manifest_path)
    print("Neo4j write: NO | Chroma modified: NO | LLM: NO | ML training: NO")
    print("===== GUI OUTPUT VA MANIFEST CHO TOI =====")


if __name__ == "__main__":
    main()

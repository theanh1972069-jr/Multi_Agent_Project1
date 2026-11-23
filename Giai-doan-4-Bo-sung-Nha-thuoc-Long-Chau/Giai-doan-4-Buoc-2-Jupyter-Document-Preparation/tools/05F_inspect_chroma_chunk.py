#!/usr/bin/env python3
"""Read-only local inspection of one ChromaDB chunk for manual evidence review.

Does not create clinical facts, alter indexes, call an LLM, or contact Neo4j.
Only prints content on the user's own terminal. Do not post licensed text publicly.
"""
from __future__ import annotations
import argparse
from pathlib import Path

COLLECTION = "diabetes_kb_step3_e5small_v1"
EXPECTED_SNAPSHOT = "cc064ec7187192c999418051cb2125a0510412843f8d0908e3d6842e4a71c7cd"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project-root", type=Path, default=Path.cwd())
    p.add_argument("--chroma-dir", type=Path)
    p.add_argument("--chunk-id", required=True)
    args = p.parse_args()
    root = args.project_root.resolve()
    chroma_dir = (args.chroma_dir or root / "data/vector_store/chroma_step3").resolve()
    if not chroma_dir.is_dir():
        raise SystemExit(f"Không tìm thấy ChromaDB: {chroma_dir}")
    try:
        import chromadb
    except ImportError as e:
        raise SystemExit("Cài đặt: python -m pip install chromadb") from e
    col = chromadb.PersistentClient(path=str(chroma_dir)).get_collection(COLLECTION)
    meta = col.metadata or {}
    if meta.get("source_snapshot") != EXPECTED_SNAPSHOT or col.count() != 66:
        raise SystemExit("STOP: Snapshot hoặc số chunks khác báo cáo Bước 3. Không tiếp tục.")
    record = col.get(ids=[args.chunk_id], include=["documents", "metadatas"])
    if len(record["ids"]) != 1:
        raise SystemExit("Không tìm thấy chunk_id. Kiểm tra chính xác ID và collection.")
    m = (record["metadatas"] or [{}])[0] or {}
    doc = (record["documents"] or [""])[0] or ""
    print("READ ONLY — CHUNK REVIEW")
    print("chunk_id:", record["ids"][0])
    print("source_id:", m.get("source_id"))
    print("section:", m.get("section"))
    print("URL:", m.get("canonical_url"))
    print("content_origin claim:", m.get("content_origin", "unknown"), "(chưa xác minh độc lập)")
    print("\n--- NỘI DUNG CHUNK (chỉ xem trên máy cá nhân) ---\n")
    print(doc)
    print("\n--- HẾT ---")
    print("Hãy đối chiếu website gốc và tự viết claim ngắn trong bảng review; không tự phê duyệt.")


if __name__ == "__main__":
    main()

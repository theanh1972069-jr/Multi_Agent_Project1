## 2026-11-03 — Giai đoạn 4, Bước 5D → 5E

- **Bằng chứng người dùng cung cấp:** Ảnh Neo4j Aura sau khi import cho thấy `processed_chunks=66` và `linked_sources=7`. Đây là kết quả lệnh import, **chưa chứng minh** trực tiếp count toàn database hoặc số orphan.
- Trước bước này, ảnh Bước 5C xác nhận 7 `SourceDocument`, 6 `Topic`, 7 `COVERS_TOPIC`, 3 `ChunkRef`, 3 `PART_OF`, 0 `MedicalClaim`.
- **Bước 5E chuẩn bị:** `05E-Aura-ReadOnly-Verification.cypher`, `tools/05E_chroma_neo4j_retrieval.py`, `05E-Graph-Retrieval-Guide.md`.
- Chưa có kết quả chạy Bước 5E, chưa đo chất lượng join thực tế. Không sửa graph/ChromaDB, không gọi LLM, không train ML.
- **Evidence Gate Bước 5A vẫn chưa đạt:** trích dẫn 25/42, quyền 13/42, 0/7 độc lập xác minh. Tiếp tục dùng để nghiên cứu nội bộ; chưa tư vấn y khoa bằng RAG/GraphRAG.

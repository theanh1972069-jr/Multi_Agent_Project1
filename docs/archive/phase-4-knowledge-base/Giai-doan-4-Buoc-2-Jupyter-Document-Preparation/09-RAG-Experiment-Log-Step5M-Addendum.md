# Experiment Log — Bổ sung Bước 5L và kế hoạch 5M

## 2026-11-03: Kết quả EXP-RAG-STEP5L-001 (do người dùng thực hiện)

- ChromaDB `diabetes_kb_step3_e5small_v1`: 66 chunks.
- Neo4j: 7 source, 66 chunk refs, 66 links, 0 orphan, 4 relation candidates, 4 technical reviews.
- Truy vấn 3 câu, 9/9 hit khớp provenance.
- `BLOCKED_RESEARCH_ONLY`, 0 answers, 0 LLM calls, 0 database writes.
- Chưa xác minh độc lập quyền sử dụng và nội dung y khoa. **Không bật Answering trên corpus thật.**

## Kế hoạch EXP-RAG-SANDBOX-STEP5M-001

- Tool: `tools/05M_rag_answering_sandbox.py`.
- Source: `data/sandbox/05M_synthetic_kb.json` (3 đoạn hư cấu).
- Cases: `registry/05M_sandbox_test_cases.json` (6 cases).
- Mode ban đầu: `--self-test`, `--mode dry-run`; optional `--mode ollama` do người dùng chủ động chạy.
- Chưa có kết quả 5M do người dùng thực hiện, **không điền metrics dự kiến thành thực tế**.
- Ghi nhận lỗi, câu trả lời, trích dẫn và số ca đúng sau khi nhận report.

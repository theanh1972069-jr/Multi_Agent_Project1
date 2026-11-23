# Giai đoạn 5 – Nhật ký thực nghiệm đến Bước 5 (2026-11-04)

| Bước | Chứng cứ người dùng thực thi | Kết luận | Giới hạn |
|---|---|---|---|
| 1 – Environment Audit | Python 3.13.9, `SHA256_MATCH`, Chroma dir tồn tại, Neo4j URI hợp lệ, `configured_not_connected` | Cấu hình đạt audit | Chưa chứng minh live connections ở Bước 1 |
| 2 – Data Analysis + Prediction | 2/2 live API cases, đúng model hash + threshold, `local_prediction_api_checked` | Đạt kiểm thử kỹ thuật | Không dự báo mắc bệnh tương lai, không huấn luyện mới |
| 3 – Knowledge Agent | 7 sources, 66 ChunkRef, 9/9 provenance, 0 approved claims; `local_chroma_neo4j_checked` | Đạt kiểm thử kỹ thuật | Medical Gate blocked, chỉ metadata |
| 4 – Consultation Agent | 6/6 preflight, 3/3 blocked before LLM, 3 Ollama answers, citations SYN-ATLAS-001/002/003 | Đạt kiểm thử vận hành; so sánh sơ bộ hỗ trợ nội dung | `manual_review_complete=false` trong report gốc; chưa là final human review |
| 5 – Unified Orchestrator + FastAPI | 16/16 contract tests; API fake-graph 200/422; Python syntax pass; 11 cases chạy qua graph simulator nội bộ | **Đã soạn bộ mã, chưa có kết quả LangGraph/Live của người dùng** | Môi trường tác giả thiếu LangGraph nên 5 graph tests skip; user chạy Step5 sẽ xác minh |

## Invariants giữ nguyên

- Model NHANES chỉ phân loại chỉ báo HbA1c ≥ 5.7%, threshold 0.225, model SHA256 khóa.
- ChromaDB 66 chunk với snapshot đã khóa, Neo4j 0 approved clinical claims.
- `medical_gate=BLOCKED_RESEARCH_ONLY` bất biến; Atlas synthetic không được thay thành tri thức y tế đã kiểm duyệt.
- Chưa có review về bản quyền và phê duyệt y khoa đủ để tạo lời khuyên lâm sàng.

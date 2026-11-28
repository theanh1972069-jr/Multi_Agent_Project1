# Bổ sung Nhật ký RAG — Giai đoạn 4, Bước 3 (chờ thực nghiệm)

> Ghép đoạn này vào `09-RAG-Experiment-Log.md` trên máy sau khi rà soát; **không ghi đè nhật ký đã có**.

## 2026-11-03 — Xác nhận đầu vào Bước 2
- `Registry sources = 7`, `Eligible sources = 7`, `Approved local files = 7`.
- `Prepared documents = 7`, `Chunks = 66`, `QA = PASS` (theo output Jupyter của người thực hiện).
- Chưa được cung cấp chunk JSONL/registry chỉnh sửa; chưa xác minh độc lập nguồn và quyền sử dụng.
- Embedding, Vector Database, LLM, model training: **chưa thực hiện**.

## Quyết định Bước 3 (proposed)
- Chọn mô hình embedding đa ngôn ngữ `intfloat/multilingual-e5-small`, offline inference sau khi tải lần đầu, `query:` và `passage:` prefixes.
- Chọn ChromaDB PersistentClient cho môi trường nghiên cứu local.
- Kiểm tra giới hạn 512 tokens trước embedding; tách records quá dài mà vẫn giữ parent ID.
- Yêu cầu xác nhận riêng về quyền dùng từng `source_id` trước khi tạo embeddings; WHO/Long Châu cần đặc biệt lưu ý.

## Kết quả Bước 3
**Chưa thực nghiệm** — chờ người dùng chạy `03_RAG_Embedding_ChromaDB.ipynb` và cung cấp JSON report.

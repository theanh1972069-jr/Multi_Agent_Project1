# Hướng dẫn Bước 4 – Retrieval Evaluation (Jupyter)

## Không cần train hoặc tạo lại vector

Bạn đã hoàn tất Bước 3 với 66 chunks/7 nguồn. Giữ nguyên ChromaDB và tên collection. Sử dụng lại kernel Python từ Bước 3.

### 1. Chuẩn bị file

Giải nén gói vào chính thư mục `04-Knowledge-Base-RAG` của bạn. **Không chép đè** `data/vector_store/`, `data/processed/` hoặc `registry/source_registry.csv` đã cập nhật trên máy.

- `notebooks/04_RAG_Retrieval_Evaluation.ipynb`
- `registry/step4_eval_questions.csv`
- `04-Retrieval-Pipeline-Evaluation.md`

### 2. Chạy Notebook (lượt A)

Mở bằng Jupyter. Đảm bảo `data/outputs/embedding_chroma_step3/step3_embedding_chroma_report.json` đang có, và tên collection trùng chính bản bạn tạo.

Chạy từ đầu tới ô **4. Xuất CSV để chấm thủ công**. Notebook sinh:

`data/outputs/retrieval_eval_step4/step4_retrieval_review.csv`

Nếu chạy toàn notebook ngay, ô 5 sẽ thông báo **awaiting_human_labels**. Đây là bình thường, không phải lỗi. **Không chạy lại ô 4** sau khi đã chấm vì ô 4 được thiết kế để từ chối ghi đè CSV.

### 3. Chấm thủ công

Trong CSV, cho từng kết quả tìm kiếm điền:

- `relevance_grade`: 0 (không hợp), 1 (liên quan một phần), 2 (phù hợp trực tiếp).
- `citation_ok`: yes/no, kiểm tra URL và nội dung thực tế.
- `rights_evidence_ok`: yes/no/unknown, dựa trên bằng chứng; nếu chưa kiểm định độc lập thì để unknown.
- `review_notes`: ghi lỗi/nhận định; đừng ghi dữ liệu sức khỏe cá nhân.

Tổng cộng **14 câu × 3 hits = 42 dòng**. Khi hỏi ngoài phạm vi hoặc yêu cầu kê thuốc, chỉ đánh giá Retrieval; không dùng để tư vấn y tế.

### 4. Tính kết quả (lượt B)

Lưu CSV. Quay lại Notebook, **chỉ chạy lại ô 5**, không chạy lại ô xuất CSV. Notebook tạo `step4_retrieval_eval_report.json` và in ra kết quả `GIAI ĐOẠN 4 — BƯỚC 4: RETRIEVAL EVALUATION`.

### 5. Gửi cho trợ lý

Gửi **output cuối** và `step4_retrieval_eval_report.json`. Nếu có trường hợp Retrieval không phù hợp, mô tả ngắn `query_id`, `source_id`, `section`, lý do. Không cần gửi toàn văn bài viết từ WHO hay Long Châu.

## Quy tắc

Không gọi LLM; không `add/upsert/delete` ChromaDB; không mở lại NHANES test; không tối ưu mô hình trên câu hỏi kiểm thử một cách vòng lặp rồi gọi đó là đánh giá độc lập. Quyền sử dụng và nội dung y khoa chưa có xác minh độc lập.

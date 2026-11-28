# Hướng dẫn thực hành Giai đoạn 4 — Bước 5A (Jupyter)

**Vẫn thuộc Bước 5 trong roadmap (RAG Answering & Knowledge Agent): phần tiền kiểm Evidence Gate.** Bạn tự chạy, không train, không gọi LLM.

## 1. Chuẩn bị

- Dùng cùng thư mục và kernel Python Bước 3–4, có `chromadb`, `sentence-transformers`.
- KHÔNG ghi đè registry hiện có, các file `.txt`, `data/processed/`, `data/vector_store/`.
- Đảm bảo file đánh giá 42 dòng tại `data/outputs/retrieval_eval_step4/step4_retrieval_review.csv` và JSON report Bước 4 ở cùng thư mục.

## 2. Chạy notebook

Mở `notebooks/05A_RAG_Evidence_Provenance_Gate.ipynb` và chạy các ô từ đầu đến cuối. Notebook:

1. Kiểm tra baseline report và các file đã chấm.
2. Tổng hợp bằng chứng quyền/trích dẫn theo 7 nguồn thành `step5a_source_audit.csv`.
3. Tạo (nếu chưa tồn tại) biểu mẫu `registry/step5a_source_rights_review.csv`; tất cả nguồn **mặc định pending**.
4. Xem Q01 và Q05; lấy top-10 trên collection cũ (chỉ truy vấn) thành `step5a_q01_q05_top10_review.csv` để bạn chấm bổ sung nếu muốn.
5. Ghi `step5a_gate_report.json` với `ready_for_llm=false`, không coi registry tự khai là thẩm định độc lập.

## 3. Bạn cần chấm và bổ sung

- Mở `step5a_source_rights_review.csv`: kiểm tra tài liệu gốc, quyền dùng **nội dung cụ thể** và loại tài liệu (nguồn thứ ba/ghi chú tự biên soạn). Điền `rights_review_status`, `evidence_url_or_permission`, `reviewer`, `reviewed_at_utc`, `medical_content_review_status`, ghi chú. **Không điền `verified` khi chưa có bằng chứng**.
- Mở `step5a_q01_q05_top10_review.csv`: điền `relevance_grade` 0/1/2 cho các ứng viên nếu muốn nghiên cứu lỗi retrieval. Không gửi toàn văn bài viết cho trợ lý; chỉ gửi bảng và nhận xét ngắn.
- Không chạy lại ô tạo template sau khi đã điền: notebook có cơ chế không ghi đè file có sẵn.

## 4. Gửi kết quả

Gửi output `GIAI ĐOẠN 4 — BƯỚC 5A: EVIDENCE GATE`, `step5a_gate_report.json`, và nếu có `step5a_source_audit.csv`, phần Q01/Q05 đã chấm. Tôi sẽ kiểm tra rồi hướng dẫn Bước 5B xây dựng RAG Answering/Knowledge Agent có guardrails.

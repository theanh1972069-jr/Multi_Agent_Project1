# 05A — Evidence & Provenance Gate (Giai đoạn 4 / Bước 5A)

**Dự án:** Multi-Agent AI hỗ trợ đánh giá chỉ dấu HbA1c liên quan đến tiểu đường  
**Trạng thái:** Sẵn sàng cho người dùng tự thực hành; CHƯA chạy notebook 5A / chưa dùng LLM.  
**Ngày:** 2026-11-03 · v0.1

## 1. Vì sao cần Bước 5A?

Bước 4 đã hoàn thành chấm 42 lượt truy xuất và có kết quả baseline: P@3=0.8611 (grade>=1), Strict Hit@3=0.8333 (10/12), MRR@3=0.7778 trên 12 câu in-scope. Đây là thành công **về chất lượng truy xuất trên tập câu hỏi phát triển**, không bảo đảm nguồn được phép dùng hoặc câu trả lời y khoa đúng.

- 25/42 lượt đánh giá có `citation_ok=yes` (59,52%).
- 13/42 có `rights_evidence_ok=yes` (30,95%); 29/42 bị ghi `no` (có thể là chưa đủ bằng chứng, **không mặc nhiên kết luận vi phạm**).
- Báo cáo Step4 ghi `source_reviews_independent=false`.
- Q01 và Q05 không có chunk grade=2 trong Top3: [0,1,1] và [1,1,1].
- Q13 ngoài phạm vi và Q14 câu hỏi liều insulin đều có relevance=0, nhưng **chưa kiểm định** khả năng abstain hoặc xử lý an toàn của hệ thống sinh câu trả lời.

**Quyết định:** Giữ nguyên 66 vectors/7 nguồn để nghiên cứu nội bộ; **không chuyển toàn bộ văn bản sang LLM để tạo tư vấn y khoa** cho đến khi có bằng chứng quyền sử dụng, trích dẫn hợp lệ và bằng chứng phù hợp.

## 2. Mục tiêu Bước 5A

1. Đối chiếu tính toàn vẹn của báo cáo Step3/Step4 với CSV đánh giá trên máy.
2. Xuất bảng audit theo từng nguồn về `citation_ok`, `rights_evidence_ok`, grade; ghi rõ thiếu hụt.
3. Bạn tự xác minh **quyền dùng nội dung cụ thể**, liên kết với giấy phép/bằng chứng và người rà soát cho 7 nguồn; **không** tự động approve theo nhãn `licensed_source_text`.
4. Điều tra Q01/Q05 bằng cách lấy ứng viên Top-10 từ **collection gốc chỉ đọc**; chấm thủ công, không chấp nhận cải thiện như test độc lập.
5. Xuất báo cáo preflight, không gọi LLM/không làm bất kỳ hành động ghi vào ChromaDB.

## 3. Hợp đồng đầu vào/đầu ra

**Đầu vào trên máy của bạn:**
- `data/outputs/embedding_chroma_step3/step3_embedding_chroma_report.json`
- `data/outputs/retrieval_eval_step4/step4_retrieval_eval_report.json`
- `data/outputs/retrieval_eval_step4/step4_retrieval_review.csv` (42 dòng đã chấm)
- ChromaDB cũ tại đường dẫn trong report Step3.

**Đầu ra (do bạn chạy):**
- `data/outputs/rag_gate_step5a/step5a_source_audit.csv` (thống kê, tự tạo)
- `registry/step5a_source_rights_review.csv` (template; chỉ bạn cập nhật sau khi xác minh)
- `data/outputs/rag_gate_step5a/step5a_q01_q05_top10_review.csv` (ứng viên; tự chấm grade)
- `data/outputs/rag_gate_step5a/step5a_gate_report.json` (trạng thái preflight)

## 4. Điều kiện để bước RAG Answering dùng được nguồn

Cần đồng thời: (a) rõ nguồn gốc và phiên bản, (b) có bằng chứng quyền tái sử dụng nội dung cụ thể, (c) được xác minh chuyên môn với ngữ cảnh thích hợp, (d) trích dẫn liên kết đúng chunk → tài liệu → URL, (e) đoạn trả lời trực tiếp câu hỏi. Nếu bất kỳ điều kiện nào chưa có, **abstain** hoặc chỉ đưa URL dưới dạng nguồn tham khảo, không lấy nội dung đó để sinh câu trả lời có vẻ chắc chắn.

Trạng thái `approved_research` tự khai trên registry **không đủ** để đánh dấu `approved_for_answering`.

## 5. Phương án nâng chất lượng Retrieval

- Q01 và Q05 mở rộng Top3 → Top10 trên collection cũ, kiểm tra liệu đoạn grade=2 xuất hiện ở vị trí 4–10.
- Nếu không có: xem xét BM25 + E5 (hybrid), RRF, hoặc reranking, nhưng phải so sánh trên **tập phát triển** và tạo tập câu hỏi chưa dùng để kiểm tra sau cùng.
- Trước khi dùng cho chatbot, cần bộ lọc bằng chứng đã được phê duyệt thay vì chỉ xem distance/nguồn trả về Top1.

## 6. Quy trình an toàn

- Không tự kéo nội dung nguồn chưa có quyền, không đưa tài liệu chưa xác minh cho LLM.
- Không mở lại NHANES Test, không sửa mô hình ML, không `add/upsert/delete` collection.
- Không coi Precision@3 hoặc độ chính xác trích dẫn là độ chính xác lâm sàng.
- Giữ nguyên hai câu Q13/Q14 như test case; sau này implement phân loại intent/guardrails để từ chối tư vấn liều thuốc, chuyển hướng liên hệ nhân viên y tế phù hợp.
- Không tự chốt `ready_for_llm=true` chỉ vì một file CSV đã được điền. Việc chốt cần kiểm chứng hồ sơ, đánh giá nội dung và an toàn đầy đủ.

## 7. Kết quả thực nghiệm

**Chưa có.** Chờ người dùng chạy notebook 5A và gửi `step5a_gate_report.json`, bảng audit và phần chấm Q01/Q05. Không gán bất kỳ metric cải thiện nào trước khi có nhãn đánh giá.

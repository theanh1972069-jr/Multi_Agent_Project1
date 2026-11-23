# 04 — Retrieval Pipeline & Evaluation (Giai đoạn 4 / Bước 4)

**Dự án:** Multi-Agent AI hỗ trợ đánh giá chỉ dấu HbA1c liên quan đến tiểu đường  
**Trạng thái:** Notebook đã chuẩn bị; người dùng chưa chạy bước đánh giá và chưa chấm nhãn.  
**Ngày:** 2026-11-03 · Phiên bản v0.1

## 1. Điểm xuất phát (đã thực nghiệm)

- 7 nguồn, 66 chunks, 384 chiều, collection `diabetes_kb_step3_e5small_v1`.
- Embedding `intfloat/multilingual-e5-small` với `passage:` và `query:`; cosine distance không là xác suất đúng.
- QA kỹ thuật Bước 3 PASS; **chưa có đánh giá relevance khách quan**.
- Báo cáo review: `self_declared_only_not_independently_verified`; chưa có đối chứng độc lập bản quyền/y khoa. Trong bước 4 chỉ sử dụng trên máy người dùng để nghiên cứu.

## 2. Mục tiêu của bước

1. Truy vấn tập vector đã có mà **không** tái index hoặc train ML.
2. Đo chất lượng top-3 với 14 câu hỏi cố định: 12 in-scope (tiếng Anh/Việt), 1 ngoài phạm vi, 1 safety probe.
3. Có đánh giá thủ công từng kết quả: relevance 0/1/2, URL/citation, tình trạng quyền sử dụng.
4. Tính chỉ số có cơ sở; không suy luận từ cosine distance rằng thông tin được chứng thực.
5. Xem lỗi lệch chủ đề, phụ thuộc nguồn/ ngôn ngữ và khả năng phân biệt ngoài phạm vi.

## 3. Hợp đồng dữ liệu

- Input: `registry/step4_eval_questions.csv`, báo cáo Bước 3, Chroma local giữ nguyên snapshot.
- Output A: `data/outputs/retrieval_eval_step4/step4_retrieval_review.csv` do notebook tạo, **con người điền**.
- Output B (chỉ sau khi điền đủ): `data/outputs/retrieval_eval_step4/step4_retrieval_eval_report.json`.
- CSV có query_id, type, language, rank, chunk_id, source_id, section, URL, distance, preview ngắn; relevance_grade, citation_ok, rights_evidence_ok, review_notes. Không gửi toàn văn cho trợ lý.

## 4. Thang điểm đánh giá thủ công

| Grade | Ý nghĩa | Ví dụ |
|---|---|---|
| 0 | Không trả lời câu hỏi hoặc sai chủ đề | Hỏi yếu tố nguy cơ, đoạn nói riêng về chẩn đoán không nhắc nguy cơ |
| 1 | Có liên quan một phần, còn thiếu ý hoặc quá chung | Hỏi nhiều yếu tố nguy cơ, đoạn chỉ nói giảm cân |
| 2 | Trực tiếp, đủ bằng chứng để trả lời đúng phần câu hỏi | Hỏi HbA1c là gì, đoạn giải thích xét nghiệm HbA1c rõ ràng |

Điểm nguồn tin uy tín **không thể thay** việc đọc nội dung chunk. Reviewer cần mở URL, đối chiếu ý nghĩa và quyền tái sử dụng. Metadata `content_origin=licensed_source_text` là nhãn người dùng tự khai, không phải giấy phép được xác minh độc lập.

## 5. Chỉ số sau khi có nhãn

Chỉ tính các câu `in_scope`:

- **Precision@3:** tổng số hit grade >=1 / tổng 3 hit mỗi câu, trung bình 12 câu.
- **Strict Hit@3:** tỷ lệ câu có ít nhất một hit grade 2 trong top-3.
- **MRR@3:** trung bình 1 / vị trí đầu tiên có hit grade 2; không có thì 0.
- **Mean Grade@3:** trung bình grade 0..2 của top-3.
- **Citation OK rate:** tỷ lệ kết quả có URL và đối chiếu nguồn đúng theo đánh giá người dùng.
- **Rights verification:** đếm yes/no/unknown riêng, không tự coi yes dựa trên registry.

**Không tính Recall@3** do không có danh sách tất cả các chunk liên quan trên toàn bộ 66 chunks. Muốn đánh giá Recall@3 cần hoàn tất relevance judgments toàn bộ corpus hoặc xây dựng qrels đủ tin cậy. Không thiết lập threshold từ 3 truy vấn mẫu.

## 6. Rủi ro và hành động sau đánh giá

- Query tiếng Việt về yếu tố nguy cơ trả nhiều chunk Long Châu về giai đoạn bệnh: có thể cần rerank, lọc chủ đề hoặc hybrid retrieval sau **khi** có benchmark.
- Nguồn thứ cấp có thể vượt nguồn chính thống vì gần ngữ nghĩa; Retrieval cần phân biệt **relevance, authority, authorization**.
- Ngoài phạm vi và câu hỏi đòi kê đơn cần chuyển hướng an toàn ở bước Knowledge Agent/RAG Answering; **không tự coi vector hit là một lời tư vấn**.
- Chỉ xây dựng optional BM25/RRF/reranking sau khi đã đo baseline và cố định bộ câu hỏi kiểm thử để tránh chọn theo may mắn.

## 7. Điều kiện kết thúc Bước 4

- Người dùng tự chạy Notebook tạo CSV và chấm đủ 42 hits; notebook tính metrics, báo cáo JSON.
- Có phân tích ít nhất 3 trường hợp top-3 chưa phù hợp và kiểm tra gốc nguồn.
- Báo cáo chưa được dùng để chứng minh năng lực chẩn đoán, quyền sử dụng nguồn hoặc lâm sàng.
- Sau đó mới chuẩn bị Bước 5 – RAG answering và Knowledge Agent nghiên cứu.

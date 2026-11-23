# 03 — Embeddings & Vector Database (ChromaDB)

**Dự án:** Multi-Agent AI hỗ trợ đánh giá chỉ dấu HbA1c liên quan đến tiểu đường  
**Giai đoạn:** 4, Bước 3  
**Trạng thái:** Hướng dẫn/chưa có thực nghiệm Embedding của người dùng  
**Phiên bản:** v0.1

## A. Kết quả đầu vào đã xác nhận

Theo ảnh kết quả Jupyter do người dùng cung cấp ngày 2026-11-03:

| Chỉ tiêu | Giá trị |
|---|---:|
| Nguồn trong registry | 7 |
| Nguồn eligible trong notebook Bước 2 | 7 |
| File văn bản được chấp nhận | 7 |
| Tài liệu prepared | 7 |
| Chunks sau cleaning | 66 |
| QA kỹ thuật | PASS |
| Embeddings / Vector DB | Chưa chạy |

**Giới hạn bằng chứng:** Chưa nhận bản nội dung 66 chunks và registry đã chỉnh để kiểm tra độc lập. Không coi `approved_research` hay `QA PASS` là bằng chứng quyền tác giả hoặc kiểm định y khoa.

## B. Thiết kế Embedding

- Mô hình ứng viên: `intfloat/multilingual-e5-small` hỗ trợ truy xuất tiếng Việt/tiếng Anh.
- Dùng `passage: ` cho nội dung lưu vector, `query: ` cho câu hỏi truy vấn.
- Vector L2-normalized, truy vấn bằng cosine distance; **distance thấp hơn gần hơn**, không hiểu là xác suất đúng hay độ tin cậy y khoa.
- Model hỗ trợ tối đa 512 tokens: notebook kiểm tra thực tế và chia thêm chunk dài, giữ ID chunk gốc.
- Bản model lần đầu được tải qua mạng; việc tính embeddings chạy cục bộ trên máy người dùng.

## C. Thiết kế ChromaDB

- Kiểu client: `chromadb.PersistentClient` cục bộ.
- Collection: `diabetes_kb_step3_e5small_v1` (sửa tên khi lập phiên bản index mới).
- Cấu hình index: cosine.
- Metadata tối thiểu: `source_id`, `canonical_url`, `publisher`, `section`, `document_version`, `document_sha256`, `chunk_sha256`, `parent_chunk_id`, `content_origin`, `retrieved_at_utc`.
- Kiểm tra snapshot SHA256 để không vô ý trộn tài liệu/embedding khác phiên bản.
- Không có LLM hoặc câu trả lời tư vấn tự sinh ở Bước 3.

## D. Chính sách kiểm duyệt tài liệu

WHO và Long Châu cần được phân biệt giữa (i) văn bản nguồn được phép tái sử dụng, (ii) ghi chú nghiên cứu tự biên soạn dựa trên nguồn, (iii) tài liệu chỉ được phép tham khảo URL. Loại (iii) **không được index nội dung không có quyền**. Đối với (ii), ghi rõ `content_origin=original_research_note` và không gán tác giả ghi chú cho WHO/Long Châu.

## E. Bài kiểm tra truy xuất đề xuất

1. `Những yếu tố nào liên quan đến tiểu đường type 2?`
2. `HbA1c dùng để đánh giá tình trạng đường huyết như thế nào?`
3. `What are the common risk factors for type 2 diabetes?`

Kết quả đánh giá chất lượng cần kiểm tra **relevance thực tế và đúng dẫn nguồn**. Chưa thể suy luận từ số chunks rằng hệ thống trả lời đúng câu hỏi.

## F. Bảng ghi chép sau khi người dùng chạy notebook

| Chỉ tiêu | Giá trị thực tế |
|---|---|
| Python / Chroma / SentenceTransformers | Chưa thực nghiệm |
| Review eligible sources | Chưa thực nghiệm |
| Input chunks | Dự kiến 66, sẽ đối chiếu |
| Indexed records (sau chia token) | Chưa thực nghiệm |
| Embedding dimension | Chưa thực nghiệm |
| Collection count | Chưa thực nghiệm |
| Số nguồn sau index | Chưa thực nghiệm |
| Queries chạy và kết quả nguồn | Chưa thực nghiệm |
| Source snapshot SHA256 | Chưa thực nghiệm |
| Báo cáo JSON | Chưa thực nghiệm |

## G. Điều kiện chuyển bước tiếp theo

Chỉ khi người dùng tự chạy đạt QA, có thể truy xuất ít nhất một đoạn có dẫn nguồn phù hợp với query và hồ sơ quyền sử dụng rõ ràng, mới tiến hành đánh giá Retrieval chuyên sâu. Không sử dụng kết quả nghiên cứu này để tư vấn điều trị.

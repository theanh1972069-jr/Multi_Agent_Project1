# Giai đoạn 4 — Bước 5L: Kết quả Safe Retrieval

**Nguồn số liệu:** `step5l_safe_retrieval_report.json` do người dùng tự chạy và gửi, thời điểm ghi trong JSON: `2026-11-03T09:54:19.165959+00:00`.
**Trạng thái:** Hoàn thành kiểm thử kỹ thuật nguyên mẫu; không phê duyệt sử dụng y khoa.

## Các kết quả đã xác nhận

| Hạng mục | Kết quả |
|---|---:|
| SourceDocument | 7 |
| ChunkRef | 66 |
| PART_OF links | 66 |
| Orphan chunks | 0 |
| RelationCandidate | 4 |
| TechnicalReview | 4 |
| Approved relations | 0 |
| Approved claims | 0 |
| Joined hits | 9 |
| Provenance matches | 9 |
| Answers generated | 0 |
| LLM called | false |
| ChromaDB modified / Neo4j modified | false / false |

Ba câu hỏi Q01, Q02, Q03 đều trả Top 3 theo embedding; mọi hit có `graph_provenance_match = true`, nhưng đều `allowed_to_answer = false`. Riêng chunk NIDDK `NIDDK-T2D-004__v1__9de2376433__0004` có 4 liên kết claim ứng viên và 0 liên kết đủ điều kiện sử dụng.

## Kết luận

1. Khớp metadata hai kho dữ liệu đã đạt trên ba câu hỏi thử nghiệm, 9/9 hits.
2. Cơ chế chặn mặc định vận hành đúng trên các dữ liệu hiện có: `BLOCKED_RESEARCH_ONLY`.
3. Bài kiểm tra **không** tương đương đánh giá bảo mật/kiểm duyệt sản xuất: bằng chứng bản quyền và thẩm định y khoa chưa được xác minh độc lập.
4. Giữ nguyên ChromaDB, Neo4j và khóa sử dụng tài liệu y khoa; không mở khóa claim hoặc relation.

**Quyết định:** Chuyển sang 5M, tạo RAG Answering Sandbox tách biệt, dùng dữ liệu hư cấu do nhóm tự biên soạn. Không dùng bảy nguồn thật để thử tạo câu trả lời LLM.

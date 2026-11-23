# Giai đoạn 4 – Bước 5J: Review Queue & Safe Graph Retrieval

**Trạng thái:** Hướng dẫn đã chuẩn bị; chưa chạy trên Neo4j Aura. Chỉ dùng Cypher đọc dữ liệu (READ-ONLY).

## Kết quả Bước 5I (người dùng cung cấp)

| candidates | technical_reviews | review_links | approved_relations | not_blocked_relations | approved_claims |
|---:|---:|---:|---:|---:|---:|
| 4 | 4 | 4 | 0 | 0 | 0 |

TechnicalReview chỉ kiểm tra cấu trúc/truy vết; không chứng minh quyền tái sử dụng nội dung hay thẩm định y khoa. Chưa có số liệu xác nhận `missing_provenance` từ kết quả mới nhất, nên Bước 5J sẽ kiểm tra lại.

## Mục tiêu

- Đọc review queue gồm relation → concept/claim → chunk → nguồn → technical review.
- Kiểm toán liên kết thiếu, không tự coi dữ liệu đầy đủ chỉ dựa trên số lượng.
- Kiểm tra chính sách **mặc định chặn**: quan hệ ứng viên không được dùng để sinh câu trả lời y khoa khi thiếu phê duyệt độc lập.

## Cách thực hiện trên Neo4j Aura

Mở file `05J-Neo4j-Review-Queue-Safe-Gate.cypher` rồi chạy từng khối:

| Khối | Nội dung | Kỳ vọng |
|---|---|---|
| `[0]` | Đếm node và trạng thái | `4,4,4,0,0,0` theo thứ tự trả về |
| `[1]` | Bảng review queue | 4 dòng |
| `[2]` | 5 kiểm tra liên kết thiếu | 0 ở cả 5 cột |
| `[3]` | Safe-gate mô phỏng | **0 dòng** |
| `[4]` | Audit số phê duyệt và bỏ chặn | 0 ở cả 4 cột |
| `[5]` | Xem graph đường đi bằng chứng | 4 quan hệ ứng viên gắn claim/chunk/source và review |

`[3]` nhắc tới hai label `IndependentMedicalReview` và `IndependentRightsReview` **dự kiến trong tương lai**, hiện không có. Không tạo hoặc giả mạo các review node này; truy vấn này chỉ thử fail-closed, **chưa phải phân quyền sản xuất**.

## Những giới hạn phải giữ nguyên

- Bốn relation vẫn `draft_unverified` và `blocked_for_answering`.
- Quyền sử dụng của 7 nguồn và nội dung y khoa vẫn chưa được xác minh độc lập.
- Không gọi LLM, không sửa ChromaDB, không đổi model ML, không mở NHANES Test.
- Không dùng kết quả technical review làm bằng chứng cho tính đúng đắn y khoa.

## Bạn gửi lại

Kết quả khối `[1]` (có thể ẩn URL dài), `[2]`, `[4]`, và xác nhận `[3]` có trả 0 dòng hay không. Không chia sẻ thông tin đăng nhập Aura.

**Bước sau:** Thiết kế quy trình xác minh độc lập và điều kiện trích dẫn/abstention, rồi mới xem xét RAG Answering/Knowledge Agent.

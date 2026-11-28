# Giai đoạn 4 – Bước 5K: Hồ sơ kiểm duyệt độc lập và điều kiện đưa Knowledge Graph vào RAG

**Trạng thái:** Đã chuẩn bị hướng dẫn. Người dùng sẽ thực hiện trên **Neo4j Aura Console**, không bắt buộc Jupyter.

**Đầu vào:** Bước 5J được người dùng xác nhận đạt kỳ vọng: 4 quan hệ ứng viên, 4 review kỹ thuật, không có liên kết thiếu, truy vấn chặn trả 0 hàng.

## 1. Bước này để làm gì?

Ở Bước 5J, hệ thống kiểm tra **đường đi bằng chứng** và cơ chế chặn quan hệ chưa được phê duyệt. Chưa xác minh độc lập rằng (a) nội dung có quyền tái sử dụng để tạo embeddings hoặc sử dụng trong ứng dụng; (b) claim được diễn giải chính xác và còn phù hợp với bằng chứng y khoa. Cả hai việc cần những hồ sơ khác với `TechnicalReview`.

**Không tự tạo node `IndependentMedicalReview` / `IndependentRightsReview` với `decision='approved'` chỉ để đạt chỉ tiêu.** Nếu thiếu người có thẩm quyền hoặc tài liệu chứng minh thì để `pending`.

## 2. Các bước người dùng tự thực hiện

1. Mở `05K-Aura-Review-Queues.cypher` trong VS Code; chạy **từng khối** trên Neo4j Aura → Query. Tất cả chỉ đọc.
2. `[0]` kiểm tra 7 nguồn, 4 relation, 1 claim, 4 TechnicalReview; 0 approved relations/claims. Đây là dự kiến theo phiên bản graph hiện tại, không phải kết quả đã chạy.
3. `[1]` xem 7 nguồn, kiểm tra URL, loại nội dung và quyền tái sử dụng. Chỉ điền bằng chứng **thật** vào `05K-review-register.csv`.
4. `[2]` xem 4 relation ứng viên, một claim NIDDK, chunk và URL. Người rà soát y khoa đủ chuyên môn cần kiểm tra **từng quan hệ** (risk factor vs cơ chế liên quan vs di truyền, không đồng nhất với nhân quả); nếu chưa có reviewer, để `pending`.
5. `[3]` phải trả 0 liên kết thiếu. `[4]` phải trả 4 hàng `blocked=true`, `[5]` phải trả **0 hàng**.
6. Gửi các bảng `[0]`, `[3]`, `[4]` và trạng thái `[5]`, cùng số lượng hồ sơ ở trạng thái `pending` trong CSV. Không gửi mật khẩu hoặc dữ liệu cá nhân.

## 3. Ma trận duyệt cần có trước khi cho phép trả lời bằng LLM

| Hạng mục | Bằng chứng cần lưu | Ai xác minh | Nếu chưa xong |
|---|---|---|---|
| **Quyền tái sử dụng nguồn** | URL, điều khoản áp dụng, phạm vi sao chép, phiên bản/ngày truy cập, giấy phép/email nếu cần | Người phụ trách pháp lý/quyền nội dung | `pending`, không cho sử dụng nguồn đó trong RAG sinh câu trả lời |
| **Mệnh đề y khoa** | Claim, đoạn nguồn, ngữ cảnh, điều kiện áp dụng, tài liệu đối chiếu | Người có chuyên môn y tế | `pending`, giữ `draft_unverified` |
| **Quan hệ y khoa** | Subject, object, loại quan hệ, claim và bằng chứng, giới hạn diễn giải | Người có chuyên môn y tế | `pending`, giữ blocked |
| **Trích dẫn** | URL phải trỏ đúng nội dung hỗ trợ câu trả lời, không chỉ đúng chủ đề | Reviewer nội dung/QA | Trả lời bị chặn nếu không đủ evidence |
| **An toàn** | Test abstention/out-of-scope/prompt injection và logging | QA/security | Chưa đưa chatbot y khoa vào thực tế |

**Phân biệt:** xác nhận rằng chunk giống nội dung website không đủ chứng minh quyền sao chép, cũng không tự chứng minh tính chính xác lâm sàng.

## 4. Dữ liệu đầu ra

- `05K-review-register.csv`: 7 source-rights items, 1 claim-medical item, 4 relation-medical items. Mỗi dòng chờ bằng chứng và quyết định thật.
- Truy vấn read-only để kiểm tra rằng chưa có dữ liệu y khoa nào được phép sử dụng.
- Kết quả thực nghiệm mới được điền vào báo cáo **sau khi người dùng chạy**, không tự bịa số liệu.

## 5. Giới hạn

- Neo4j vẫn là graph research-only. Không tự điều chỉnh ChromaDB (66 chunks), không chạy lại mô hình NHANES, không mở lại Test, không gọi LLM.
- Xác minh giấy phép khác nhau theo bài viết: **CDC/NIDDK, WHO, Long Châu cần kiểm tra từng nội dung cụ thể**; không suy luận rằng mọi trang cùng một nhà cung cấp đều có cùng quyền tái sử dụng.
- Kết quả 5J đã đạt **kiểm thử chặn trong cấu hình hiện tại**; chưa có bằng chứng về phân quyền, chống giả mạo approval hoặc an toàn khi xuất bản.

## 6. Hướng sau Bước 5K

Nếu chưa có người thẩm định độc lập, vẫn có thể tiếp tục **thử nghiệm kỹ thuật retrieval fusion và abstention với dữ liệu giả lập/được cấp phép riêng**, không gọi đó là Knowledge Agent y khoa đã được xác thực. Khi quyền và chất lượng y khoa được kiểm định, mới thiết kế chính sách kích hoạt nguồn/claim có khả năng kiểm toán và viết báo cáo đánh giá riêng.

## Tài liệu tham khảo kỹ thuật

- Neo4j Cypher: https://neo4j.com/docs/cypher-manual/current/clauses/merge/
- Neo4j Cypher subqueries: https://neo4j.com/docs/getting-started/cypher/subqueries/

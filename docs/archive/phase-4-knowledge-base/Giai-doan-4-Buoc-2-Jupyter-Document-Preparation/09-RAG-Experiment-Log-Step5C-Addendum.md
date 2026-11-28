# Giai đoạn 4 — Nhật ký bổ sung Bước 5C (chưa chạy)

- Ghi nhận: Chưa nhận được output Bước 5B từ Neo4j AuraDB.
- Thiết kế 5C: tạo uniqueness constraints cho ChunkRef và MedicalClaim; liên kết 3 chunk_id đã có trong báo cáo ChromaDB Bước 3; cho phép tạo MedicalClaim dạng `draft_unverified` khi người dùng đối chiếu văn bản thật.
- Không thực thi thay người dùng. Không tải toàn văn nguồn, không xác minh độc lập quyền sử dụng, không thay đổi ChromaDB/ML, không gọi LLM.
- Bước tiếp theo: Người dùng tự thực thi trên Aura Console, gửi kết quả preflight 5B và 5C.
- Các chỉ số ở tài liệu 05C là số kỳ vọng, không phải output chạy thực tế.

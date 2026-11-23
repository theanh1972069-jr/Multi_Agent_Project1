# Giai đoạn 4 – Bổ sung Experiment Log, Bước 5G → 5H

Ngày ghi: **2026-11-03**.

## Kết quả người dùng gửi (Bước 5G)

- Graph Neo4j Aura thể hiện `MedicalClaim RESEARCH-CLAIM-001` nối 5 thực thể bằng `MENTIONS_CONCEPT`.
- Kết quả Cypher: `concepts=5`, `mention_links=5`, `approved_claims=0`, `claims_not_blocked=0`.
- Bước 5G được xác nhận đạt ở mức cấu trúc đồ thị, **không phải kiểm chứng lâm sàng**.

## Kế hoạch bước 5H

- Tạo `RelationCandidate` dạng node ứng viên, liên kết `SUBJECT_CONCEPT`, `OBJECT_CONCEPT` và `SUPPORTED_BY_CLAIM`.
- Làm thử 1 quan hệ thừa cân/béo phì → tiểu đường type 2, vẫn `draft_unverified` và `blocked_for_answering`.
- Chỉ mở rộng thêm 3 ứng viên sau khi người dùng gửi kết quả kiểm tra của lần thử đầu.
- **Chưa chạy Cypher, chưa duyệt quan hệ, chưa gọi LLM, chưa thay đổi ChromaDB.**

## Các giới hạn còn tồn tại

- Bước 5A: `ready_for_llm=false`, xác minh độc lập 0/7 nguồn.
- Trích dẫn Bước 4: 25/42 được đánh dấu đạt; bằng chứng quyền 13/42.
- Neo4j lưu metadata và claims chờ duyệt; không được xem như Knowledge Graph y khoa hoàn chỉnh dùng lâm sàng.

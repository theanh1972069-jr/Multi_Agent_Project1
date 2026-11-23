# Giai đoạn 5 – Bước 3: Nhật ký kiểm tra khi tạo bộ thực hành

- Kiểm tra cú pháp: `compileall` chạy không lỗi cho `step3_knowledge_integration.py`, `step3_run.py`, `step3_self_test.py`.
- Kiểm thử offline: `python -m phase5.step3_self_test` → **15/15 pass** trong môi trường tạo bộ thực hành.
- Môi trường này không cài LangGraph, ChromaDB, Neo4j Python driver và SentenceTransformers. Vì vậy **chưa chạy Graph mock hoặc kết nối live** ở phía trợ lý; kết quả sẽ do người dùng gửi.
- Báo cáo Bước 2 Live do người dùng gửi: 2/2 `ok`, SHA256, threshold match, knowledge gate blocked. Không lặp lại huấn luyện.
- Không có phê duyệt medical/rights độc lập; không mở khóa MedicalClaim hoặc RelationCandidate.

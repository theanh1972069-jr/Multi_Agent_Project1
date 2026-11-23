# GIAI ĐOẠN 4 — NHẬT KÝ THỰC NGHIỆM RAG

**Phiên bản:** v0.1 — 2026-11-03

| Mã | Bước | Nội dung | Trạng thái | Bằng chứng |
|---|---|---|---|---|
| RAG-EXP-001 | 1 | Xây danh mục 7 nguồn CDC, NIDDK, WHO và Long Châu | Tài liệu v0.2 hoàn thành, nguồn vẫn ứng viên | `01-Knowledge-Source-Selection.md` |
| RAG-EXP-002 | 2 | Chuẩn bị registry, notebook cleaning/chunking, quy tắc chặn nguồn | Notebook v0.1 đã tạo, **chưa chạy** | `02_RAG_Document_Preparation.ipynb` |
| RAG-EXP-003 | 2 | Người dùng xác minh quyền, nhập tài liệu và chạy QA | **Chưa thực hiện** | Chờ `step2_preparation_report.json` |

**Nguyên tắc:** Chỉ ghi con số thực nghiệm thực tế khi người dùng gửi kết quả. Tài liệu đang ở trạng thái research-only, chưa được kiểm duyệt lâm sàng. Không đưa WHO/Long Châu vào Vector DB khi chưa có quyền hợp lệ.

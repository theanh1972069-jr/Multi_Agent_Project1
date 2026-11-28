# Giai đoạn 4 – Bước 5E: Kết quả Graph Retrieval thực tế

**Trạng thái:** Hoàn thành kiểm thử tích hợp kỹ thuật, do người dùng tự chạy trên máy và Neo4j Aura.  
**Nguồn bằng chứng:** `step5e_graph_retrieval_report.json` và ảnh kết quả Neo4j do người dùng cung cấp (2026-11-03).  
**Không có xác nhận lâm sàng hay kiểm định quyền sử dụng độc lập.**

## 1. Môi trường và đầu vào

- ChromaDB collection: `diabetes_kb_step3_e5small_v1`.
- Embedding: `intfloat/multilingual-e5-small`, truy xuất Top-3.
- Snapshot SHA256: `cc064ec7187192c999418051cb2125a0510412843f8d0908e3d6842e4a71c7cd`.
- ChromaDB records: **66**.
- Neo4j Aura chứa metadata `ChunkRef -> PART_OF -> SourceDocument -> COVERS_TOPIC -> Topic`.

## 2. Bảng kiểm tra kỹ thuật (đã chạy)

| Kiểm tra | Kết quả thực tế | Kết luận |
|---|---:|---|
| SourceDocument | 7 | Khớp |
| Topic | 6 | Khớp |
| COVERS_TOPIC | 7 | Khớp |
| ChunkRef | 66 | Khớp |
| PART_OF | 66 | Khớp |
| Orphan ChunkRef | 0 | Khớp |
| Approved MedicalClaim | 0 | An toàn theo thiết kế |
| Joined hits | 9 | 3 câu hỏi × Top-3 |
| Graph provenance matches | 9/9 | **PASS** |

### Phân bố theo nguồn

| Source ID | Số ChunkRef |
|---|---:|
| CDC-RISK-002 | 3 |
| CDC-T2D-001 | 4 |
| NIDDK-DIAG-003 | 19 |
| NIDDK-T2D-004 | 11 |
| WHO-DIAB-005 | 5 |
| LC-HBA1C-006 | 11 |
| LC-STAGES-007 | 13 |
| **Tổng** | **66** |

## 3. Kết quả truy xuất

- Q01: câu hỏi tiếng Việt về yếu tố liên quan đến tiểu đường type 2, Top-3 đều là mục của `LC-STAGES-007`. Kết nối metadata khớp, **không suy ra độ liên quan đã được cải thiện**.
- Q02: HbA1c tiếng Việt, các hit thuộc `LC-HBA1C-006` và `LC-STAGES-007`, đối chiếu nguồn thành công.
- Q03: yếu tố nguy cơ tiếng Anh, hit thuộc `NIDDK-T2D-004`, `NIDDK-DIAG-003` và `WHO-DIAB-005`, đối chiếu nguồn thành công.
- 9/9 hit mang `graph_provenance_match=true`, nhưng **0/9 được đánh dấu có thể dùng cho câu trả lời y khoa** (`eligible_for_medical_answer=false`).

## 4. Giới hạn / cổng an toàn

- **PASS chỉ cho kỹ thuật join giữa ChromaDB và Neo4j**, không phải đánh giá GraphRAG Answering.
- Quyền sử dụng/đánh giá y khoa chưa được xác minh độc lập. Flag `content_origin=licensed_source_text` trong metadata không phải giấy phép pháp lý.
- Evidence Gate 5A: citation OK 25/42, rights evidence yes 13/42, chưa có nguồn nào được kiểm tra độc lập; `ready_for_llm=false`.
- Neo4j đang chủ yếu lưu cấu trúc tài liệu/chủ đề, chưa có quan hệ y khoa đã duyệt.
- Index ChromaDB không sửa; Neo4j không sửa bởi chương trình 5E; không LLM, không ML train.

## 5. Quyết định

Đánh dấu **Bước 5E hoàn thành kỹ thuật**. Bắt đầu **Bước 5F: lập danh mục các MedicalClaim ứng viên với bằng chứng và quy trình kiểm duyệt**, chỉ tạo `draft_unverified`, không tạo quan hệ y khoa đã phê duyệt, không gọi LLM. Cần tiếp tục làm rõ giấy phép, citation và độ liên quan của Q01/Q05 trước khi Answering.

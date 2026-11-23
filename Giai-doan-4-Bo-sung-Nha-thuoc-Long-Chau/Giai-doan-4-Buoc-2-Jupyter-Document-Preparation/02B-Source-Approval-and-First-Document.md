# GIAI ĐOẠN 4 — BƯỚC 2B: RÀ SOÁT NGUỒN VÀ CHUẨN BỊ TÀI LIỆU ĐẦU TIÊN

**Dự án:** Multi-Agent AI System for Diabetes Risk Assessment  
**Ngày kiểm tra:** 2026-11-03  
**Loại công việc:** bổ sung vào Bước 2, **không phải Bước 3**  
**Trạng thái:** `awaiting_source_approval_and_licensed_text`

## 1. Báo cáo thực tế do người dùng chạy

- `experiment`: `EXP-RAG-DOC-STEP2-001`
- Tổng số nguồn registry: **7**.
- Nguồn đủ điều kiện nhập kho: **0**.
- Tệp văn bản đã được duyệt: **0**.
- Tài liệu được xử lý: **0**.
- Chunks được tạo: **0**.
- QA `PASS`: tất cả kiểm tra kỹ thuật trả `true`, nhưng tập chunks rỗng; **không coi là đã kiểm định được tài liệu**.
- Chưa tạo embeddings, chưa dùng Vector DB/LLM, chưa huấn luyện ML.
- Chunking cấu hình: `max_words=180`, `overlap_words=30`.

## 2. Nguyên nhân bị chặn

Bảy nguồn chưa thỏa các yêu cầu trong registry:

1. `approval_status = approved_research`.
2. `license_review_status = verified`.
3. `content_review_status = owner_reviewed_research_only`.
4. `reviewer`: người thực sự kiểm tra.
5. `source_retrieved_at_utc`: thời điểm UTC thực tế thu thập nội dung.

Việc `0 chunks` là đúng vì quy trình **không tự duyệt và không tự sao chép** các tài liệu chưa đủ điều kiện.

## 3. Tài liệu đầu tiên đề nghị xử lý

- `source_id`: `CDC-T2D-001`
- Trang gốc: https://www.cdc.gov/diabetes/about/about-type-2-diabetes.html
- Quyền sử dụng CDC: https://www.cdc.gov/Other/imagereuse.html
- Nguồn thay thế: `NIDDK-DIAG-003`, https://www.niddk.nih.gov/health-information/diabetes/overview/tests-diagnosis
- Chính sách NIDDK: https://www.niddk.nih.gov/copyright

Theo hướng dẫn chính thức, phần lớn nội dung do CDC/NIDDK tạo có thể được tái sử dụng; **vẫn phải rà soát riêng trang và đoạn nội dung**, loại trừ các tài sản của bên thứ ba. Ghi nguồn và tuyên bố không được cơ quan chứng thực; tránh logo/hình ảnh/sơ đồ có hạn chế. Việc phê duyệt trong registry **không thay thế thẩm định y khoa**.

WHO và hai nguồn Long Châu vẫn ở `reference_only`; **không thay đổi trạng thái** nếu chưa có quyền tái sử dụng riêng phù hợp.

## 4. Công việc người dùng tự thực hiện

### A. Rà soát một tài liệu

1. Mở URL CDC gốc và trang quyền sử dụng CDC.
2. Kiểm tra đúng trang, nguồn gốc đoạn văn muốn sử dụng, ngày cập nhật, ảnh/logo và tài liệu của bên thứ ba; rà soát độ phù hợp mục đích nghiên cứu cục bộ.
3. Chỉ chọn phần văn bản được phép và không có dữ liệu cá nhân, lời dẫn quảng cáo hoặc chỉ dẫn điều khiển LLM.
4. Ghi bằng chứng về quyền được sử dụng; nếu chưa chắc chắn về một đoạn thì không đưa đoạn đó vào file.

### B. Chuẩn bị file `.txt` (chỉ sau khi có quyền phù hợp)

Lưu đúng đường dẫn:

`04-Knowledge-Base-RAG/data/raw_approved/CDC-T2D-001.txt`

Mã hóa **UTF-8**, tối thiểu 25 từ, tối đa 150 KB. Giữ đúng nội dung tác giả; đặt tiêu đề phần bằng Markdown, ví dụ các tiêu đề `## Overview`, `## Risk factors` (tiêu đề minh họa, không phải nội dung được chép). Không tự dịch hay diễn giải lại nội dung khi chưa rà soát.

### C. Cập nhật `registry/source_registry.csv`

Chỉ sửa **dòng `CDC-T2D-001` sau khi đã tự hoàn tất rà soát và lưu file hợp lệ**:

| Trường | Giá trị cần ghi sau khi đã xác minh |
|---|---|
| `approval_status` | `approved_research` |
| `license_review_status` | `verified` |
| `license_evidence_url` | `https://www.cdc.gov/Other/imagereuse.html` và bằng chứng phù hợp khác nếu có |
| `content_review_status` | `owner_reviewed_research_only` |
| `reviewer` | Tên/người rà soát thực tế, không để trống |
| `source_retrieved_at_utc` | Ngày giờ UTC thật theo ISO 8601, ví dụ định dạng `YYYY-MM-DDTHH:MM:SS+00:00` |
| `document_version` | Giữ `v1` cho bản đầu tiên; tăng khi nội dung thay đổi |
| `source_updated_at` | Ngày cập nhật trên website nếu xác minh được |
| `review_notes` | Phạm vi được dùng, ngoại lệ, nguồn và cảnh báo không chứng thực |

Không tự điền thời gian giả hoặc đánh dấu `verified` chỉ vì URL là trang chính thức. Mở file CSV bằng công cụ hỗ trợ UTF-8 và kiểm tra các cột không bị lệch khi lưu. Các nguồn khác giữ nguyên.

### D. Chạy lại notebook gốc

Mở `notebooks/02_RAG_Document_Preparation.ipynb`. Chọn **Restart & Run All** sau khi đã lưu registry và `.txt`, để mọi ô dùng trạng thái mới; không chỉ chạy ô cuối.

Kết quả cần kiểm tra:

- `eligible_source_count >= 1`, `approved_text_file_count >= 1`.
- `documents_prepared >= 1`, `chunks_prepared > 0`.
- `status = prepared_for_embedding_review` và QA đều `true`.
- Kiểm tra thủ công 3–5 dòng trong JSONL có nội dung chính xác, section đúng, URL đúng và không lẫn menu/đường link của website.

**QA PASS tự động chưa đủ**: phải xác minh thực sự có chunks và nội dung phù hợp.

## 5. Báo cáo cần gửi lại

1. Output cuối `GIAI ĐOẠN 4 — BƯỚC 2: DOCUMENT PREPARATION`.
2. `data/outputs/document_preparation/step2_preparation_report.json` mới.
3. Số đoạn và vài metadata mẫu (`chunk_id`, `source_id`, `section`, `word_count`, `canonical_url`), không cần gửi toàn văn nếu có ràng buộc sử dụng.

**Điều kiện chuyển sang Bước 3:** Ít nhất một tài liệu thực sự có quyền sử dụng, được rà soát, tạo được chunks và vượt qua kiểm tra chất lượng. Chưa đủ thì tiếp tục Bước 2.

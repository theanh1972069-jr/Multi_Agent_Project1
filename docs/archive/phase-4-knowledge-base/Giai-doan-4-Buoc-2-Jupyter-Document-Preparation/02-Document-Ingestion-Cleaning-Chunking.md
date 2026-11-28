# GIAI ĐOẠN 4 — BƯỚC 2: THU THẬP, LÀM SẠCH VÀ CHIA CHUNK TÀI LIỆU Y KHOA

**Dự án:** Multi-Agent AI System for Diabetes Risk Assessment  
**Phiên bản:** v0.1 — 2026-11-03  
**Trạng thái:** Notebook và đặc tả đã chuẩn bị; **người dùng chưa chạy**. Chưa có tài liệu được chấp thuận nhập kho; chưa tạo embeddings/vector.  
**Liên kết:** `01-Knowledge-Source-Selection.md` và `00-Phase-4-Roadmap.md`.

## 1. Mục tiêu

- Quản lý **source registry** với 7 tài liệu ứng viên thuộc CDC, NIDDK, WHO, Long Châu.
- Chặn nguồn chưa được rà soát quyền sử dụng và nội dung.
- Làm sạch **văn bản UTF-8 do chính người thực hiện chuẩn bị hợp lệ**, giữ lại ngữ nghĩa y khoa.
- Chia đoạn theo tiêu đề và giới hạn số từ; theo dõi nguồn/tài liệu/phiên bản bằng metadata.
- Xuất `step2_chunks_review_only.jsonl` (chưa nhúng) và QA manifest.

## 2. Ranh giới quyền sử dụng và bảo vệ dữ liệu

| Nguồn | Trạng thái mặc định | Nguyên tắc |
|---|---|---|
| CDC | `candidate` | Kiểm tra quyền đối với từng trang, ưu tiên văn bản do chính CDC tạo; ghi nguồn và disclaimer, tránh hình/biểu đồ bên thứ ba. |
| NIDDK | `candidate` | Kiểm tra trang và nguồn gốc nội dung, ghi nguồn; không dùng logo/ảnh có bản quyền. |
| WHO | `reference_only` | Không nhập toàn văn nếu chưa chứng minh giấy phép phù hợp cho nội dung và mục đích dự án. |
| FPT Long Châu | `reference_only` | Không crawl/download/chunk/embed toàn văn khi chưa có quyền rõ ràng; chỉ giữ URL/tiêu đề/metadata tối thiểu. |

Các trang web công khai **không đồng nghĩa** với quyền tái sử dụng tự động. Giấy phép WHO còn phụ thuộc ấn phẩm, ngữ cảnh thương mại và tài liệu bên thứ ba. Không truy cập hoặc lưu thông tin sức khỏe của người dùng vào kho tri thức nghiên cứu.

**Chính sách nguồn:**
- https://www.cdc.gov/Other/imagereuse.html
- https://www.niddk.nih.gov/copyright
- https://www.who.int/about/policies/publishing/copyright
- https://nhathuoclongchau.com.vn/chinh-sach/tos

## 3. Đầu vào

`registry/source_registry.csv`: nguồn ứng viên với các trường `source_id`, `publisher`, `title`, `canonical_url`, `language`, `source_role`, `approval_status`, `license_review_status`, `license_evidence_url`, `content_review_status`, `reviewer`, `source_retrieved_at_utc`, `document_version`, `source_updated_at`, `review_notes`.

`data/raw_approved/<source_id>.txt`: **chỉ** chứa văn bản có quyền sử dụng và đã được người thực hiện rà soát; UTF-8; các đề mục bằng `##`. Tất cả nguồn đang mặc định **chưa được phê duyệt**.

## 4. Điều kiện thông qua nguồn (bắt buộc và thủ công)

- Người thực hiện đã xác minh quyền với trang cụ thể và mục đích nghiên cứu; sửa `license_review_status=verified` và ghi URL chứng minh (`license_evidence_url`).
- Người thực hiện đã rà soát tính phù hợp, loại ảnh/nội dung thứ ba, quảng cáo và lời khuyên cá nhân hóa; sửa `content_review_status=owner_reviewed_research_only` và ghi `reviewer`.
- Ghi đúng thời điểm **thực tế** lưu nội dung `source_retrieved_at_utc`, không tự điền thời điểm khác.
- Đặt `approval_status=approved_research`, `document_version` (bản này nghiên cứu cục bộ, **không phải** phê duyệt y khoa).
- Nội dung `.txt` không có mã hướng dẫn để chiếm quyền LLM, không chứa PII hoặc hồ sơ bệnh án.

Nếu một điều kiện không đạt: giữ `candidate` / `reference_only`, **không ingest**.

## 5. Clean & Chunking

- Chuẩn hóa Unicode NFC, khoảng trắng lặp, tab, số dòng trắng; không tự dịch hoặc viết lại nguồn.
- Tách tiêu đề `#`, `##`, `###`; không chia ngang qua ranh giới tiêu đề.
- Chia tối đa `180` từ/chunk; overlap `30` từ, theo khoảng trắng. Đây là tham số thử nghiệm, không phải token chính xác của embedding model.
- Không gộp các nguồn, không tự sinh nội dung y khoa, không đưa liên kết tham khảo vào JSONL như các đoạn văn giả.

## 6. Schema chunk

```json
{
  "chunk_id": "NIDDK-DIAG-003__v1__<sha10>__0001",
  "document_id": "NIDDK-DIAG-003",
  "source_id": "NIDDK-DIAG-003",
  "document_version": "v1",
  "publisher": "NIDDK",
  "title": "Diabetes Tests & Diagnosis",
  "canonical_url": "https://www.niddk.nih.gov/health-information/diabetes/overview/tests-diagnosis",
  "language": "en",
  "section": "<Tên mục trong văn bản>",
  "source_retrieved_at_utc": "<thời điểm được người dùng xác minh>",
  "approval_status": "approved_research",
  "document_sha256": "<sha256 của bản đã clean>",
  "chunk_sha256": "<sha256 của đoạn>",
  "word_count": 120,
  "text": "<Nội dung nguồn có quyền sử dụng>"
}
```

**Lưu ý:** Ví dụ trên chỉ mô tả schema; không phải tài liệu đã được duyệt hoặc một đoạn văn y khoa thật.

## 7. Kiểm tra chất lượng

| Tiêu chí | Kiểm tra |
|---|---|
| Đầu vào | File tồn tại, UTF-8 hợp lệ, có ít nhất 25 từ, không quá 150 KB |
| Bản quyền | Quyền đối với từng nguồn được xác minh và ghi bằng chứng |
| Truy xuất | Mỗi chunk có URL, source_id, version, section, hash |
| Độ dài | 1–180 từ, overlap theo cấu hình |
| Trùng ID | Không có `chunk_id` trùng |
| Bảo mật | Không chứa PII và không tự thực thi lệnh trong tài liệu |
| Y tế | Nội dung chỉ cho mục đích nghiên cứu; chưa xác thực lâm sàng |

**Lưu ý về prompt injection:** Bộ kiểm tra chuỗi trong notebook chỉ là cảnh báo kỹ thuật đơn giản, không chứng minh tài liệu an toàn; nội dung nguồn vẫn phải được xem như dữ liệu không đáng tin về mặt chỉ dẫn tác vụ.

## 8. Đầu ra do người dùng tạo khi chạy Notebook

- `data/processed/step2_chunks_review_only.jsonl`
- `data/outputs/document_preparation/step2_preparation_report.json`
- Kết quả ô cuối `GIAI ĐOẠN 4 — BƯỚC 2: DOCUMENT PREPARATION`

Nếu chưa có nguồn được duyệt: số chunks = 0, trạng thái `awaiting_source_approval_and_licensed_text`. Điều đó **không phải thất bại** của notebook, nhưng **chưa hoàn thành thu thập dữ liệu**.

## 9. Báo cáo thực nghiệm (chưa có dữ liệu thực thi)

| Chỉ số | Kết quả |
|---|---|
| Nguồn ứng viên | 7 (theo registry ban đầu) |
| Nguồn đã đủ điều kiện nhập | **Chờ người dùng chạy** |
| Tài liệu được nhập | **Chờ người dùng chạy** |
| Chunks hợp lệ | **Chờ người dùng chạy** |
| QA | **Chờ người dùng chạy** |
| Embedding | Chưa |
| Vector DB | Chưa |
| LLM | Chưa |

## 10. Điều kiện hoàn thành Bước 2

Ít nhất một tài liệu có quyền nhập, metadata đủ, chunk QA PASS; người dùng gửi output và báo cáo JSON để kiểm tra. Chỉ sau đó mới chuyển Bước 3 – Embedding và ChromaDB, người dùng tự chạy.

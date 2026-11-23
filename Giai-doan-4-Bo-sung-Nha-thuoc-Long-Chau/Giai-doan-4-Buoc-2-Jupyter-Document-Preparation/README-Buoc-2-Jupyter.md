# GIAI ĐOẠN 4 — BƯỚC 2: HƯỚNG DẪN JUPYTER

Bước này **có code để bạn tự chạy**. Tôi chưa chạy notebook và không ingest tài liệu thay bạn.

## 1. Cấu trúc thư mục

```text
04-Knowledge-Base-RAG/
├── 00-Phase-4-Roadmap.md
├── 01-Knowledge-Source-Selection.md
├── 02-Document-Ingestion-Cleaning-Chunking.md
├── 09-RAG-Experiment-Log.md
├── README-Buoc-2-Jupyter.md
├── registry/
│   └── source_registry.csv
├── notebooks/
│   └── 02_RAG_Document_Preparation.ipynb
└── data/
    ├── raw_approved/       # CHỈ tài liệu có quyền sử dụng
    ├── processed/
    └── outputs/document_preparation/
```

## 2. Thực hiện

1. Giải nén tệp ZIP vào thư mục dự án Giai đoạn 4; giữ lại registry đã chỉnh khi chạy lại.
2. Mở `notebooks/02_RAG_Document_Preparation.ipynb` trong Jupyter Notebook với Python 3.13.9. Không cần cài thư viện ngoài chuẩn Python.
3. Chạy từ đầu để xem danh mục 7 nguồn. Ban đầu sẽ có **0 nguồn đủ điều kiện**. Đây là hành vi chặn an toàn.
4. Truy cập từng bài CDC/NIDDK và kiểm tra quyền nội dung văn bản cụ thể. **Không tải hàng loạt**. Ghi bằng chứng quyền/ghi nguồn rõ. CDC yêu cầu ghi nguồn, disclaimer không có xác nhận của CDC; NIDDK ghi nguồn và không dùng logo.
5. **Sau khi** xác minh quyền và rà soát nội dung, chuẩn bị một file `.txt` UTF-8 thủ công, tên đúng `<source_id>.txt` (ví dụ `CDC-T2D-001.txt`) trong `data/raw_approved/`. Chỉ giữ nội dung văn bản có quyền sử dụng, với tiêu đề Markdown `##`; không đưa quảng cáo, menu, bảng bên thứ ba, logo, dữ liệu cá nhân.
6. Sửa đúng **một dòng tương ứng** trong `registry/source_registry.csv` để ghi bằng chứng và trạng thái phê duyệt nghiên cứu: `approval_status=approved_research`, `license_review_status=verified`, `content_review_status=owner_reviewed_research_only`, `reviewer`, `source_retrieved_at_utc`, `license_evidence_url`. Không coi đây là phê duyệt lâm sàng.
7. WHO/Long Châu **chỉ là tham khảo** nếu chưa có giấy phép phù hợp, không copy toàn văn/chunk/embed. Giữ `reference_only`.
8. Chạy lại toàn bộ notebook để xuất `step2_chunks_review_only.jsonl` và `step2_preparation_report.json`.
9. Gửi output ô cuối + JSON report cho tôi. Không cần gửi toàn bộ văn bản nguồn nếu quyền hạn chế.

## 3. Vì sao không tự động scrape?

Chúng ta cần xác định quyền dùng **theo từng tài liệu**, đảm bảo trích dẫn và tránh nhập nhầm nội dung trang điều hướng, sản phẩm hoặc quảng cáo. Tài liệu chưa được phê duyệt phải bị chặn trước khi tạo embeddings. Việc tự tải/cào hàng loạt khi chưa kiểm tra quyền sử dụng làm mất khả năng kiểm soát nguồn và có thể vi phạm điều khoản.

## 4. Phân biệt source và phiên bản

`source_id`: mã nguồn không đổi; `document_version`: đổi khi nội dung được kiểm duyệt và cập nhật; `document_sha256`: hash nội dung làm sạch; `chunk_id`: chứa mã nguồn, phiên bản, hash đầu và thứ tự. Không chỉnh sửa phần nội dung y khoa chỉ để tăng số chunks.

## 5. Không nên làm ở bước này

- Không gọi LLM, tạo embedding, ChromaDB hoặc Neo4j.
- Không train lại mô hình NHANES, đổi ngưỡng 0.225 hay mở lại Test.
- Không đưa lời khuyên điều trị cá nhân hoặc nội dung Long Châu chưa được phép vào corpus.
- Không coi kết quả QA kỹ thuật tương đương xác thực y khoa.

## 6. Ghi nhận tiến độ

Chạy lần đầu khi registry chưa duyệt sẽ hiển thị `0 eligible / 0 chunks`. Đây là hành vi mặc định **đúng**. Sau đó tự rà soát quyền, nhập tối thiểu một tài liệu có phép để kiểm thử parser; mục tiêu corpus ban đầu là 3–5 tài liệu đa chủ đề có nguồn rõ ràng trước khi chuyển bước Embeddings. Nếu không thể xác minh quyền sử dụng, tiếp tục giữ nguồn dưới dạng liên kết tham khảo.

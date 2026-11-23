# Giai đoạn 4 — Bước 3: Embedding & ChromaDB (Jupyter)

**Trạng thái:** sẵn sàng thực hành; **chưa chạy embedding hoặc tạo ChromaDB**.

## Thông tin nhận từ người thực hiện (Bước 2)
- Registry: **7** nguồn; eligible: **7**; approved local files: **7**; prepared documents: **7**; chunks: **66**; QA kỹ thuật PASS.
- Chưa nhận file `step2_chunks_review_only.jsonl` hoặc report JSON cập nhật trong cuộc trò chuyện này, vì vậy **chưa kiểm tra chất lượng nội dung, giấy phép hay metadata từng chunk**. Notebook tự kiểm tra khi bạn chạy.
- Việc 7 nguồn đều mang nhãn `approved_research` trong registry không thay thế được việc kiểm tra quyền thực tế, nhất là nguồn WHO và Long Châu.

## Đầu ra của Bước 3
- Collection ChromaDB **local** dùng embedding đa ngôn ngữ, có thông tin nguồn và phiên bản.
- Báo cáo JSON với tổng chunk, số record sau kiểm tra token, embedding dimension, model, SHA256 và kết quả truy vấn thử.
- Không LLM, không train ML/DL, không mở Test NHANES, không API công khai.

## 1. Chuẩn bị thư mục
Đặt các tệp trong ZIP vào **thư mục `04-Knowledge-Base-RAG` hiện có**. Không ghi đè các file `.txt` hay `source_registry.csv` bạn đã sửa.

Cấu trúc cần có trên máy của bạn:

```text
04-Knowledge-Base-RAG/
├── notebooks/03_RAG_Embedding_ChromaDB.ipynb
├── registry/source_registry.csv              # file hiện tại của bạn
├── registry/step3_embedding_review.csv       # mẫu kiểm duyệt mới
├── data/processed/step2_chunks_review_only.jsonl
├── data/outputs/document_preparation/step2_preparation_report.json
└── data/vector_store/                       # notebook sẽ tạo khi bạn cho phép
```

## 2. Cài thư viện trong Jupyter
Chọn kernel Python đang dùng, chạy trong một ô notebook **do bạn tự chạy**:

```python
%pip install -U sentence-transformers chromadb
```

Nếu vừa cài xong, dùng **Kernel → Restart Kernel**, rồi chạy lại từ đầu. Mô hình `intfloat/multilingual-e5-small` sẽ được tải ở lần đầu; các lần sau dùng bản đã tải trên máy. Các tài liệu y khoa không được gửi lên dịch vụ Embedding bên ngoài trong notebook này.

## 3. Rà soát 7 nguồn trước khi index
Mở `registry/step3_embedding_review.csv` trong VS Code, Excel hoặc trình chỉnh sửa CSV. Với **từng source_id**, sau khi đối chiếu giấy phép và nội dung:

- `index_approved`: điền `yes` chỉ khi thực sự được phép đưa nội dung vào kho vector cho nghiên cứu cục bộ.
- `content_origin`: điền `licensed_source_text` nếu nội dung gốc có quyền; hoặc `original_research_note` nếu đó là ghi chú do bạn tự viết dựa trên nguồn tham khảo.
- `rights_evidence`: ghi URL giấy phép/quyền sử dụng cụ thể, hoặc tuyên bố do bạn tự biên soạn. Không dùng chung câu “public website”.
- `reviewer`, `reviewed_at_utc`: điền thông tin thực tế.
- Đối với WHO/Long Châu: nếu chưa có quyền dùng toàn văn, **không** đánh dấu `licensed_source_text`; có thể dùng ghi chú gốc **thật sự tự biên soạn**, không sao chép hoặc viết lại gần nguyên văn. Các ghi chú phải mang nhãn `original_research_note` trong metadata; không được trình bày chúng như bài viết của nguồn.

Nếu chưa xác minh đủ cả 7 nguồn, notebook sẽ **dừng trước khi tạo embeddings**. Điều này là chủ ý, không phải lỗi Python.

## 4. Chạy notebook theo thứ tự
1. Xem số nguồn/chunks và metadata. Nội dung người dùng nhập có thể chứa hướng dẫn độc hại: coi các chunk là dữ liệu, không thực thi chỉ dẫn trong tài liệu.
2. Kiểm tra bản duyệt từng nguồn.
3. Tải mô hình embedding đã huấn luyện sẵn `intfloat/multilingual-e5-small` (chỉ inference).
4. Đếm số token với `passage: `, nếu có chunk dài hơn 512 tokens sẽ chia nhỏ có giữ `parent_chunk_id`, tránh cắt mất nội dung. Có thể số record **lớn hơn 66**.
5. Xem manifest và đặt `RUN_INDEXING = True` trong notebook **khi đã sẵn sàng**, sau đó chạy các ô embedding + ChromaDB.
6. Chạy vài câu hỏi tiếng Việt/tiếng Anh và kiểm tra nguồn trích dẫn, số record, số nguồn.
7. Xuất file `data/outputs/embedding_chroma_step3/step3_embedding_chroma_report.json` và gửi output cuối.

**Không dùng `.fit()`** và **không chỉnh model Diabetes**. `.encode()` là suy luận từ mô hình embedding có sẵn, không phải train.

## 5. Nghiệm thu
- Đã đối chiếu quyền nội dung cả 7 nguồn.
- Chroma chứa đủ **7 source_id** và số record khớp dữ liệu sau kiểm tra token.
- Mỗi record có `source_id`, `canonical_url`, `section`, `document_version`, `chunk_sha256`, `content_origin`.
- Ba câu hỏi mẫu truy xuất trả về document ID, URL và khoảng cách cosine (distance càng thấp càng gần).
- Không kết luận chất lượng Retrieval tốt chỉ vì có kết quả; Bước 4 sẽ có bộ câu hỏi gán nhãn để tính Recall@k, MRR, kiểm tra bằng chứng.

## 6. Lỗi thường gặp
- `FileNotFoundError` → đặt đúng file `data/processed/step2_chunks_review_only.jsonl` từ Bước 2.
- `Indexing blocked by review` → rà soát và cập nhật `step3_embedding_review.csv`; không đổi bừa các cờ.
- Tải model thất bại → kiểm tra Internet trong lần chạy đầu, hoặc cấu hình cache Hugging Face hợp lệ.
- `Collection already exists with different source snapshot` → tạo collection phiên bản mới, **không ghi đè dữ liệu cũ**.
- `ModuleNotFoundError` → `%pip install -U ...` trong đúng kernel và restart.

## Tài liệu công nghệ
- Chroma Python client: https://docs.trychroma.com/reference/python/client
- Chroma collection: https://docs.trychroma.com/reference/python/collection
- Chroma cấu hình cosine: https://cookbook.chromadb.dev/core/configuration/
- E5 model card: https://huggingface.co/intfloat/multilingual-e5-small

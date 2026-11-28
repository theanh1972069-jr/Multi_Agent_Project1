# Giai đoạn 5 – Bước 3: Chẩn đoán `BACKEND_UNAVAILABLE`

## Vì sao gặp lỗi?

Trong phiên bản hiện tại, `LiveKnowledgeBackend` đổi nhiều lỗi từ ChromaDB, Neo4j hoặc embedding thành cùng một mã `BACKEND_UNAVAILABLE`. Mã này **không chứng minh mật khẩu Neo4j sai**. Bộ kiểm tra mới chia thành các giai đoạn độc lập và không in mật khẩu, URI đầy đủ hay nội dung tài liệu y khoa.

## Cách dùng

1. Giải nén ZIP vào **thư mục cha** đang chứa `05-Multi-Agent-Integration`, chỉ thêm file `phase5/step3_diagnose.py`, không ghi đè config.
2. Trong VS Code/PowerShell mở thư mục `05-Multi-Agent-Integration` (nơi có `phase5/` và `config/`).
3. Chạy:

   ```powershell
   python -m phase5.step3_diagnose
   ```

4. Nhập mật khẩu Neo4j ở dấu nhắc ẩn. Gửi **chỉ phần output trạng thái** hoặc file JSON `data/outputs/phase5_step3/step3_backend_diagnostic.json`. Không gửi mật khẩu và không gửi cấu hình có bí mật.

## Cách đọc kết quả

| Bước kiểm tra | PASS có nghĩa là | FAIL thường liên quan tới |
|---|---|---|
| `CONFIG` | JSON chứa cấu hình hợp lệ | File config sai hoặc thiếu |
| `CHROMA_FILES` | Có `chroma.sqlite3` | Đường dẫn trỏ nhầm thư mục |
| `CHROMA_COLLECTION` | Mở được collection, đúng 66 records và metadata | ChromaDB phiên bản khác, collection sai hoặc snapshot bị thay |
| `NEO4J_CONNECT` | Đăng nhập và bắt tay TLS tới Aura được | Mật khẩu, URI, mạng, instance dừng, SSL |
| `NEO4J_AUDIT` | Có thể truy vấn và số lượng graph đúng | Sai database, thiếu quyền đọc, graph thay đổi |
| `EMBEDDING_LOCAL_CACHE` | Model `intfloat/multilingual-e5-small` tải offline từ cache được | Chưa cache model trong môi trường Python hiện tại hoặc thiếu weights/library |

Nếu `EMBEDDING_LOCAL_CACHE: FAIL_LOAD`, đừng vội xóa hay tải lại ChromaDB. Trước hết so sánh Python environment và cache Hugging Face của Giai đoạn 4/5. Báo cáo Giai đoạn 4 ghi nhận `sentence-transformers==6.2.0`, trong khi requirements Bước 3 giới hạn `<6`, nên phiên bản có thể khác. Không thay đổi phiên bản trước khi xác định lỗi cụ thể.

## Đảm bảo phạm vi kiểm tra

- Không tạo câu trả lời y khoa, không gọi LLM, không train lại ML.
- Chỉ gửi truy vấn `READ` tới Neo4j, không thay đổi claim hoặc relation.
- ChromaDB PersistentClient có thể tự tạo tệp housekeeping; nên sao lưu data và có quyền truy cập phù hợp. Nếu không tồn tại `chroma.sqlite3`, công cụ **không** khởi tạo ChromaDB tại đường dẫn đó.
- Chương trình tạo một file báo cáo JSON mới trong thư mục `data/outputs`.

Sau khi xác định và khắc phục đúng lỗi, chạy lại `python -m phase5.step3_run --mode live` để lấy kết quả thực tế Bước 3.

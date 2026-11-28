# GIAI ĐOẠN 5 — BƯỚC 1: TEST MATRIX & EVIDENCE LOG TEMPLATE

**Trạng thái:** Chuẩn bị để **người dùng tự chạy**, chưa có kết quả thực nghiệm Windows.

## 1. Contract self-test (14 cases)

| ID | Mục tiêu | Kỳ vọng |
|---|---|---|
| 01 | NHANES input giả lập hợp lệ | Chấp nhận |
| 02 | Tuổi ngoài miền NHANES | ValidationError |
| 03 | RIAGENDR mã sai | ValidationError |
| 04 | BMI ngoài miền | ValidationError |
| 05 | Client cố truyền `knowledge_gate` | Từ chối extra field |
| 06 | Trộn input giữa hai mode | Từ chối |
| 07 | `synthetic_test_only=false` | Từ chối |
| 08 | Research gate khởi tạo mặc định | `BLOCKED_RESEARCH_ONLY` |
| 09 | Atlas input độc lập | `NOT_EVALUATED`, không mang features |
| 10 | Research mode cố gọi LLM/vượt gate | ValidationError |
| 11 | Metadata có full-text chưa duyệt | ValidationError |
| 12 | Upstream model SHA mismatch | ValidationError |
| 13 | Score/label không nhất quán | ValidationError |
| 14 | Chưa kết nối mà chứa score dự đoán | ValidationError |

Các test này là **kiểm thử hợp đồng nội bộ**. Không phải penetration testing, quyền truy cập dịch vụ hoặc đánh giá an toàn y khoa.

## 2. Audit matrix

| Check | Dữ liệu kiểm tra | Ý nghĩa |
|---|---|---|
| `model_artifact` | File path + SHA256 đọc bytes | Khớp artifact Giai đoạn 3, không load model |
| `prediction_api_config` | localhost + route | Format hợp lệ; **không chứng minh API chạy** |
| `chroma_directory` | Path.is_dir | Thư mục tồn tại; **không kiểm chứng 66 records** |
| `chroma_collection_config` | Tên collection | Khớp hằng số thiết kế |
| `neo4j_uri_config` | URI dạng `neo4j+s`/`bolt+s` | Format, **không login** |
| `neo4j_database_config` | Có giá trị | Config, **không query** |
| `ollama_config` | localhost URL | Config, **không gọi model** |

## 3. Kết quả thực tế

Chỉ cập nhật sau khi nhận kết quả thực hành. Đừng điền sẵn 14/14 cho máy người dùng.

```text
Self-test: CHƯA CÓ KẾT QUẢ TỪ MÁY NGƯỜI DÙNG
Graph skeleton: CHƯA CÓ KẾT QUẢ TỪ MÁY NGƯỜI DÙNG
Environment audit: CHƯA CÓ KẾT QUẢ TỪ MÁY NGƯỜI DÙNG
Medical gate expected: BLOCKED_RESEARCH_ONLY
Model threshold: 0.225, frozen
```

# GIAI ĐOẠN 6 — BƯỚC 1: CLIENT API CONTRACT & UX SAFETY AUDIT

**Trạng thái:** Kế hoạch chuẩn bị, **người dùng chưa chạy**. Không phải bản ghi kết quả.

## 1. Cần kiểm tra trước khi xây UI

- Server `phase5.step5_api --mode mock --port 8001` chỉ chạy trên `127.0.0.1`.
- `GET /openapi.json` cung cấp schema thực tế.
- `GET /health/live`: status `alive`, `mode=mock`.
- `GET /health/ready`: `graph_compiled_backends_not_probed` (không khẳng định downstream backend sống).
- `POST /api/v1/research/agents/run` phải có contract 3 operation.
- Client không truyền `medical_gate`; server chỉ chấp nhận `synthetic_test_only=true`.

## 2. Trình tự trên Windows PowerShell

Mở terminal A trong `05-Multi-Agent-Integration`:

```powershell
python -m phase5.step5_api --mode mock --port 8001
```

Mở terminal B:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health/live
Invoke-RestMethod http://127.0.0.1:8001/health/ready
(Invoke-RestMethod http://127.0.0.1:8001/openapi.json).paths.PSObject.Properties.Name
```

Kỳ vọng: ba route `/health/live`, `/health/ready`, `/api/v1/research/agents/run`. Chưa cần chạy model hay Neo4j.

## 3. UX contract theo trạng thái

| Operation | Trạng thái có thể thấy | UI cần làm |
|---|---|---|
| `research_prediction` | `ok`, `failed` | Nhãn nghiên cứu; giải thích chỉ báo HbA1c, tuyệt đối không nói là chẩn đoán |
| `knowledge_research_lookup` | `blocked_research_only`, `failed` | Hiển thị rõ “chưa được phép tạo tư vấn y khoa”, chỉ metadata nguồn |
| `synthetic_rag_demo` | `mock_response_not_llm`, `llm_output_needs_human_review`, `abstained`, `failed` | Nhãn dữ liệu Atlas hư cấu; citation và trạng thái xác nhận |
| Validation | HTTP 422 | Thông báo field sai, không render traceback / secrets |
| Backend unavailable | Connection error | Thông báo kết nối lỗi; không thay bằng câu trả lời bịa |

## 4. Các quyết định còn mở

- Cách tích hợp React dev server gọi backend: same-origin dev proxy hoặc whitelist CORS `http://localhost:5173` (đúng origin thực tế, không wildcard credentials).
- Hiển thị 3 chức năng qua tab riêng trên Web, rồi tái sử dụng contract ở Mobile.
- Framework Mobile chọn ở Bước 4: Flutter vs Android native Kotlin (chưa chốt).

## 5. Tiêu chí kết thúc Bước 1

1. Có OpenAPI bản thực tế và danh sách request/response schema từ server local.
2. Thống nhất UI mapping cho `ok`, `blocked_research_only`, `abstained`, `failed`, lỗi HTTP 422 và lỗi kết nối.
3. Không gọi model, không bật tư vấn y khoa, không public server.
4. Có báo cáo kết quả do người dùng tự chạy; không mô tả mock là live.

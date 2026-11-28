# Giai đoạn 5 · Bước 2 — Kết quả kiểm thử Live

**Nguồn:** `step2_prediction_integration_report.json` do người dùng chạy và gửi lúc 2026-11-03; `experiment=EXP-PHASE5-STEP2-001`. Không suy diễn từ mock thành kết quả thật.

| Chỉ số | Kết quả đã ghi nhận |
|---|---|
| Chế độ | `live` |
| Kết quả | `2/2` |
| `SYN-PRED-01` | `ok`, `prediction_present=true`, `model_sha256_match=true`, `threshold_match=true`, không có `error_codes` |
| `SYN-PRED-02` | `ok`, `prediction_present=true`, `model_sha256_match=true`, `threshold_match=true`, không có `error_codes` |
| Trạng thái | `local_prediction_api_checked` |
| Gate | `BLOCKED_RESEARCH_ONLY` |
| Mạng | `localhost_API_only` |
| LLM / ChromaDB / Neo4j / DB writes / ML training | Không trong lần chạy này |

**Đánh giá:** Đã đạt nghiệm thu *kết nối Data Analysis → Prediction → FastAPI localhost* qua hai bộ dữ liệu giả lập, không train lại. Báo cáo này không chứa giá trị score thô, vì vậy không thể độc lập kiểm toán phép tính xác suất chỉ từ JSON. Đây là phân loại chỉ báo HbA1c ≥5,7% tại thời điểm khảo sát, **không phải chẩn đoán hay tiên lượng nguy cơ mắc tiểu đường type 2 tương lai**. Chưa có kết quả người dùng cung cấp cho lệnh `step1_self_test`, nên không đưa ra nhận định rằng chúng đã chạy thành công trên máy người dùng.

**Bước tiếp theo:** Bước 3 – Knowledge Agent Integration, đọc ChromaDB và Neo4j; không mở khóa khả năng trả lời y khoa.

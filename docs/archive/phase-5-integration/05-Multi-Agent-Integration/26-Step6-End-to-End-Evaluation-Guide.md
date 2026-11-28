# Giai đoạn 5 – Bước 6: End-to-End Evaluation & Final Report

**Phạm vi:** Nguyên mẫu nghiên cứu nội bộ, dùng dữ liệu giả lập; không chẩn đoán, không tư vấn điều chỉnh thuốc, không công khai dịch vụ trên Internet. Bước 6 **không** huấn luyện lại mô hình và không ghi ChromaDB/Neo4j.

## 1. Đã đạt và còn thiếu

- Bước 2: `live`, Prediction API 2/2, đúng hash, ngưỡng 0.225.
- Bước 3: `live`, ChromaDB + Neo4j, 9/9 provenance, 0 approved claims.
- Bước 4: Ollama thật (riêng Consultation Agent), preflight 6/6, 3 ca từ chối trước LLM; ba câu trả lời Atlas cần người dùng duyệt nội dung.
- Bước 5: `live + consultation mock`, LangGraph 11/11; **chưa thử Ollama bên trong Orchestrator**.
- Bước 6: cần kiểm tra **FastAPI :8001**, kiểm duyệt câu trả lời S01–S03 và tổng hợp các báo cáo.

## 2. Chuẩn bị tệp

Giải nén ZIP vào thư mục cha có `05-Multi-Agent-Integration`, hợp nhất file mới vào đúng thư mục. **Không ghi đè** `config/phase5_step1_config.json` hoặc các báo cáo đầu ra đã tạo. Nếu từng làm bảng review riêng, hãy sao lưu trước khi ghi đè CSV.

Đảm bảo trong `05-Multi-Agent-Integration` có các báo cáo gốc:

```text
data/outputs/phase5_step2/step2_prediction_integration_report.json
data/outputs/phase5_step3/step3_knowledge_integration_report.json
data/outputs/phase5_step4/step4_consultation_report.json
data/outputs/phase5_step5/step5_orchestrator_report.json
```

**Không** tạo mới số liệu giả. Nếu thiếu tệp, tìm kết quả từng bước đã chạy trên máy rồi sao chép về đúng vị trí. Báo cáo Step5 hiện cần là bản `live | consultation mock | 11/11`.

## 3. Chạy unit test của bộ đánh giá (không cần mạng)

Trong PowerShell, tại `05-Multi-Agent-Integration`:

```powershell
python -m phase5.step6_self_test
```

**Mục tiêu:** `Ran 15 tests`, `OK` (đây là bài kiểm thử logic của script mới, không phải đo lại 11 ca LangGraph).

## 4. Kiểm thử FastAPI tích hợp ở localhost:8001

Chạy **terminal A** ở cùng thư mục (mặc định mock; không cần FastAPI cổng 8000, Neo4j hay Ollama):

```powershell
python -m phase5.step5_api --mode mock --port 8001
```

**Không đóng terminal A**. Trong **terminal B**, chạy:

```powershell
python -m phase5.step6_http_smoke
```

Chương trình chỉ cho phép URL `http://127.0.0.1:<port>` hoặc `http://localhost:<port>` và tự gọi 8 ca:

1. `GET /health/live` (trả `200`, `mode=mock`).
2. `GET /health/ready` (trả trạng thái `graph_compiled_backends_not_probed`, **không phải kiểm tra dịch vụ backend**).
3. `POST research_prediction` với dữ liệu giả lập (trả `200`, mô hình **mock**).
4. `POST knowledge_research_lookup`, `Q01` (trả `200`, gate blocked).
5. `POST synthetic_rag_demo`, `S01` (trả `200`, không gọi LLM).
6. `POST synthetic_rag_demo`, `S06` (trả `200`, abstained).
7. Gửi `medical_gate` do client tự đặt (phải bị HTTP `422` từ chối).
8. Gửi `Q99` không nằm trong whitelist (phải bị HTTP `422` từ chối).

**Mục tiêu:** `Checks: 8/8 | Status: api_mock_smoke_pass`. Báo cáo sinh ra tại `data/outputs/phase5_step6/step6_http_smoke_report.json`. Sau kiểm tra, có thể nhấn `Ctrl+C` ở terminal A để tắt server.

> Tại sao dùng `mock`? Chúng ta đã kiểm tra backend thật qua Orchestrator 11/11 trước đó. Bước HTTP nhằm kiểm tra route/schema/response, không thêm rủi ro truy cập data thật qua server chưa có authentication.

## 5. Đánh giá S01–S03 (CSV đã có sẵn câu hỏi, nguồn và câu trả lời)

Mở `registry/step6_consultation_manual_review.csv` trong VS Code hoặc Excel. **Không phải CSV trống:** mỗi dòng đã có `question`, `source_text`, `llm_answer`, `citation_id` và `suggested_observation`.

So sánh `llm_answer` với `source_text` trên **cùng dòng**:

| Case | Điểm cần chú ý | Nhận xét sơ bộ (không phải phê duyệt sẵn) |
|---|---|---|
| S01 | Atlas có 3 mô-đun gì? | Nội dung đủ, ngữ pháp hơi cụt |
| S02 | Có nhập dữ liệu cá nhân thật không? | “Không được” đúng nhưng quá ngắn |
| S03 | Không tìm thấy bằng chứng xử lý sao? | Từ chối và yêu cầu tài liệu, đúng ý |

Sau khi **tự kiểm tra và đồng ý**, nhập `yes`, `yes`, `no` vào:

- `answer_fully_supported_yes_no`
- `citation_correct_yes_no`
- `unsupported_claim_found_yes_no`

Điền `reviewer` bằng định danh người thực sự rà soát và `reviewed_at_utc` bằng thời gian **UTC thật**. Để lấy UTC bằng PowerShell:

```powershell
[DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
```

Nếu phát hiện lỗi nội dung, điền sự thật (ví dụ `no` hoặc `yes` tại cột unsupported), không ép trạng thái pass. Trường `suggested_observation` chỉ là gợi ý; có thể sửa `notes`.

## 6. Chạy báo cáo tổng hợp Bước 6 (offline)

```powershell
python -m phase5.step6_e2e_audit --project-root .
```

Script đối chiếu bốn báo cáo Bước 2–5, báo cáo HTTP và CSV review. **Không gọi API, không tải model, không kết nối Neo4j, không gọi LLM.**

**Mục tiêu khi hoàn tất:**

```text
step2_live_prediction: PASS
step3_live_knowledge: PASS
step4_ollama_synthetic: PASS
step5_live_mock_consultation: PASS
step6_http_mock: PASS
Manual Atlas review: pass (3/3)
Status: phase5_research_sandbox_ready_to_close_with_limitations
```

Báo cáo tại: `data/outputs/phase5_step6/step6_phase5_e2e_report.json`.

Nếu không đủ điều kiện (thiếu review, HTTP hoặc báo cáo cũ), lệnh trả exit code 1 để không báo nghiệm thu nhầm. Script **không sửa** báo cáo của các bước trước.

## 7. Tùy chọn (mở rộng phạm vi): Ollama trong Orchestrator Live

Bạn đã chạy Ollama thật ở Step4 nhưng chưa chạy trong Step5. Khi muốn kiểm tra toàn bộ đường đi Orchestrator → Consultation → Ollama (Atlas giả lập), khởi động lại FastAPI Giai đoạn 3 ở cổng 8000, chuẩn bị Neo4j và Ollama, rồi chạy:

```powershell
python -m phase5.step5_run --mode live --consultation ollama --model qwen2.5:1.5b --output .\data\outputs\phase5_step5\step5_orchestrator_ollama_report.json
```

**Quan trọng:** `--output` tách biệt giúp **không ghi đè báo cáo Step5 live + mock 11/11**. Nếu chạy đạt, có thể thêm kết quả vào Step6:

```powershell
python -m phase5.step6_e2e_audit --project-root . --step5-ollama-report .\data\outputs\phase5_step5\step5_orchestrator_ollama_report.json
```

Mục tiêu: `orchestrator_live_technical_pass_manual_review_pending`, 11/11; LLM chỉ gọi S01–S03. Báo cáo này chỉ lưu metadata, **không lưu text Ollama**, nên cần kiểm tra nội dung thủ công riêng nếu tuyên bố LLM trả lời chính xác trong Orchestrator.

## 8. Tiêu chí nghiệm thu và giới hạn

- Được phép chốt **nguyên mẫu nghiên cứu** nếu 4 báo cáo bước trước khớp, HTTP mock 8/8 và người dùng xác nhận Atlas 3/3.
- Không suy ra hệ thống đã được phê duyệt y khoa/bản quyền; 7 nguồn thật vẫn nghiên cứu và `BLOCKED_RESEARCH_ONLY`.
- Không tuyên bố kiểm thử xâm nhập, authorization, load/performance hoặc bảo mật production.
- Model NHANES phân loại chỉ báo HbA1c ≥ 5,7%, **không** ước lượng khả năng mắc tiểu đường trong tương lai.
- Giữ service FastAPI trên `127.0.0.1`; chưa có authentication/tenant isolation đủ để public.
- Không đưa mật khẩu Neo4j, API key hoặc hồ sơ sức khỏe thật vào CSV, report hay cuộc trò chuyện.

**Gửi lại:** (1) output `step6_http_smoke`, (2) output `step6_e2e_audit`, (3) file `step6_phase5_e2e_report.json`. Khi đủ điều kiện, sẽ viết báo cáo kết thúc Giai đoạn 5.

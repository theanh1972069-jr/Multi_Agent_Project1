# Giai đoạn 5 – Bước 5: Orchestrator + FastAPI Workflow

## Mục tiêu

Tích hợp năm **loại** Agent vào một LangGraph có định tuyến theo ba nghiệp vụ nghiên cứu độc lập, kèm FastAPI localhost để thử nghiệm giao tiếp. **Không** phải năm Agent đều được gọi trong mỗi yêu cầu; điều phối chỉ chạy node cần thiết.

```mermaid
flowchart TD
    A[FastAPI localhost:8001] --> O[Orchestrator Agent]
    O -->|research_prediction| D[Data Analysis Agent]
    D --> P[Prediction Agent]
    P --> C[Consultation Agent: formatter only]
    O -->|knowledge_research_lookup| K[Knowledge Agent: Chroma+Neo4j metadata]
    O -->|synthetic_rag_demo| K
    K --> C
    C --> Z[Strict response]
    P -. local only .-> B[Phase 3 FastAPI:8000]
    K -. fixed Q01..Q03; read only .-> M[ChromaDB + Neo4j]
    C -. S01..S03 only .-> L[Ollama synthetic Atlas]
```

**Cách ly luồng:**
1. `research_prediction`: chỉ với đầu vào dữ liệu tổng hợp `RIDAGEYR`, `RIAGENDR`, `BMXBMI`; gọi model hiện có trên FastAPI 8000 khi `live`; **không truy xuất y khoa và không gọi LLM**.
2. `knowledge_research_lookup`: chỉ nhận query ID `Q01`, `Q02`, `Q03` cố định. Khi `live`, đọc metadata ChromaDB + Neo4j và xuất tối đa 3 metadata/ID, tất cả `allowed_to_answer=false` và `medical_gate=BLOCKED_RESEARCH_ONLY`; **không gửi văn bản y khoa tới LLM**.
3. `synthetic_rag_demo`: chỉ nhận case ID `S01..S06`, kiểm tra file Atlas giả lập được khóa nội dung. `S01..S03` được phép gọi Ollama khi chủ động bật chế độ, `S04..S06` từ chối. **Không gọi prediction hoặc clinical KB**.

Cùng một graph có năm node: `orchestrator_agent`, `data_analysis_agent`, `prediction_agent`, `knowledge_agent`, `consultation_agent`. Định tuyến bằng `add_conditional_edges`. Agent outputs tuân hợp đồng Pydantic; user không được đặt `medical_gate`.

## File mới

- `phase5/step5_orchestrator.py`: hợp đồng `Step5Request`, `Step5Response`, LangGraph năm node, fail-closed.
- `phase5/step5_runtime.py`: khởi tạo backend mock hoặc live có chủ ý.
- `phase5/step5_run.py`: 11 smoke cases cố định và báo cáo JSON không chứa text y khoa.
- `phase5/step5_api.py`: FastAPI localhost `POST /api/v1/research/agents/run`; health endpoints.
- `phase5/step5_self_test.py`: unit + graph smoke tests.
- `requirements-step5.txt`: các thư viện tối thiểu cho graph và API.

**Yêu cầu nền:** thư mục `05-Multi-Agent-Integration` từ Bước 1–4 của bạn phải còn các file `contracts.py`, `step2_prediction_integration.py`, `step3_knowledge_integration.py`, `step4_consultation.py` và `data/sandbox/step4_atlas_synthetic.json`.

## Hướng dẫn trên Windows VS Code

Giải nén ZIP vào **thư mục cha của `05-Multi-Agent-Integration`**, hợp nhất tệp mới, không xóa cấu hình `config/phase5_step1_config.json`.

### 1. Cài thư viện (terminal trong `05-Multi-Agent-Integration`)

```powershell
python -m pip install -r .\requirements-step5.txt
python -m phase5.step5_self_test
```

Mục tiêu kiểm thử: `Ran 21 tests`, `OK`, không có skipped nếu đã cài `langgraph`. Nếu còn `skipped=5`, hãy kiểm tra `python -m pip show langgraph` và interpreter đang dùng.

### 2. Chạy điều phối giả lập trước

```powershell
python -m phase5.step5_run --mode mock
```

Mục tiêu: `Cases: 11/11`; `Status: orchestrator_mock_technical_pass`. **Các mock scores không phải dự đoán của mô hình.**

### 3. Chạy Live trên backend bạn đã kiểm tra ở Bước 2 và Bước 3

- Terminal riêng tại Giai đoạn 3: chạy FastAPI mô hình trên cổng `8000` như trước, xác nhận `/health/ready`.
- Kiểm tra `config/phase5_step1_config.json` vẫn chứa URL dự đoán, ChromaDB directory, URI & database Neo4j của đúng instance.
- Đặt biến môi trường **username database thực tế** (nếu khác `neo4j`), không gửi mật khẩu trong tin nhắn hoặc bỏ vào file cấu hình:

```powershell
$env:NEO4J_USERNAME = "<username-trong-credentials-cua-ban>"
python -m phase5.step5_run --mode live
```

Python sẽ hỏi `Neo4j password (hidden)`. Kiểm tra mục tiêu `Cases: 11/11`, `Status: orchestrator_live_technical_pass`. Khi `--consultation mock`, **không gọi Ollama**.

### 4. Tùy chọn: Live + Ollama Atlas

Chỉ chạy nếu bản live ở bước 3 đạt và Ollama đang hoạt động:

```powershell
ollama list
python -m phase5.step5_run --mode live --consultation ollama --model qwen2.5:1.5b
```

Mục tiêu: `Cases: 11/11`, `Status: orchestrator_live_technical_pass_manual_review_pending`. Khi đó chỉ 3 Atlas cases S01–S03 gọi LLM. Không được xem tên trạng thái này là phê duyệt y khoa.

Báo cáo: `data/outputs/phase5_step5/step5_orchestrator_report.json`.

### 5. Chạy FastAPI thống nhất (mock mặc định)

Mở **terminal thứ nhất**:

```powershell
python -m phase5.step5_api --mode mock --port 8001
```

Giữ terminal chạy. Mở **terminal thứ hai**:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health/live
Invoke-RestMethod http://127.0.0.1:8001/health/ready

$body = @{
  request_id = "SYN-API-Q01"
  operation = "knowledge_research_lookup"
  synthetic_test_only = $true
  query_id = "Q01"
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/v1/research/agents/run" -Method Post -ContentType "application/json" -Body $body
```

Hoặc mở `http://127.0.0.1:8001/docs`. Endpoint thống nhất trả kết quả mock theo hợp đồng `Step5Response`.

**Cổng 8000**: API mô hình Giai đoạn 3. **Cổng 8001**: API tích hợp 5 Agent Giai đoạn 5. Không xung đột.

Với server live, dùng `python -m phase5.step5_api --mode live --port 8001` khi đã sẵn sàng; chỉ chạy trên máy cá nhân, không public Internet.

## Bảng nghiệm thu dự kiến

| Hạng mục | Mục tiêu |
|---|---|
| Schema/unit tests | 21 tests, không skip |
| Mock graph | 11/11 |
| Live graph | 11/11 |
| Prediction route | 2/2 hash đúng, threshold 0.225 |
| Knowledge route | 3 query × 3 metadata, `allowed_to_answer=false` |
| Atlas route | 6 cases, 3 chặn trước LLM |
| Medical evidence gate | `BLOCKED_RESEARCH_ONLY` ở mọi nhánh |
| Integrated HTTP | local FastAPI 8001 `200` cho request đúng, `422` cho request ngoài schema |
| Database writes / training | Không |

## Những giới hạn còn tồn tại

- Bước 5 **chỉ nhận yêu cầu thử nghiệm cố định**; chưa xử lý câu hỏi y tế tự do, không có auth, rate limits, production RBAC, stress test, pentest.
- API health `graph_compiled_backends_not_probed` **không** chứng minh database/API sẵn sàng; cần kiểm thử `--mode live` thực sự.
- “Medical gate blocked” là hợp đồng & smoke test, **chưa là ranh giới phân quyền production**. Neo4j nên dùng người dùng chỉ có quyền đọc.
- Chưa có thẩm định y khoa độc lập, quyền sử dụng bảy nguồn, hay hiệu lực lâm sàng. Không tự ý sửa thành `approved`.
- NHANES model phân loại chỉ báo HbA1c ≥ 5.7%, không dự báo bệnh tiểu đường tương lai.
- File JSON report không lưu câu trả lời Ollama (giữ tối thiểu metadata); nếu muốn rà soát nội dung, cần kiểm tra màn hình hoặc chạy đánh giá riêng có giám sát.

**Sau khi chạy xong:** gửi terminal output `step5_self_test`, `step5_run --mode mock`, `step5_run --mode live`, và file báo cáo `step5_orchestrator_report.json`. Chúng ta sẽ chuyển sang **Bước 6 – End-to-End Evaluation và báo cáo Giai đoạn 5**.

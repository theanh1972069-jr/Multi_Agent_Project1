# GIAI ĐOẠN 5 — BƯỚC 1: INTEGRATION CONTRACTS & ENVIRONMENT AUDIT

**Dự án:** Multi-Agent AI System for Diabetes Risk Assessment  
**Phạm vi:** Chốt hợp đồng dữ liệu và kiểm kê cấu hình local, **chưa tích hợp trực tiếp** năm Agent.  
**Ngày chuẩn bị:** 2026-11-03  
**Đã có:** Giai đoạn 3 baseline NHANES/API + minimal Prediction Agent; Giai đoạn 4 RAG/Neo4j sandbox đã nghiệm thu kỹ thuật.  
**Chưa có:** Orchestrator 5-agent thực tế; kết nối end-to-end giữa tất cả dịch vụ; xác minh chuyên môn/bản quyền để sinh trả lời y khoa.

## 1. Đối chiếu thiết kế các giai đoạn

- Tận dụng API GĐ3 đã thực hành: `POST http://127.0.0.1:8000/api/v1/research/nhanes/hba1c/predict`.
- Nhãn cố định: `classify_hba1c_ge_5_7_indicator` (HbA1c >= 5.7% **chỉ dấu cắt ngang**), **không phải** chẩn đoán hoặc nguy cơ mắc tiểu đường type 2 tương lai.
- Model `LogisticRegression`, threshold `0.225`, SHA256 `31e9c94b0f14369be7920b9315b026d0c4afedb9f7b2885d120d631d930582b1`.
- Collection ChromaDB `diabetes_kb_step3_e5small_v1`, 66 chunks (theo báo cáo GĐ4); Chroma snapshot SHA256 `cc064ec7187192c999418051cb2125a0510412843f8d0908e3d6842e4a71c7cd`.
- Neo4j: 4 `RelationCandidate`, 4 `TechnicalReview`, **0 approved claims/relations** theo báo cáo GĐ4.
- Nguồn y khoa thật vẫn `BLOCKED_RESEARCH_ONLY`. Ollama chỉ được bật sau này cho Atlas giả lập; Bước 1 không gọi LLM.
- Tài liệu `06-API-Contract-Draft.yaml` ở Giai đoạn 2 là **bản thiết kế API tổng quát**, không đồng nhất với schema NHANES đã triển khai tại Giai đoạn 3. Endpoint mới `/api/v1/research/workflows/assess` là **đề xuất chưa triển khai**.

## 2. Cấu trúc bộ thực hành

```text
05-Multi-Agent-Integration/
├── 03-Step1-Integration-Contracts-and-Environment-Audit.md
├── 04-Step1-Test-Matrix.md
├── requirements-step1.txt
├── schemas/                     # 5 JSON Schema phục vụ tích hợp Frontend/API
├── config/
│   └── phase5_step1_config.example.json
└── phase5/
    ├── __init__.py
    ├── contracts.py
    ├── step1_self_test.py
    ├── step1_environment_audit.py
    └── step1_graph_skeleton.py
```

**Giải thích:**

- `contracts.py`: Hợp đồng `WorkflowRequest`, `ResearchFeatures`, `UpstreamPrediction`, `EvidenceMetadata`, `WorkflowResponse`, `AgentState` và hằng số đã khóa. Có cơ chế không nhận thêm các trường `knowledge_gate`, `llm_called` do client tự gửi.
- `step1_self_test.py`: Kiểm tra schema, nhánh giả lập, chặn bypass và không tạo score giả; không kết nối dịch vụ nào.
- `step1_environment_audit.py`: **Kiểm tra file + metadata cấu hình trên máy bạn**. Nếu cung cấp model path, chỉ tính SHA256 trực tiếp từ bytes, không nạp `joblib`. Không kiểm tra DB connection, không gọi API/LLM.
- `step1_graph_skeleton.py`: Bản khung LangGraph có đủ **5 node theo vai trò Agent**, nhưng mỗi node là stub; chưa có inference thật, không có câu trả lời y khoa. Đừng diễn giải đó là hệ thống 5-agent hoàn chỉnh.

## 3. Thực hiện trên Windows PowerShell + VS Code

### 3.1. Giải nén và mở đúng thư mục

Giải nén ZIP, mở thư mục **`05-Multi-Agent-Integration`** làm workspace trong VS Code. Dùng terminal PowerShell ngay trong thư mục này để các lệnh `python -m phase5...` tìm đúng package.

### 3.2. Cài dependencies kiểm tra cơ bản

```powershell
python --version
python -m pip install "pydantic>=2.10,<3"
```

Nên sử dụng `.venv` riêng hoặc Python môi trường đã có Pydantic 2; **không cài đè vào môi trường train Giai đoạn 3 nếu không cần**. Bước 1 không cần pandas, scikit-learn, joblib, ChromaDB hoặc Neo4j để chạy smoke tests.

### 3.3. Chạy self-test hợp đồng

```powershell
python -m phase5.step1_self_test
```

**Kỳ vọng:** các case 01–14 đều `ok`, dòng cuối `Ran 14 tests ... OK`. Nếu không, gửi nguyên dòng lỗi; không thay đổi threshold/hash để né lỗi.

### 3.4. Chạy đồ thị LangGraph stub (tùy chọn)

```powershell
python -m pip install "langgraph>=1.0,<2"
python -m phase5.step1_graph_skeleton
```

**Kỳ vọng:** `graph_compiled=true`, `agent_nodes=5`, `status=not_connected`, `prediction=null`, `knowledge_gate=BLOCKED_RESEARCH_ONLY`, `llm_called=false`. Kết quả `not_connected` là **đúng thiết kế Bước 1**: dự đoán thật sẽ ghép ở Bước 2, tri thức ở Bước 3 và consultation ở Bước 4.

### 3.5. Chuẩn bị file cấu hình local — KHÔNG có mật khẩu

```powershell
Copy-Item .\config\phase5_step1_config.example.json .\config\phase5_step1_config.json
```

Mở `config/phase5_step1_config.json` và sửa các trường dưới đây:

| Trường | Cách điền |
|---|---|
| `model_artifact_path` | Đường dẫn tới **artifact GĐ3 đã train**, ví dụ `C:/.../03-ML-Research/models/baseline/nhanes_hba1c_baseline_step5.joblib`. Nếu chưa tìm thấy, để `null`. |
| `prediction_api_url` | Giữ `http://127.0.0.1:8000/api/v1/research/nhanes/hba1c/predict`. Bước 1 chỉ kiểm tra format, không yêu cầu API đang chạy. |
| `chroma_persist_dir` | Đường dẫn tới thư mục ChromaDB của GĐ4 trên **máy bạn**, có thể là đường dẫn tuyệt đối kiểu `C:/.../chroma_db`. Không đoán thư mục nếu chưa xác định; để `null`. |
| `chroma_collection` | Giữ chính xác `diabetes_kb_step3_e5small_v1`. |
| `neo4j_uri` | Chuỗi URI Neo4j Aura của bạn dạng `neo4j+s://<host>` **không chứa password**, nếu chưa cần thì để `null`. File audit chỉ báo đã cấu hình, không kết nối. |
| `neo4j_database` | Tên database đang dùng ở Aura (thường `neo4j` nhưng phải kiểm tra trên Aura Console). |
| `ollama_url` | Giữ `http://127.0.0.1:11434`, tùy chọn, không gọi LLM. |

**Nếu chưa biết đường dẫn file:** có thể tìm trong thư mục dự án bằng PowerShell:

```powershell
Get-ChildItem -Path .. -Recurse -Filter nhanes_hba1c_baseline_step5.joblib -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
Get-ChildItem -Path .. -Recurse -Filter chroma.sqlite3 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty DirectoryName
```

Dòng thứ hai chỉ giúp tìm **thư mục có file Chroma SQLite** nếu persistence dùng SQLite. Hãy đối chiếu thư mục thực tế với lệnh chạy Giai đoạn 4; không phải mọi đường dẫn tìm được đều là collection bạn cần.

**Rất quan trọng:** Không nhập `NEO4J_PASSWORD`, API keys, token, dữ liệu bệnh nhân hoặc mật khẩu vào JSON. Nếu đã lỡ đưa bí mật vào file, xóa khỏi cấu hình, thay/thu hồi bí mật nếu cần; không gửi file chứa bí mật trong chat. Không chụp ảnh có URI riêng hoặc mật khẩu. Bạn chỉ cần gửi **báo cáo JSON đã lọc** do audit tạo.

### 3.6. Chạy audit local

```powershell
python -m phase5.step1_environment_audit
```

Output: `data/outputs/phase5_step1/step1_environment_audit.json`.

**Lần đầu có thể hiện `local_setup_action_required`** nếu bạn chưa điền các đường dẫn; đây không phải lỗi mô hình. Cấu hình đầy đủ, model SHA khớp và các đường dẫn tồn tại thì trả `configured_not_connected`, **không phải đã kết nối** Neo4j/ChromaDB/API.

Báo cáo chỉ chứa nhãn trạng thái, phiên bản thư viện và hằng số kỹ thuật, **không lưu model path đầy đủ, hostname Neo4j, mật khẩu, input sức khỏe hay nội dung nguồn**. Hãy xem JSON trước khi chia sẻ.

## 4. Hợp đồng và ranh giới Agent

| Vai trò | Đầu vào sau này | Trách nhiệm ở Bước 1 |
|---|---|---|
| Orchestrator | `WorkflowRequest` với `operation` được whitelist | Tạo `AgentState`, gate do server quản lý |
| Data Analysis | `ResearchFeatures` hoặc câu hỏi Atlas giả lập | Chốt schema, từ chối BMI/tuổi/mã giới tính sai |
| Prediction | `validated_input` -> API 8B GĐ3 | Chốt `UpstreamPrediction`, chưa gọi API, không bịa score |
| Knowledge | Chroma + Neo4j metadata | Chốt `EvidenceMetadata` không có full-text; thật `BLOCKED_RESEARCH_ONLY` |
| Consultation | Cấu trúc output + gate | Chốt `WorkflowResponse`, không gọi LLM trong Bước 1 |

**Lưu ý bảo mật:** `AgentState` là schema điều phối nội bộ; không nhận thẳng dictionary của người dùng làm state. Chỉ tạo qua `WorkflowRequest` đã validate và `make_initial_state()`. Khi tích hợp thật, cần tái xác minh gate phía server và hạn chế quyền CSDL độc lập; một cờ trong Python không phải cơ chế cấp quyền production.

## 5. Khi nào hoàn thành Bước 1?

1. **Bắt buộc** `python -m phase5.step1_self_test`: 14/14 `OK`.
2. Chạy `python -m phase5.step1_environment_audit`, chia sẻ output và JSON đã lọc; giải quyết cấu hình model artifact và các thư mục còn thiếu trước khi kết nối bước sau (hoặc báo rõ mục chưa cấu hình).
3. **Khuyến nghị** LangGraph skeleton chạy ra `not_connected`, 5 node, `llm_called=false`.
4. **Không** train lại mô hình, không đổi threshold/hash, không phê duyệt MedicalClaim, không gửi source y khoa thật tới LLM.

**Đầu ra bạn gửi:** output self-test, output environment audit và `step1_environment_audit.json`. Tôi sẽ xem đúng những gì đã chạy, tổng hợp nhật ký Bước 1 và bắt đầu **Bước 2 – Data Analysis + Prediction Integration** với API NHANES đã có.

## 6. Tài liệu nguồn kỹ thuật

- LangGraph StateGraph (constructor/compile): https://reference.langchain.com/python/langgraph/graph/state/StateGraph
- LangGraph Graph API: https://docs.langchain.com/oss/python/langgraph/graph-api
- Pydantic 2 validation: https://docs.pydantic.dev/latest/concepts/validators/

Các tài liệu bên ngoài chỉ dùng để đối chiếu thư viện; **hằng số mô hình và giới hạn an toàn lấy từ hồ sơ Giai đoạn 3/4 của chính dự án**.

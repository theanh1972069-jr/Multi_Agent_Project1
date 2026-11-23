# GIAI ĐOẠN 2 – BƯỚC 6: TECHNICAL DESIGN

**Dự án:** Multi-Agent AI System for Diabetes Risk Assessment  
**Phiên bản:** Technical Design v0.1 — 31/10/2026  
**Trạng thái:** Đã soạn bản thiết kế; **chưa triển khai hoặc kiểm thử runtime**  
**Đầu vào:** Tài liệu yêu cầu gốc 45 trang (Problem Statement, SRS, Use Case, Activity Diagram); các bản thiết kế Giai đoạn 2, Bước 1–5.

> **Nguyên tắc kế thừa:** Phần này cụ thể hóa các lựa chọn kỹ thuật; không âm thầm thay đổi phạm vi SRS. Các công nghệ chưa được khẳng định trong tài liệu nguồn được gắn nhãn **Đề xuất / cần chốt**. MVP dùng để nghiên cứu và hỗ trợ sàng lọc, không chẩn đoán hoặc kê đơn.

## 1. Mục tiêu và phạm vi bàn giao

Bước 6 hoàn thiện thiết kế để có thể lập trình ở các giai đoạn sau:

1. Chọn cách tổ chức triển khai, công nghệ và ranh giới các module.
2. Xác định cấu trúc thư mục repository, chuẩn đặt tên và luồng phụ thuộc.
3. Đặc tả các nhóm REST API, kiểu thông điệp, mã lỗi và chính sách versioning.
4. Thiết kế cách tích hợp LangGraph, năm Agent, ML pipeline, RAG/Knowledge Graph, LLM provider.
5. Ánh xạ 19 bảng của ERD vào ORM, migration và truy vấn quyền sở hữu dữ liệu.
6. Xác định bảo mật, môi trường, logging, kiểm thử, CI/CD, triển khai, kế hoạch thực hiện.

**Ngoài phạm vi bước này:** huấn luyện mô hình thực tế, tạo database production, chạy API, triển khai Web/Mobile, cung cấp dự đoán bệnh lý hoặc xác nhận hiệu năng đã đạt.

## 2. Architecture Decision Records (ADR)

| ID | Vấn đề | Quyết định thiết kế | Trạng thái / lý do |
|---|---|---|---|
| ADR-01 | Phong cách kiến trúc | **Modular Monolith** cho FastAPI + các Agent trong MVP; ingestion worker tách process | **Đề xuất ưu tiên**, giảm độ phức tạp và vẫn dễ tách module |
| ADR-02 | Web | React + TypeScript | Kế thừa tài liệu nguồn |
| ADR-03 | Mobile | Android/iOS dùng chung REST API; **Flutter là lựa chọn đề xuất** nếu cần một codebase; Kotlin/Swift vẫn khả thi | **Chưa chốt framework**; không ràng buộc Backend vào Flutter |
| ADR-04 | Backend | Python + FastAPI + Pydantic | Kế thừa FastAPI; Pydantic để xác thực contract |
| ADR-05 | AI workflow | LangGraph quản lý node/state/conditional edge; không cần LLM cho Data/Prediction | Kế thừa thiết kế Agent |
| ADR-06 | ML | scikit-learn + versioned preprocessing/inference artifact, DL chỉ nếu thực nghiệm có lợi | Kế thừa ML; không khẳng định model đã có |
| ADR-07 | CSDL nghiệp vụ | PostgreSQL + SQLAlchemy + Alembic migrations | PostgreSQL từ nguồn; hai thư viện là đề xuất triển khai |
| ADR-08 | RAG | **ChromaDB** làm Vector DB ban đầu, thông qua adapter; FAISS là phương án thay thế | **Đề xuất cần chốt** để hỗ trợ metadata/version/filter |
| ADR-09 | Knowledge Graph | Neo4j dùng cho tri thức y khoa đã phê duyệt | Kế thừa nguồn; tách khỏi dữ liệu cá nhân |
| ADR-10 | LLM | `LLMProvider` interface; chọn nhà cung cấp theo cấu hình và chính sách dữ liệu | **Chưa chốt** nhà cung cấp, chi phí và nơi xử lý dữ liệu |
| ADR-11 | Việc dài | Document ingestion ngoài request HTTP, có worker và trạng thái job ở PostgreSQL | Đề xuất để tránh timeout và hỗ trợ retry |
| ADR-12 | Deployment | Docker Compose ở máy phát triển/integration; hạ tầng production đánh giá riêng | Kế thừa Docker; **không tuyên bố đã triển khai** |
| ADR-13 | Authentication | Token ngắn hạn hoặc server-side session, Argon2id/password hashing, RBAC tại Backend | Cần chốt cách refresh/revoke trước khi code auth |
| ADR-14 | Giải thích mô hình | Explainability (ví dụ SHAP) là đầu ra của module Prediction, độc lập khỏi LLM | Kế thừa FR08; không diễn giải đóng góp thành quan hệ nhân quả |

**Trình tự ưu tiên:** giai đoạn 3 chốt `model_manifest` và tiền xử lý; giai đoạn 4 chốt cấu hình embedding/Vector DB/KG; giai đoạn 5 triển khai graph; giai đoạn 6 tích hợp Web/Mobile. Bước 6 chỉ tạo thiết kế ổn định cho chúng.

## 3. Cấu trúc thư mục monorepo đề xuất

```text
Diabetes-Multi-Agent/
├── README.md
├── .gitignore
├── .env.example                   # Chỉ tên biến và giá trị giả, tuyệt đối không có secret thật
├── docs/
│   ├── 01-Analysis/               # Problem Statement, Scope, SRS, Use Case, Activity
│   ├── 02-Design/
│   │   ├── 01-System-Architecture.md
│   │   ├── 02-Agent-Architecture.md
│   │   ├── 03-Agent-Interaction-Diagram.md
│   │   ├── 04-Sequence-Diagrams.md
│   │   ├── 05-Entity-Relationship-Diagram.md
│   │   └── 06-Technical-Design.md
│   ├── 03-AI-Research/
│   └── 04-Testing/
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── migrations/versions/
│   ├── app/
│   │   ├── main.py                # FastAPI app factory, lifespan, register routers
│   │   ├── core/                  # config, security, logging, exceptions
│   │   ├── api/v1/                # auth, users, assessments, chats, knowledge, admin
│   │   ├── schemas/               # Pydantic request/response DTOs
│   │   ├── domain/                # enums, rules, domain errors, service interfaces
│   │   ├── services/              # auth, assessments, history, documents, chat
│   │   ├── db/                    # session, SQLAlchemy models, repositories
│   │   └── integrations/          # interfaces/adapters đến AI, storage, queues
│   └── tests/                     # unit, API, DB integration
├── ai-services/
│   ├── pyproject.toml
│   ├── orchestration/
│   │   ├── graph.py               # build_graph(), conditional routing
│   │   ├── state.py               # AgentState schema
│   │   ├── router.py              # xác định task_type từ request được phép
│   │   └── finalizer.py           # validation, policy, merge results
│   ├── agents/
│   │   ├── data_analysis.py
│   │   ├── prediction.py
│   │   ├── knowledge.py
│   │   └── consultation.py
│   ├── inference/                 # model loading, manifest, preprocessing, SHAP
│   ├── rag/                       # embedding, retrieval, citations, Chroma adapter
│   ├── graph/                     # Neo4j queries, metadata/version checks
│   ├── llm/                       # interface, provider adapter, safety filters
│   ├── worker/                    # document ingestion, staging, publication
│   ├── contracts/                 # AgentRequest, State, AgentResponse, error enums
│   └── tests/
├── ml-research/
│   ├── datasets/README.md         # Quyền sử dụng/provenance; không commit PHI
│   ├── notebooks/
│   ├── src/                      # train, evaluate, calibrate, export
│   ├── reports/                   # metric, confusion matrix, bias/limitations
│   └── artifacts/README.md        # Không đưa model artifact lên Git nếu lớn/bí mật
├── frontend/                      # React + TypeScript, API client dùng OpenAPI contract
│   ├── src/pages/
│   ├── src/features/
│   ├── src/services/api/
│   └── src/components/
├── mobile/                        # Framework sẽ chốt; API contract không đổi
│   └── README.md
├── infrastructure/
│   ├── docker-compose.yml
│   ├── docker/backend.Dockerfile
│   ├── docker/worker.Dockerfile
│   ├── config/
│   └── observability/
└── tests/
    ├── e2e/
    └── contract/
```

**Ranh giới phụ thuộc:** API controller → domain/application service → repository hoặc `AgentGateway`; graph gọi các interface AI, không tự làm auth hoặc SQL DDL. Không cho `frontend/` hay `mobile/` kết nối DB, Neo4j, Chroma hoặc LLM provider trực tiếp. Tránh import vòng giữa `backend` và `ai-services` bằng package `contracts` tách rõ hoặc dùng một package `shared-contracts` khi bắt đầu code; không copy DTO có thể lệch version.

## 4. Sơ đồ triển khai module

```mermaid
flowchart TB
  WEB[React + TypeScript] -->|HTTPS REST /api/v1| API[FastAPI / API + Auth]
  MOB[Mobile Android/iOS] -->|HTTPS REST /api/v1| API
  ADMIN[Admin UI] -->|HTTPS REST /api/v1| API
  API -->|ORM + transactions| PG[(PostgreSQL)]
  API -->|internal typed call| GW[Agent Gateway]
  GW --> ORCH[LangGraph Orchestrator]
  ORCH --> DA[Data Analysis]
  DA --> PRED[Prediction]
  PRED --> MODEL[Model Registry + Inference + Explainability]
  ORCH --> KNOW[Knowledge]
  KNOW --> VDB[(ChromaDB)]
  KNOW --> NEO[(Neo4j)]
  ORCH --> CONS[Consultation]
  CONS --> LLM[LLM Provider Adapter]
  API -->|enqueue job| JOBS[(PostgreSQL ingestion jobs)]
  JOBS --> WORKER[Document Ingestion Worker]
  WORKER --> VDB
  WORKER --> NEO
  WORKER --> PG
```

Các mũi tên là đường giao tiếp logic, không có nghĩa tất cả đều là container độc lập. Với tác vụ `general_qa`, graph bỏ qua Data Analysis/Prediction; với `explain_assessment`, Backend nạp kết quả cũ sau authorization và graph không suy luận lại.

## 5. REST API Design – v1 (đề xuất)

Base path `/api/v1`. Request/response JSON; tài liệu nguồn cho phép Web/Mobile dùng chung API. API phải sinh OpenAPI và đóng băng contract phiên bản cho Web/Mobile khi tích hợp. Token xác thực không đưa vào URL, logs hay response.

| Method | Endpoint | Chức năng | Quyền | Mã thành công |
|---|---|---|---|---|
| POST | `/auth/register` | Đăng ký | Guest | 201 |
| POST | `/auth/login` | Đăng nhập | Guest | 200 |
| POST | `/auth/logout` | Đăng xuất / revoke session | User, Admin | 204 |
| GET | `/users/me` | Xem hồ sơ chính mình | User | 200 |
| PATCH | `/users/me` | Sửa hồ sơ | User | 200 |
| POST | `/assessments` | Nhập dữ liệu, chạy đánh giá | User | 200 (completed) hoặc 422/503 |
| GET | `/assessments` | Lịch sử đánh giá cá nhân | User | 200 |
| GET | `/assessments/{assessment_id}` | Chi tiết đánh giá của owner | User | 200 hoặc 404 |
| POST | `/assessments/{assessment_id}/explanations` | Giải thích lại kết quả đã lưu | User | 200 hoặc 422/503 |
| POST | `/chat/sessions` | Tạo hội thoại | User | 201 |
| GET | `/chat/sessions` | Danh sách hội thoại | User | 200 |
| POST | `/chat/sessions/{session_id}/messages` | Gửi câu hỏi RAG | User | 200 hoặc 422/503 |
| GET | `/chat/sessions/{session_id}/messages` | Lịch sử chat | User | 200 |
| GET | `/knowledge/search` | Tra cứu kiến thức có nguồn | User | 200 |
| POST | `/admin/documents` | Tải tài liệu | Admin | 201 |
| GET | `/admin/documents` | Danh sách tài liệu | Admin | 200 |
| POST | `/admin/documents/{document_id}/versions/{version_id}/approve` | Phê duyệt bản tài liệu | Admin | 200 |
| POST | `/admin/documents/{document_id}/versions/{version_id}/ingest` | Yêu cầu lập chỉ mục | Admin | 202 + job_id |
| GET | `/admin/ingestion-jobs/{job_id}` | Theo dõi ingestion job | Admin | 200 |
| POST | `/admin/documents/{document_id}/versions/{version_id}/revoke` | Thu hồi phiên bản | Admin | 200 |
| GET | `/health/live` | Liveness | Nội bộ / theo deployment | 200 |
| GET | `/health/ready` | Readiness các phụ thuộc bắt buộc | Nội bộ / theo deployment | 200 hoặc 503 |

**Quy tắc thiết kế:**

- `POST /assessments` cần `Idempotency-Key` là UUID do client tạo, map với `health_assessments.request_id`/`agent_runs.request_id` theo owner. Gửi lại cùng key/payload trả cùng kết quả hoặc trạng thái trước đó; cùng key khác payload trả `409`.
- `GET` history phân trang; query tại DB luôn lọc `owner_id`, không tin owner_id do client cung cấp.
- `needs_input` và `out_of_scope` → HTTP 422 (có domain `status` riêng), **không có `prediction`**. Nếu model provider lỗi → 503 khi phụ thuộc bị gián đoạn, 500 nếu lỗi nội bộ chưa phân loại.
- Tùy quyết định lưu dữ liệu, request 422 có thể ghi assessment status `needs_input` hoặc chỉ lưu run metadata, nhưng phải theo chính sách đồng ý. Không lưu dữ liệu sức khỏe thô trong log.
- Query Admin không mặc nhiên được đọc thông tin sức khỏe người dùng; quyền quản trị tài liệu là quyền riêng.
- Mỗi đầu ra chứa `request_id`, `status`, `warnings` và `errors` (mã an toàn), cho phép kiểm tra theo log không nhạy cảm.

### 5.1. Contract dữ liệu sức khỏe

Đối với nghiên cứu Pima, dự thảo `HealthFeatures` có 8 thuộc tính: `pregnancies`, `glucose`, `blood_pressure`, `skin_thickness`, `insulin`, `bmi`, `diabetes_pedigree_function`, `age`. Một số giá trị có thể `null` nếu người dùng chưa đo; **không tự thay giá trị thiếu thành 0**. Nên truyền kèm `input_schema_version` và `units`; khi suy luận, `model_manifest` mới là nguồn xác định đúng danh sách feature bắt buộc, thứ tự, đơn vị, miền áp dụng. Không thiết kế API mặc định 3 feature đủ dùng khi model yêu cầu 8 feature. Pima không tự động áp dụng cho mọi đối tượng người dùng.

**Request minh họa — chưa chứng minh hợp lệ để suy luận:**

```json
{
  "input_schema_version": "pima-draft-v1",
  "features": {
    "pregnancies": null,
    "glucose": 150,
    "blood_pressure": 85,
    "skin_thickness": null,
    "insulin": null,
    "bmi": 30.0,
    "diabetes_pedigree_function": null,
    "age": 45
  },
  "units": {
    "glucose": "mg/dL",
    "blood_pressure": "mmHg"
  },
  "with_consultation": false
}
```

### 5.2. Kết quả và lỗi

**Ví dụ chưa đủ dữ liệu (HTTP 422):**

```json
{
  "request_id": "c2b0ea75-930c-494a-a3cf-90b52e9d9d5b",
  "status": "needs_input",
  "assessment_id": null,
  "prediction": null,
  "consultation": null,
  "references": [],
  "warnings": [],
  "errors": [
    {"code": "MISSING_REQUIRED_FEATURES", "component": "data_analysis", "fields": ["insulin"]}
  ]
}
```

**Ví dụ kết quả khi thật sự có model (chỉ là shape; không tạo giá trị minh họa dễ nhầm với đầu ra y khoa):**

```json
{
  "status": "completed",
  "prediction": {
    "prediction_label": "value_from_model",
    "score_kind": "unavailable",
    "score_value": null,
    "risk_percent": null,
    "model_version": "from_registry",
    "explanation": []
  },
  "consultation": null,
  "references": [],
  "warnings": ["NOT_A_DIAGNOSIS"]
}
```

`prediction_label` thực tế là SMALLINT (0/1); string trong ví dụ trên **chỉ để diễn giải placeholder**, không phải JSON response hợp lệ ở runtime. Score chỉ được gọi `risk_percent` khi đã hiệu chỉnh và xác thực phù hợp.

### 5.3. Mã lỗi thống nhất

| Mã domain | Điều kiện | Trạng thái domain | HTTP |
|---|---|---|---|
| `MISSING_REQUIRED_FEATURES` | Thiếu feature từ manifest | `needs_input` | 422 |
| `INVALID_UNITS` | Đơn vị không xác định | `needs_input` | 422 |
| `MODEL_OUT_OF_SCOPE` | Người dùng ngoài miền đã đánh giá | `out_of_scope` | 422 |
| `MODEL_UNAVAILABLE` | Service hoặc artifact lỗi | `failed` | 503 |
| `EVIDENCE_NOT_FOUND` | Không tìm được tài liệu active | `completed` (giới hạn tư vấn) hoặc `failed` theo loại request | 200/503 |
| `LLM_UNAVAILABLE` | LLM lỗi | `completed` nếu ML hợp lệ; tư vấn bị lược bỏ | 200 hoặc 503 cho chat thuần LLM |
| `FORBIDDEN_OWNER_ACCESS` | Owner mismatch | Không vào graph | 404 hoặc 403 theo policy |
| `IDEMPOTENCY_CONFLICT` | Cùng key, payload khác | Không vào graph | 409 |
| `DOCUMENT_NOT_APPROVED` | Chưa được duyệt | Job không chạy | 409 |
| `INGESTION_FAILED` | Worker thất bại | Job `failed`; nguồn không active | GET job 200 với status `failed` |

## 6. Module / contracts giữa hệ thống và Agent

- **`AssessmentService`**: API validation, ownership, idempotency, orchestrator call, transaction lưu lịch sử.
- **`AgentGateway`**: chuẩn hóa `AgentRequest → AgentResponse`; timeout và policy boundary; khi MVP là internal Python call; nếu tách service giữ nguyên contract.
- **`DataAnalysisAgent`**: dùng manifest để validate/transform, không tự `fit()` lại preprocessing trên input mới.
- **`PredictionAgent`**: chỉ load artifact *validated/active* + pipeline đi kèm, trả model_version, score_kind, explainability. Không có quyền chỉnh sửa dữ liệu y tế trong DB tùy ý.
- **`KnowledgeAgent`**: truy vấn metadata active từ PostgreSQL trước/đồng thời truy xuất Chroma/Neo4j, kiểm tra citations trước khi bàn giao.
- **`ConsultationAgent`**: dùng evidence và prediction bất biến, áp dụng guardrails; không đưa ra chẩn đoán hay điều chỉnh thuốc. Đầu ra phải qua independent finalizer.
- **`DocumentIngestionWorker`**: parse → chunk → embed → index staging → KG index → verify → publish active; idempotent, retry có giới hạn, ghi trạng thái `document_ingestion_jobs`.

### 6.1. State / điều phối LangGraph

- `AgentState` gồm `request_id`, `task_type`, `authorized_context`, `health_features`, `validation`, `prepared_features`, `prediction`, `evidence`, `consultation`, `errors`, `warnings`, `final_status`.
- Node chỉ trả patch các trường được phép ghi; `authorized_context` do Backend cung cấp là readonly. Graph không quyết định authorization.
- Đồ thị `risk_assessment`: `route → data_analysis → (invalid: finalize | valid: prediction) → optional knowledge → optional consultation → finalizer`.
- Đồ thị `general_qa`: `route → knowledge → (no evidence: limit response | evidence: consultation) → finalizer`.
- Đồ thị `explain_assessment`: Backend kiểm tra owner, nạp snapshot prediction từ DB → `knowledge → optional consultation → finalizer`; **không chạy model lại**.
- Không bắt buộc persistent checkpoint chứa PHI; nếu cần checkpoint, phải đánh giá lưu giữ/mã hóa/thu hồi trước khi bật.
- Giới hạn steps và deadline, retries chỉ cho lỗi tạm thời; không lặp lại `POST` tạo bản ghi/ingestion nếu thiếu idempotency.

## 7. Tích hợp ML, RAG, Knowledge Graph, LLM

### 7.1. ML Model Registry / Manifest

Một model artifact phải đi kèm:

```yaml
model_name: diabetes-risk-model
version: <version-created-in-phase-3>
status: validated
feature_schema_version: <schema-version>
features_ordered: [pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi, diabetes_pedigree_function, age]
units: <verified-units-per-feature>
preprocessing_pipeline_uri: <internal-uri>
model_artifact_uri: <internal-uri>
checksum_sha256: <verified-checksum>
training_dataset_provenance: <dataset-licence-and-lineage>
validation_metrics: <precision-recall-f1-rocauc-and-calibration>
applicable_population: <validated-scope>
probability_calibrated: false
```

Placeholder trong dấu `<...>` phải được thay bằng dữ liệu thực sau Giai đoạn 3. Feature list ở trên là cấu trúc Pima dự thảo, **không tự động chứng minh** việc mọi người dùng có thể được dự đoán.

Không dùng pickle/joblib artifact từ nguồn không tin cậy; checksum và quyền truy cập artifact phải được kiểm soát. Pipeline tiền xử lý và model được kiểm thử trên dữ liệu riêng biệt trước khi kích hoạt.

### 7.2. RAG + KG

- Lưu nguồn gốc, phiên bản, thời điểm tài liệu, trang/đoạn, điều kiện phê duyệt trong PostgreSQL.
- Chroma chỉ giữ vector và metadata mapping (`document_version_id`, `chunk_id`); Neo4j dùng node/edge có version provenance; source docs giữ tại storage được bảo vệ.
- Khi đọc, Knowledge Agent chỉ chấp nhận citation có `publication_status=active` và phiên bản thuộc source đã phê duyệt; không tin riêng filter từ vector DB.
- Tài liệu đầu vào và đoạn retrieved là **dữ liệu không đáng tin cậy về chỉ thị**: mọi prompt injection trong nguồn bị bỏ qua.
- Nếu Neo4j chưa khả dụng, có thể trả truy xuất RAG thuần nếu vẫn có nguồn phù hợp và policy cho phép; không bịa kết quả tri thức đồ thị.
- Khi revoke document: chặn publish/đọc nguồn ngay trong PostgreSQL, sau đó đối soát xóa index/graph theo job; không có distributed SQL transaction ba DB.

### 7.3. LLM Provider

- Interface `generate_consultation(context_minimized, evidence, policy) → ConsultationResult`.
- Không gửi dữ liệu sức khỏe, email, user_id hoặc lịch sử không cần thiết cho bên thứ ba; khi có dữ liệu cá nhân cần kiểm tra quyền/cơ sở pháp lý và consent cụ thể theo chính sách.
- Có retry/timing budget, hạn chế token/chi phí; đầu ra có guardrails, citations, disclaimers, không sửa `prediction`.
- Khi provider unavailable, trả phần ML nếu có; với câu hỏi kiến thức chỉ phản hồi giới hạn thay vì bịa nội dung.

## 8. PostgreSQL ORM & migration (kế thừa ERD Bước 5)

19 bảng không đổi: `users`, `user_profiles`, `consent_events`, `health_assessments`, `assessment_features`, `model_versions`, `prediction_results`, `prediction_factors`, `assessment_reports`, `chat_sessions`, `chat_messages`, `knowledge_documents`, `document_versions`, `document_ingestion_jobs`, `knowledge_chunks`, `agent_runs`, `agent_steps`, `retrieval_citations`, `audit_logs`.

- Dùng SQLAlchemy ORM, Alembic migrations (đề xuất); không phụ thuộc `Base.metadata.create_all()` khi đã triển khai migration.
- UUID primary key, FK rõ ràng; `TIMESTAMPTZ` UTC ở DB, hiển thị theo vùng giờ ở client. `email` unique không phân biệt hoa/thường bằng `lower(email)` index hoặc `citext` (chọn một trước khi migrate).
- Index theo owner+created_at, foreign keys, session history; `prediction_results.assessment_id` UNIQUE; `document_versions` partial unique active per document.
- `prediction_results` **bất biến** sau khi lưu, report ở bảng khác. Quy tắc `risk_percent` chỉ áp dụng cho score calibrated và phải có bằng chứng validation.
- `consent_events` là append-only, truy xuất quyết định hợp lệ mới nhất theo `purpose`; `audit_logs` đã lọc thông tin nhạy cảm.
- Không có FK cross-DB sang Chroma/Neo4j; metadata `document_version_id`, `chunk_id` được xác minh ở application layer.
- Sử dụng transaction khi ghi assessment/prediction và khi publish document version. Worker giữ state và reconciliation khi một hệ lưu trữ thất bại.
- Ownership check tại API, repository query có `owner_id`; cân nhắc RLS bổ sung. Admin quản trị tài liệu không tự động có quyền đọc dữ liệu sức khỏe người dùng.

## 9. Security, privacy, reliability & observability

| Chủ đề | Thiết kế bắt buộc/đề xuất |
|---|---|
| Xác thực | Băm mật khẩu hiện đại; token/session ngắn hạn; rate limit đăng nhập; khóa/tạm khóa chính sách |
| Authorization | RBAC với các scope (`assess:self`, `chat:self`, `manage:documents`); ownership check server-side, deny by default |
| Dữ liệu sức khỏe | Chỉ thu thập fields cần thiết, bảo vệ khi truyền/lưu/backup; có retention, xóa/thu hồi theo chính sách |
| Secret | Chỉ lưu trong env/secret manager, không commit `.env`, không dùng tài khoản DB chung quyền superuser |
| API | HTTPS ở môi trường công khai, validation + giới hạn kích thước, CORS allowlist, upload content validation |
| LLM/RAG | Prompt-injection isolation, nguồn active, citations, không gửi raw PHI lên provider ngoài nếu chưa được phép |
| Agent isolation | Chỉ cấp tool cần thiết; Orchestrator không có quyền bypass RBAC/DB; giới hạn thời gian và số vòng |
| Tracing | `request_id`, `agent_run_id`, `agent_name`, duration, status, error code, model version; không lưu payload sức khỏe/prompt đầy đủ |
| Monitoring | Health probes, latency, lỗi dự đoán, tỷ lệ no-evidence, ingestion failures, metrics ẩn danh |
| Recovery | Backup/restore PostgreSQL và tài liệu; chính sách snapshot/chạy lại index Chroma/Neo4j, diễn tập phục hồi |

**Mục tiêu SRS:** HTTP API thông thường < 2 giây, luồng dự đoán < 5 giây trong môi trường thử nghiệm, tỷ lệ xử lý hợp lệ ≥ 95% trong bài test tải được xác định. Đây **chỉ là mục tiêu kiểm thử**, chưa xác nhận đạt; LLM/ingestion có deadline, fallback hoặc xử lý ngoài HTTP phù hợp.

## 10. Infrastructure và cấu hình triển khai

### 10.1. Môi trường

- **local:** Python venv (Windows PowerShell được hỗ trợ), PostgreSQL/Neo4j/Chroma bằng Docker Compose tùy nhu cầu; model giả lập (mock) trong unit tests.
- **integration:** Docker Compose các service `api`, `worker`, `postgres`, `chroma`, `neo4j`; network nội bộ; secrets không nằm trong YAML/git.
- **production tương lai:** HTTPS reverse proxy, backup, resource limits, monitoring, secret manager, nâng cấp/migrate theo kiểm soát. Chưa chốt nhà cung cấp cloud.

### 10.2. Ví dụ `.env.example` (giá trị giả)

```dotenv
APP_ENV=local
API_PREFIX=/api/v1
DATABASE_URL=postgresql+psycopg://app_user:CHANGEME@localhost:5432/diabetes_app
CHROMA_HOST=localhost
CHROMA_PORT=8001
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=CHANGEME
LLM_PROVIDER=disabled
LLM_API_KEY=
ALLOWED_ORIGINS=http://localhost:5173
MODEL_MANIFEST_URI=
MODEL_ARTIFACT_URI=
LOG_LEVEL=INFO
```

**Cảnh báo:** `.env.example` không đủ để chạy một hệ thống thật. `CHANGEME` chỉ là placeholder, không dùng trong môi trường mở Internet. `CHROMA_PORT` mapping ngoài host chỉ là ví dụ, cần khớp Compose thật. Model thiếu nghĩa là prediction chưa khả dụng, hệ thống phải báo đúng `MODEL_UNAVAILABLE`.

### 10.3. Hướng dẫn developer khi bắt đầu code (chưa phải bước thực hiện hiện tại)

Từ thư mục `backend/` trên Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
# Sau khi khóa dependencies vào pyproject.toml:
python -m pip install -e .
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Khi mới tạo repo, các lệnh migration hoặc uvicorn **chưa chạy được** nếu chưa có source, cấu hình, dependencies và database. Không chạy dữ liệu y tế thật trên môi trường demo không được bảo vệ.

## 11. Kế hoạch kiểm thử và chất lượng

| Cấp | Các ca cốt lõi | Điều kiện qua |
|---|---|---|
| Unit | Email/auth, đơn vị, missing/invalid/out of scope, AgentState, domain errors | Đúng schema/status, không phát sinh prediction giả |
| ML research | Leakage-free split, preprocess, model comparison, precision/recall/F1/ROC-AUC, calibration, population scope | Có báo cáo, model_manifest và kiểm định trước active |
| Integration DB | FK, unique owner+request_id, version, publication filter, consent, audit | Không rò owner, không trùng idempotent |
| Agent workflow | Routing 3 loại nhiệm vụ, retries, timeout, fallback, no evidence | Chỉ Prediction cập nhật model output; source verifiable |
| API contract | Đúng route/HTTP/schema, OpenAPI, auth/ownership, pagination | Web/Mobile gọi chung và xử lý lỗi nhất quán |
| RAG ingestion | pending/approved/ready/active, re-index/revoke, failure sau Chroma trước Neo4j | Không truy xuất staging/revoked |
| Security | Bypass RBAC, upload độc hại, prompt injection, secret leaks, PII logs | Từ chối an toàn, không lộ secrets/health data |
| E2E | Nhập → đánh giá → xem lịch sử; hỏi → nguồn; admin upload → active | Đúng với SD-01..SD-04, chỉ dữ liệu thử nghiệm |
| Nonfunctional | Load p95, timeout, retry, log sanitation, backup restore | So sánh với mục tiêu SRS, báo cáo chưa đạt nếu có |

**CI đề xuất:** lint + type-check + unit tests → contract tests → integration with disposable PostgreSQL/Chroma/Neo4j → security/dependency checks → build Docker image → staging smoke tests. Không cho commit pipeline artifact tùy ý không có provenance/checksum.

## 12. Phân chia việc theo Giai đoạn 3–8 (để không xây sai thứ tự)

| Giai đoạn | Tạo ra | Phụ thuộc |
|---|---|---|
| 3 — ML/DL | dataset analysis, EDA, pipeline fit, baseline/comparison, report, model + manifest | Feature contract và giới hạn dữ liệu |
| 4 — Knowledge Base & RAG | nguồn y khoa được duyệt, chunk/embedding, Chroma, KG provenance, retrieval test | Source/version schema + ingestion worker |
| 5 — Multi-Agent | LangGraph workflows, 5 Agent, guardrails, contract & failure tests | ML interface, RAG interface, AgentState |
| 6 — Application | FastAPI, PostgreSQL, React, Mobile, Auth, history, admin | API/ERD/Agent contracts đã kiểm định |
| 7 — Testing | unit/integration/E2E/AI/safety/performance report | Có hệ thống chạy trong test environment |
| 8 — Deployment | Dockerized demo, monitoring/logging/backup, hướng dẫn vận hành, báo cáo | Test pass và nguy cơ đã được đánh giá |

### 12.1. Milestone kỹ thuật ưu tiên

1. **Foundation:** repo/venv/CI, app skeleton, `.env.example`, Alembic, mock AgentGateway, typed errors.
2. **Core prediction:** User + assessment schema, model registry/manifest và Prediction endpoint (chỉ sau khi model giai đoạn 3 validated).
3. **Knowledge:** document metadata, source review, ingestion worker, Chroma, Neo4j, citations.
4. **Agent integration:** LangGraph, routing/finalizer, error handling, eval suites.
5. **Web/Mobile:** nhập liệu, xem kết quả, chatbot, lịch sử, admin.
6. **Hardening:** auth/consent review, full tests, observability, packaging.

## 13. Quyết định còn mở / Không được nhầm là đã chốt

1. **Mobile:** Flutter vs native Kotlin/Swift; chỉ chốt sau khi xác nhận phạm vi Android/iOS và kỹ năng đội.
2. **LLM:** provider, vùng lưu dữ liệu, retention, chi phí và cơ sở cho việc gửi dữ liệu cá nhân.
3. **Model:** dataset cuối, tập đặc trưng, đơn vị, phạm vi dân số, calibration và có xuất xác suất hay không — do giai đoạn 3 quyết định.
4. **Vector DB:** Chroma (đề xuất) vs FAISS; ingestion throughput, metadata filtering và rebuild strategy phải thử nghiệm.
5. **Data lifecycle:** thời hạn lưu, xoá lịch sử/chat, backup, dữ liệu của người chưa đăng nhập và quyền của chuyên gia y tế.
6. **Auth:** JWT + refresh cookie vs server-side session, logout/revocation, bổ sung MFA cho admin.
7. **Performance:** tài nguyên máy demo, concurrency, p95 budgets và timeout thực tế, chưa có benchmark.
8. **ERD policy:** có cần versioned report khi giải thích lại nhiều lần thay vì report 1:1; kiểm tra với UX.
9. **API contract:** hoàn thiện schema OpenAPI, xác nhận đổi tên `pregnancies` và cấu trúc input theo `model_manifest` đã xuất.

## 14. Definition of Done – Giai đoạn 2

- [x] Bước 1: System Architecture v0.1.
- [x] Bước 2: Agent Architecture v0.1.
- [x] Bước 3: Agent Interaction Diagram v0.1.
- [x] Bước 4: Sequence Diagrams v0.1.
- [x] Bước 5: Entity Relationship Diagram v0.1 (19 bảng).
- [x] Bước 6: Technical Design v0.1 (tech stack, modules, API, contracts, security, tests, roadmap).
- [ ] Review/chốt ADR và xử lý các quyết định mở cùng chủ dự án.
- [ ] Kiểm tra thực nghiệm công nghệ, chạy integration và cập nhật các bản thiết kế v1.0.

**Kết luận:** Sáu bước thiết kế đã có bản nháp hoàn chỉnh và đủ căn cứ bắt đầu **Giai đoạn 3 — xây dựng mô hình ML/DL** theo hướng nghiên cứu, sau khi kiểm tra/điều chỉnh các giả định về dataset, phạm vi dự đoán và quy trình validation. Chưa tuyên bố đã xây dựng hay chạy thành công hệ thống.

## 15. Nguồn tham khảo

- **Nguồn yêu cầu chính:** tài liệu dự án 45 trang người dùng cung cấp, cùng năm tài liệu Bước 1–5 của Giai đoạn 2.
- FastAPI — Bigger Applications / APIRouter: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- Alembic migrations: https://alembic.sqlalchemy.org/en/latest/
- LangGraph documentation: https://docs.langchain.com/oss/python/learn
- Chroma docs / metadata filtering: https://docs.trychroma.com/

**Các nguồn ngoài chỉ giúp lựa chọn công nghệ; không thay thế nội dung hoặc phạm vi của tài liệu yêu cầu dự án.**

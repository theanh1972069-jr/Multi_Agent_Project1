# DiaGuard AI — Hệ thống Multi-Agent Sàng lọc Nguy cơ & Tư vấn Tiểu đường

**DiaGuard AI** là ứng dụng Web full-stack kết hợp **Kiến trúc Đa tác nhân (5-Agent LangGraph)**, **Học máy giải thích được trên dữ liệu NHANES 2021–2023**, **RAG (ChromaDB + `intfloat/multilingual-e5-small`)** và **Diabetes Knowledge Graph (Neo4j / Local JSON Mirror)** nhằm hỗ trợ sàng lọc nguy cơ chỉ dấu đường huyết `HbA1c ≥ 5.7%` và giải đáp kiến thức y khoa chuẩn hóa bằng tiếng Việt.

> **Lưu ý y khoa:** Kết quả từ mô hình học máy và chatbot chỉ mang tính chất **sàng lọc tham khảo và giáo dục sức khỏe**, không thay thế chẩn đoán lâm sàng, xét nghiệm máu (HbA1c, FPG, OGTT) hoặc chỉ định điều trị của bác sĩ.

---

## 1. Tổng quan Kiến trúc Hệ thống

### 1.1. Luồng điều phối 5-Agent (`ai_services/orchestration/graph.py`)
1. **Orchestrator Agent (`orchestrator`)**: Phân loại ý định người dùng (đánh giá nguy cơ, hỏi đáp tri thức, chuyển hướng sang màn hình sàng lọc), kiểm tra lớp an toàn y khoa (Medical Safety Guardrails) và điều phối nhánh thực thi.
2. **Data Analysis Agent (`data_analysis`)**: Kiểm tra tính hợp lệ và phạm vi sàng lọc của bộ dữ liệu NHANES (người trưởng thành `20–80 tuổi`, chưa từng được chẩn đoán tiểu đường, không mang thai), đồng thời tính toán các chỉ số dẫn xuất (`BMI`, `WHtR`, `WHR`). Nếu hồ sơ nằm ngoài phạm vi (`out_of_scope`), luồng dừng trước khi chấm điểm ML.
3. **Prediction Agent (`prediction`)**: Tải mô hình `nhanes_hba1c_v2.joblib` kèm kiểm tra toàn vẹn chữ ký **SHA-256** từ `model_manifest.json`, dự báo xác suất `HbA1c ≥ 5.7%`, phân tầng 3 mức nguy cơ (`low` < `0.245`, `moderate` `0.245–0.31`, `elevated` ≥ `0.31`), và tính đóng góp cục bộ từng đặc trưng (`feature_contributions`).
4. **Knowledge Agent (`knowledge`)**: Truy xuất ngữ nghĩa từ **ChromaDB** (`intfloat/multilingual-e5-small`, 384 chiều) kết hợp truy vấn quan hệ từ **Diabetes Knowledge Graph** (`neo4j` hoặc `local_mirror`), tự động lọc theo danh sách tài liệu đang kích hoạt (`active`) trong CSDL.
5. **Consultation Agent (`consultation`)**: Tổng hợp giải thích tiếng Việt có trích dẫn nguồn (`[1]`, `[2]`...) qua LLM (`Ollama` / `Gemini` / `OpenAI`), tự động chuyển sang **Offline Deterministic Template Fallback** khi LLM không khả dụng để đảm bảo hệ thống luôn phản hồi ổn định và không bịa đặt dữ liệu.

### 1.2. Mô hình Học máy NHANES v2 (`ml_pipeline/`)
- **Nguồn dữ liệu**: NHANES August 2021–August 2023 (`DEMO_L`, `BMX_L`, `DIQ_L`, `GHB_L`), tổng `4,698` mẫu hợp lệ (`3,288` train / `705` val / `705` test).
- **6 đặc trưng đầu vào**: `RIDAGEYR` (Tuổi), `RIAGENDR` (Giới tính), `BMXBMI` (BMI), `BMXWAIST` (Vòng eo), `WHtR` (Vòng eo / Chiều cao), `WHR` (Vòng eo / Vòng hông).
- **So sánh hiệu năng với Baseline GĐ3** (`ml_pipeline/artifacts/comparison_report.json`):
  - **Test ROC-AUC**: `0.7532` (v2, 6 features) so với `0.7406` (GĐ3, 3 features) — tăng `+0.0126`.
  - **Test Average Precision**: `0.5205` so với `0.5118`.
  - **Test Brier Score**: `0.1752` so với `0.1785` (hiệu chỉnh xác suất tốt hơn).

### 1.3. Hybrid Knowledge Base & Medical Safety Guardrails
- **7 tài liệu y khoa gốc được chuẩn hóa**: CDC, NIDDK, WHO và Hệ thống Nhà thuốc Long Châu (tự động nạp vào ChromaDB và SQL khi khởi động lần đầu). Quản trị viên có thể tải thêm `.pdf`, `.txt`, `.md`, bật/tắt trạng thái `active`/`inactive`, hoặc xóa tài liệu trực tiếp trên giao diện `/admin`.
- **An toàn y khoa (`ai_services/safety/guardrails.py`)**: Nhận diện và chặn yêu cầu kê đơn thuốc (`prescription_request`), yêu cầu khẳng định chẩn đoán (`diagnosis_override`), phát hiện prompt injection (`prompt_injection`), cảnh báo khẩn cấp (`emergency`), và làm sạch nội dung tài liệu trước khi đưa vào prompt LLM.

---

## 2. Cấu trúc Thư mục Monorepo

```text
Multi_Agent_Project1/
├── ai_services/                  # LangGraph 5-Agent, ML Predictor, Hybrid RAG+KG, Safety, LLM Factory
├── backend/                      # FastAPI Modular Monolith (Auth JWT, Assessments, Chat, Knowledge, Admin)
│   ├── app/                      # Core config, SQLAlchemy models, routers, services
│   └── tests/                    # Bộ kiểm thử pytest (ML, Agents, Safety, Knowledge, API E2E)
├── frontend/                     # React 18 + TypeScript + Vite + Tailwind CSS + Recharts (7 màn hình)
├── ml_pipeline/                  # Pipeline huấn luyện NHANES v2 & artifacts đã xác thực SHA-256
├── infrastructure/               # docker-compose.yml (PostgreSQL 16 + profiles backend/frontend)
├── data/                         # SQLite DB, ChromaDB persist, KG JSON mirror, uploads (tự tạo khi chạy)
├── docs/                         # Tài liệu đặc tả kiến trúc & kế hoạch triển khai
├── GĐ2/                          # Kho lưu trữ nghiên cứu Giai đoạn 2 (giữ nguyên chỉ đọc)
├── GĐ3/                          # Kho lưu trữ nghiên cứu & mô hình Giai đoạn 3 (giữ nguyên chỉ đọc)
├── Giai-doan-4-Bo-sung-Nha-thuoc-Long-Chau/          # Nguồn tri thức y khoa chuẩn hóa (giữ nguyên)
├── Giai-doan-5-Buoc-1-Contracts-Environment-Audit/   # Hợp đồng & kiểm tra môi trường GĐ5 (giữ nguyên)
├── .env.example                  # Mẫu biến môi trường cho Local / Ollama / Gemini / OpenAI / Postgres / Neo4j
└── pytest.ini                    # Cấu hình pytest
```

---

## 3. Hướng dẫn Cài đặt & Chạy nhanh (Windows PowerShell)

### Yêu cầu môi trường
- **Python 3.13+** (đã kiểm thử trên Python 3.13.9)
- **Node.js 22+** & **npm 10+**
- **Ollama** (tùy chọn cho LLM cục bộ) hoặc **Docker Desktop** (tùy chọn cho PostgreSQL / Neo4j)

### Bước 1: Tạo tệp cấu hình `.env`
```powershell
Copy-Item .env.example .env
```
*(Mặc định `.env` sử dụng SQLite tại `data/diabetes_app.db`, mô hình embedding `intfloat/multilingual-e5-small` và `LLM_PROVIDER=ollama`. Nếu Ollama chưa bật, hệ thống tự động dùng template tiếng Việt chuẩn hóa.)*

### Bước 2: Cài đặt thư viện (nếu môi trường chưa có)
```powershell
pip install -r backend/requirements.txt
npm --prefix frontend install
```

### Bước 3: Khởi động Backend (FastAPI)
Mở terminal PowerShell tại thư mục gốc dự án:
```powershell
uvicorn backend.app.main:create_app --factory --reload --port 8000
```
- API Docs (Swagger UI): `http://127.0.0.1:8000/docs`
- Healthcheck: `http://127.0.0.1:8000/api/v1/health`

### Bước 4: Khởi động Frontend (React + Vite)
Mở terminal PowerShell thứ hai tại thư mục gốc dự án:
```powershell
npm --prefix frontend run dev
```
Truy cập ứng dụng tại: **`http://localhost:5173`**

### Tài khoản Demo (tự động tạo khi khởi động lần đầu)
| Vai trò | Email | Mật khẩu | Chức năng chính |
| :--- | :--- | :--- | :--- |
| **Người dùng (User)** | `user@demo.local` | `DemoUser123!` | Tổng quan, Sàng lọc 5-Agent, Chatbot RAG+KG, Khám phá Đồ thị Tri thức, Lịch sử |
| **Quản trị viên (Admin)** | `admin@demo.local` | `DemoAdmin123!` | Toàn bộ tính năng User + Quản trị Tài liệu RAG, Giám sát Multi-Agent, Quản lý Người dùng (`/admin`) |

*(Trên màn hình Đăng nhập có sẵn 2 nút **Demo User** và **Demo Admin** để điền nhanh thông tin.)*

---

## 4. Cấu hình LLM (Ollama / Gemini / OpenAI)

### 4.1. Sử dụng Ollama cục bộ (Mặc định)
```powershell
ollama pull qwen2.5:1.5b
ollama serve
```
Đảm bảo trong `.env`:
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:1.5b
OLLAMA_TIMEOUT_SECONDS=45
```

### 4.2. Chuyển đổi sang Google Gemini
Cập nhật `.env` và khởi động lại backend:
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### 4.3. Chuyển đổi sang OpenAI (hoặc endpoint tương thích OpenAI)
Cập nhật `.env` và khởi động lại backend:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=
```

---

## 5. Chạy PostgreSQL & Neo4j với Docker Compose (Tùy chọn)

### 5.1. Khởi động PostgreSQL 16 cho Backend
```powershell
docker compose -f infrastructure/docker-compose.yml up -d postgres
```
Sau đó mở comment dòng PostgreSQL trong `.env`:
```env
DATABASE_URL=postgresql+psycopg://diabetes:diabetes@localhost:5432/diabetes_app
```
Hoặc khởi động toàn bộ các service (`postgres`, `backend`, `frontend`) bằng profile `full`:
```powershell
docker compose -f infrastructure/docker-compose.yml --profile full up -d
```

### 5.2. Kết nối Neo4j (Tùy chọn)
Khi không cấu hình Neo4j, hệ thống tự động sử dụng **Local JSON Mirror** (`data/knowledge_graph/diabetes_kg.json`). Nếu muốn dùng Neo4j Aura hoặc Neo4j Desktop/Docker, cài gói `neo4j` và điền vào `.env`:
```env
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

---

## 6. Kiểm thử Tự động & Build Production

```powershell
# Chạy toàn bộ test backend (ML, Safety, Hybrid Knowledge, Multi-Agent, FastAPI E2E)
python -m pytest -v

# Kiểm tra TypeScript và đóng gói production Frontend
npm --prefix frontend run build
```

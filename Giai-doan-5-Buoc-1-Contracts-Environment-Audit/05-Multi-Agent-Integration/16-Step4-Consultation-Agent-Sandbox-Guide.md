# Giai đoạn 5 — Bước 4: Consultation Agent Sandbox (Atlas)

**Mục tiêu:** Kiểm thử riêng Consultation Agent với **dữ liệu hư cấu Atlas**; chưa ghép năm Agent, chưa truy cập kho tri thức y khoa, không truy cập mô hình NHANES. Giữ medical Knowledge Gate `BLOCKED_RESEARCH_ONLY` trong suốt thử nghiệm.

## 1. Thành phần và điều kiện trước khi chạy

- `phase5/step4_consultation.py`: hợp đồng Consultation Agent, khóa danh sách 6 câu hỏi, dữ liệu giả lập và kiểm tra trích dẫn.
- `phase5/step4_run.py`: giao diện dòng lệnh và xuất JSON.
- `phase5/step4_self_test.py`: bộ unit test offline.
- `data/sandbox/step4_atlas_synthetic.json`: ba đoạn Atlas hư cấu, được kiểm tra nội dung chính xác trước khi sử dụng.
- `15-Step3-Live-Results.md`: số liệu Bước 3 do người dùng chạy.

**Không cần chạy lại FastAPI, Neo4j hoặc ChromaDB ở Bước 4.** Bước 4 tách riêng để phòng ngừa gửi nội dung nguồn y khoa chưa duyệt tới LLM. Khi tích hợp năm Agent ở Bước 5, ranh giới này sẽ phải tiếp tục được kiểm tra.

## 2. Cài đặt trong VS Code / PowerShell

Giải nén vào thư mục **cha** đang chứa `05-Multi-Agent-Integration`, rồi mở PowerShell **tại** thư mục `05-Multi-Agent-Integration`. Gói Step 4 chỉ bổ sung tệp mới; không chép đè `config/phase5_step1_config.json`.

### A. Test offline, không mạng, không LLM

```powershell
python -m phase5.step4_self_test
```

Kỳ vọng: `Ran 17 tests` và `OK`.

### B. Chạy thử trên metadata/response giả lập

```powershell
python -m phase5.step4_run --mode mock
```

Kỳ vọng:

```text
Mode: mock | Dataset: SYN-ATLAS-RAG-05M-v1
Preflight: 6/6 | blocked before LLM: 3/3 | LLM attempts: 0
S01: MOCK_RESPONSE_NOT_LLM | citations=SYN-ATLAS-001 | errors=none
S02: MOCK_RESPONSE_NOT_LLM | citations=SYN-ATLAS-002 | errors=none
S03: MOCK_RESPONSE_NOT_LLM | citations=SYN-ATLAS-003 | errors=none
S04: ABSTAIN_NO_EVIDENCE | citations=- | errors=none
S05: ABSTAIN_UNSAFE_REQUEST | citations=- | errors=none
S06: ABSTAIN_MEDICAL_REQUEST | citations=- | errors=none
Status: technical_pass_mock_only
```

**Lưu ý:** Ba câu trả lời trong `mock` là câu được cố định trong mã để kiểm tra hợp đồng, **không phải** nội dung LLM tạo ra.

### C. Gọi Ollama trên localhost — bước do bạn chủ động thực hiện

Kiểm tra Ollama đã cài và có model cũ đã tải ở Giai đoạn 4:

```powershell
ollama list
```

Nếu chưa có model `qwen2.5:1.5b` thì mới tải (cần mạng internet):

```powershell
ollama pull qwen2.5:1.5b
```

Đảm bảo Ollama đang hoạt động trên `http://127.0.0.1:11434`. Sau đó chạy:

```powershell
python -m phase5.step4_run --mode ollama --model qwen2.5:1.5b
```

Chỉ S01, S02, S03 được gửi tới LLM. S04, S05, S06 bị chặn trước khi gọi model. Script không gọi ChromaDB, Neo4j, FastAPI prediction, không huấn luyện ML. LLM chỉ được yêu cầu dùng Atlas hư cấu. Với đầu ra hợp lệ, trạng thái là `LLM_OUTPUT_NEEDS_HUMAN_REVIEW`, **không phải phê duyệt nội dung**.

## 3. Mục tiêu khi chạy LLM trên máy người dùng

| Chỉ số | Mục tiêu |
|---|---:|
| Preflight | 6/6 |
| Block trước LLM (S04–S06) | 3/3 |
| LLM attempts | 3 |
| Có trả lời + citation hợp lệ về cấu trúc cho S01–S03 | 3/3 |
| Medical KB accessed | false |
| Medical knowledge gate | `BLOCKED_RESEARCH_ONLY` |
| Chroma/Neo4j modified / ML training | false / false |
| Manual content review | pending cho đến khi người dùng đối chiếu |

Nếu Ollama không chạy hoặc response không đúng JSON/chunk ID, báo cáo có `ABSTAIN_LLM_ERROR` và status `sandbox_incomplete_or_llm_error`. Điều này **không phải** dữ liệu y khoa bị mở khóa.

## 4. Báo cáo kết quả

File được tạo tại:

`data/outputs/phase5_step4/step4_consultation_report.json`

Cả `mock` và `ollama` cùng sử dụng đường dẫn này, vì vậy hãy gửi báo cáo của lệnh chạy cuối cùng. Có thể lưu bản mock riêng trước khi chạy Ollama nếu cần so sánh.

**Hãy gửi:** output `step4_self_test`, `step4_run --mode mock`, `step4_run --mode ollama` và file JSON cuối cùng. Không gửi mật khẩu, token hay tệp credentials.

## 5. Giới hạn và an toàn

- Bộ kiểm thử chỉ gồm **sáu câu cố định**. Nó không phải bộ lọc prompt injection hoàn chỉnh, không đảm bảo mọi loại câu hỏi khác được xử lý đúng.
- Kiểm tra citation chỉ xác nhận đúng ID bằng chứng; phải kiểm tra thủ công nội dung câu trả lời có thực sự được nguồn Atlas hỗ trợ không.
- Script chủ động từ chối corpus bị chỉnh sửa, tuy vậy đây là biện pháp thử nghiệm, không thay thế sandbox bảo mật hoặc phân quyền.
- Không sử dụng RAG để tạo lời khuyên về liều thuốc, chẩn đoán hay đánh giá bệnh cho người thật.
- Nếu mật khẩu Neo4j từng được chia sẻ, đổi mật khẩu đó trước khi chuyển sang sử dụng các dịch vụ trong Giai đoạn 5; không lưu secret trong JSON.

**Sau Bước 4** sẽ là Bước 5: LangGraph Orchestrator + FastAPI (5 Agent). Chưa có endpoint tích hợp chính thức ở Bước 4.

# Giai đoạn 4 — Bước 5M: RAG Answering Sandbox

## 1. Mục tiêu

- Tự chạy một luồng **retrieve → evidence gate → (tùy chọn) local LLM → citation check**.
- Học cách từ chối khi không có bằng chứng, yêu cầu ngoài phạm vi, và đầu vào cố ý vượt quyền.
- Lưu kết quả vào JSON để phân tích và chuẩn bị **Giai đoạn 4 — Bước 6**.
- Tuyệt đối không mở khóa tài liệu y khoa chưa được kiểm định.

**Giới hạn:** Dữ liệu hư cấu “Atlas” hoàn toàn tách biệt khỏi ChromaDB (66 chunks), Neo4j và mô hình ML. Đây là RAG kỹ thuật dạng sandbox dùng lexical retrieval, **không phải** GraphRAG thật hay đánh giá chất lượng medical RAG. Phát hiện prompt injection bằng từ khóa chỉ là mô phỏng, chưa đủ cho production.

## 2. Cấu trúc tệp

```text
04-Knowledge-Base-RAG/
├── tools/05M_rag_answering_sandbox.py
├── data/sandbox/05M_synthetic_kb.json
├── registry/05M_sandbox_test_cases.json
├── 05M-RAG-Answering-Sandbox-Guide.md
├── 05L-Safe-Retrieval-Results.md
└── data/outputs/rag_sandbox_step5m/   # xuất hiện khi bạn chạy
```

## 3. Bước A — Tự kiểm tra logic trước khi bật LLM

Mở **VS Code → Terminal / PowerShell** tại thư mục `04-Knowledge-Base-RAG` chứa `tools/`, `registry/`, `data/`.

```powershell
python .\tools\05M_rag_answering_sandbox.py --self-test
```

Mong đợi `SELF-TEST: PASS` và `6/6` case; script không ghi database, không gọi API, không tạo report.

Chạy một vòng không dùng LLM:

```powershell
python .\tools\05M_rag_answering_sandbox.py --mode dry-run
```

Tạo `data/outputs/rag_sandbox_step5m/step5m_rag_sandbox_report.json`.

## 4. Bước B — Tùy chọn: dùng Ollama cục bộ để sinh câu trả lời

Chỉ làm bước này sau khi bạn chủ động quyết định sử dụng LLM. Không cần OpenAI API key.

1. Cài Ollama từ website chính thức: https://ollama.com/download
2. Mở PowerShell:

```powershell
ollama --version
ollama pull qwen2.5:1.5b
ollama list
```

3. Đảm bảo Ollama đang chạy tại `http://127.0.0.1:11434`. Trên Windows thường có thể khởi động Ollama từ Start Menu; nếu không có server, mở cửa sổ terminal riêng chạy `ollama serve`.
4. Ở cửa sổ terminal dự án, chạy:

```powershell
python .\tools\05M_rag_answering_sandbox.py --mode ollama --model qwen2.5:1.5b
```

Mã gọi local `POST /api/chat` với `stream:false`, `format:"json"`, `temperature:0`. Không gửi dữ liệu 7 nguồn y khoa hay dữ liệu bệnh nhân tới mô hình. Với `qwen2.5:1.5b`, chất lượng ngôn ngữ có thể giới hạn; có thể thay mô hình cục bộ, ghi rõ phiên bản trong báo cáo.

## 5. Bộ kiểm thử 6 tình huống

| Case | Loại | Kỳ vọng trước LLM |
|---|---|---|
| S01 | Hỏi các module Atlas | Có bằng chứng `SYN-ATLAS-001` |
| S02 | Chính sách dữ liệu giả lập | Có bằng chứng `SYN-ATLAS-002` |
| S03 | Từ chối khi thiếu dữ liệu | Có bằng chứng `SYN-ATLAS-003` |
| S04 | Câu hỏi ngoài phạm vi | `ABSTAIN_NO_EVIDENCE` |
| S05 | Cố gắng vượt hướng dẫn | `ABSTAIN_UNSAFE_REQUEST` |
| S06 | Đòi tư vấn insulin | `ABSTAIN_MEDICAL_REQUEST` |

Với mode Ollama, chỉ S01–S03 mới được gửi vào model cục bộ. LLM phải xuất JSON với `answer` và `citations`; code kiểm tra `citations` là các chunk ID thuộc kết quả retrieval. Tuy nhiên, việc có citations hợp lệ chưa đủ chứng minh nội dung đúng: **bạn phải đọc và đối chiếu từng câu trả lời**.

## 6. Mẫu đánh giá thủ công sau khi chạy Ollama

- [ ] S01: câu trả lời đúng ba module; dẫn `SYN-ATLAS-001`; không thêm chức năng tưởng tượng.
- [ ] S02: nói chỉ dùng dữ liệu giả lập; dẫn `SYN-ATLAS-002`; không thêm chính sách không có trong bằng chứng.
- [ ] S03: mô tả từ chối khi thiếu bằng chứng; dẫn `SYN-ATLAS-003`.
- [ ] S04–S06: không gọi LLM và từ chối đúng loại.
- [ ] Không có URL hay đoạn nội dung từ 7 nguồn thật, không có thông tin cá nhân.
- [ ] Kiểm tra `llm_status` trong report: nếu local Ollama lỗi, không ghi nhận là PASS sinh câu trả lời.

## 7. Điều kiện nghiệm thu 5M

- Self-test logic 6/6, báo cáo JSON ghi đúng trạng thái.
- Nếu chọn chạy Ollama: kiểm tra đủ ba ca có bằng chứng, trích dẫn ID hợp lệ, và chấm nội dung thủ công.
- Đầu vào không phù hợp vẫn được chặn; real Knowledge Base vẫn có trạng thái `BLOCKED_RESEARCH_ONLY`.
- Không tự gọi kết quả là “đã kiểm định y khoa” hoặc “production-ready”.

Sau khi hoàn thành, gửi **output và file** `step5m_rag_sandbox_report.json`. Chuyển Giai đoạn 4 Bước 6: đánh giá end-to-end trên bộ giả lập, rà soát quyền nguồn thực và tổng kết thành báo cáo Markdown.

## 8. Tài liệu kỹ thuật

- Ollama official API: https://docs.ollama.com/api (API chat, non-streaming)
- Qwen2.5 local model catalog: https://ollama.com/library/qwen2.5 (có hỗ trợ tiếng Việt; kích thước model khác nhau)

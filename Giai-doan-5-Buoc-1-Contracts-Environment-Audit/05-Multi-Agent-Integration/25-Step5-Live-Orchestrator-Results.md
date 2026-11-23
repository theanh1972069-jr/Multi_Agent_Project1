# Giai đoạn 5 – Kết quả thực tế Bước 5 (Orchestrator LangGraph)

**Nguồn:** Tệp người dùng cung cấp `step5_orchestrator_report.json`, `experiment=EXP-PHASE5-STEP5-001`, thời gian báo cáo UTC `2026-11-03T17:48:38.230505+00:00`. Những giá trị bên dưới được trích từ báo cáo; không phải benchmark được chạy lại trong môi trường soạn.

## Kết quả

| Nhánh | Chạy thật hay giả lập? | Ca đạt | Bằng chứng / cách ly |
|---|---|---:|---|
| Data Analysis → Prediction | Live tới FastAPI NHANES localhost | 2/2 | Hai trường hợp đúng SHA256, không gọi LLM, không trả metadata tri thức |
| Knowledge Retrieval | Live ChromaDB + Neo4j Aura | 3/3 | Mỗi câu trả 3 metadata, 9/9 provenance, trạng thái `blocked_research_only` |
| Consultation Atlas | Mock trong Orchestrator | 6/6 | S01–S03 có mã nguồn giả lập, S04–S06 `abstained`, không gọi LLM |
| Tổng | `mode=live`, `consultation_mode=mock` | **11/11** | `orchestrator_live_technical_pass` |

**Bất biến an toàn:** `medical_knowledge_gate=BLOCKED_RESEARCH_ONLY`; không tạo câu trả lời y khoa, không ghi database, không train ML.

## Điều đã chứng minh và chưa chứng minh

- Đã chứng minh ba nhánh route chạy qua LangGraph; nhánh dự đoán & tri thức kết nối backend thật, nhánh Atlas mock.
- Chưa kiểm thử Ollama **bên trong Step 5 Orchestrator**. Bước 4 đã gọi Ollama thật riêng rẽ (`3` attempts), cần ghi rõ hai phạm vi khác nhau.
- Bước 4 có đánh giá nội dung **sơ bộ** trên ba câu Atlas; báo cáo chưa có `manual_review_complete=true` nên một cuộc xác nhận thủ công vẫn cần để nghiệm thu nội dung.
- Không chứng minh mô hình NHANES dự báo tiểu đường tương lai, không chứng minh phân quyền production hay kiểm duyệt y khoa/copyright.

**Quyết định:** Bước 5 đạt nghiệm thu kỹ thuật trong phạm vi thử nghiệm. Tiếp tục Bước 6 – kiểm tra HTTP API localhost, nhất quán báo cáo, đánh giá Atlas thủ công và tổng kết.

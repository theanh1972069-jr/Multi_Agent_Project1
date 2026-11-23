# Giai đoạn 5 – Bước 6: Ma trận kiểm thử và tiêu chí

| ID | Phạm vi | Nguồn dữ liệu | Đạt khi | Trạng thái hiện tại |
|---|---|---|---|---|
| E2E-01 | Prediction | Step2 live JSON | 2/2, hash & threshold match, gate blocked | Đã thấy báo cáo người dùng, audit Step6 chờ chạy |
| E2E-02 | Knowledge | Step3 live JSON | 7 sources, 66 chunks, 9/9 provenance, không medical answer | Đã thấy báo cáo người dùng, audit Step6 chờ chạy |
| E2E-03 | Consultation standalone | Step4 Ollama JSON | 6/6 preflight, 3/3 chặn, 3 citation Atlas | Đã thấy báo cáo người dùng, human review chờ xác nhận |
| E2E-04 | 5-Agent Orchestrator | Step5 live + mock JSON | 11/11, 2 Pred + 3 Know + 6 Atlas, gate blocked | **Đạt thực tế theo báo cáo người dùng** |
| E2E-05 | FastAPI localhost | Step6 HTTP smoke | 8/8, status 200/422 đúng, mock | Chưa chạy trên máy người dùng |
| E2E-06 | Human groundedness review | Step6 CSV | S01–S03 khớp nguồn, reviewer & UTC có thật | Chưa xác nhận |
| E2E-07 | Optional Ollama inside Orchestrator | Step5 live + Ollama JSON riêng | 11/11, 3 LLM calls chỉ trên Atlas | Chưa chạy; không bắt buộc để nghiệm thu *phạm vi giới hạn* |
| E2E-08 | Clinical/rights clearance | External review | Độc lập, ghi nguồn bằng chứng và thẩm định chuyên gia | **Không đạt/chưa thực hiện; không nằm trong phạm vi nghiệm thu kỹ thuật** |

Phạm vi Bước 6 gồm **kiểm tra báo cáo và smoke test localhost**, không phải full production/security/clinical E2E. Báo cáo đóng giai đoạn cần chỉ rõ những mục chờ ngoài phạm vi thay vì tự suy ra đạt.

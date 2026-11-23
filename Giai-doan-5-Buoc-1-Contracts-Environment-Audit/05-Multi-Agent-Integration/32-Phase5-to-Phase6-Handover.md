# GIAI ĐOẠN 5 → GIAI ĐOẠN 6: BIÊN BẢN BÀN GIAO

**Ngày:** 2026-11-04  
**Trạng thái:** Giai đoạn 5 đóng ở mức `research_sandbox_only`; Giai đoạn 6 chưa có UI thực thi.

## 1. Thành phần bàn giao

- Backend FastAPI nghiên cứu `phase5/step5_api.py`, cấu hình mặc định local-only `127.0.0.1:8001`.
- LangGraph `phase5/step5_orchestrator.py`, hợp đồng `Step5Request`, `Step5Response`.
- Prediction từ FastAPI nghiên cứu NHANES ở `127.0.0.1:8000` (khi chạy live).
- Knowledge read-only từ ChromaDB/Neo4j; `BLOCKED_RESEARCH_ONLY` và 0 approved claims.
- Consultation chỉ được dùng Ollama cho Atlas giả lập.
- 6 báo cáo thực nghiệm và báo cáo nghiệm thu trong gói ZIP.

## 2. API interface cần giữ nguyên

`GET /health/live`, `GET /health/ready`, `POST /api/v1/research/agents/run` ở port 8001.

Các operation được phép:

- `research_prediction`: `features={RIDAGEYR,RIAGENDR,BMXBMI}`, chỉ dùng input giả lập và diễn giải là chỉ báo nghiên cứu HbA1c.
- `knowledge_research_lookup`: chỉ `query_id=Q01|Q02|Q03`, trả metadata + blocked.
- `synthetic_rag_demo`: chỉ `case_id=S01..S06`, trả câu trả lời Atlas giả lập (mock / Ollama có kiểm soát).

Trường `synthetic_test_only=true` bắt buộc; `medical_gate` do server sở hữu và client không được gán. HTTP 422 cho payload bị từ chối.

## 3. Chốt phạm vi cho Giai đoạn 6

**Theo Technical Design Giai đoạn 2:** xây dựng tích hợp Web + Mobile chung backend. React + TypeScript đã được thiết kế; Mobile **chưa chốt Flutter hay native**.

Trước khi code UI production, phải thiết kế authentication/authorization, CORS/CSRF hợp lý, session, database nghiệp vụ và phân tách môi trường; không tự biến local sandbox :8001 thành public API.

**Đề xuất đường đi an toàn:** API contract audit → React Web sandbox trên localhost → UI và kiểm thử API mock → chọn mobile framework → Mobile sandbox → kiểm tra đầu-cuối và tổng kết.

## 4. Chưa đạt và tuyệt đối không mặc định đã có

- Người dùng thật / tài khoản / lịch sử / database PostgreSQL nghiệp vụ production.
- Dữ liệu y khoa thật đã được phép đưa vào chatbot.
- Đánh giá độ chính xác/hiệu năng theo tiêu chuẩn y tế.
- Bảo vệ trước injection tùy ý, penetration test hay multi-user authorization.
- Chạy Orchestrator + Ollama live cùng nhau (chưa có báo cáo Step5 tùy chọn).

**Lưu ý về chứng cứ:** E2E test chỉ đối chiếu JSON có sẵn, không mở mạng. `Manual review pass 3/3` đến từ báo cáo JSON cuối do người dùng thực thi.

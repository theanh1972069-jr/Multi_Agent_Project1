# GIAI ĐOẠN 6 — LỘ TRÌNH TÍCH HỢP WEB / MOBILE

**Dự án:** Multi-Agent AI System for Diabetes Risk Assessment  
**Ngày lập kế hoạch:** 2026-11-04  
**Cơ sở:** Giai đoạn 2 — `06-Technical-Design.md` (trình tự Giai đoạn 6 Web/Mobile); Giai đoạn 5 đã đóng ở mức nguyên mẫu nghiên cứu.

> Giai đoạn 6 **chưa triển khai**. Đây là lộ trình đề xuất dựa trên thiết kế trước đó, không phải bằng chứng các chức năng đã được xây dựng.

## 1. Mục tiêu

- Một UI Web React + TypeScript làm client cho cùng API nghiên cứu, dùng dữ liệu **giả lập**, phát hiện và giải thích các trạng thái `blocked_research_only`, `abstained`, `failed`.
- Một client Mobile dùng cùng hợp đồng REST API; framework Flutter hoặc native Kotlin/Swift **sẽ được chốt khi bắt đầu nhánh Mobile**, không tự áp đặt.
- Tách biệt UI khỏi Model, Neo4j, ChromaDB và Ollama; ứng dụng không kết nối các thành phần backend trực tiếp.
- **Không** tạo UI tự tin chẩn đoán bệnh, kê đơn hay xử lý bệnh án thật khi chưa có xác minh lâm sàng/rights và bảo mật.

## 2. Sáu bước có điểm dừng

| Bước | Công việc | Điều kiện nghiệm thu |
|---|---|---|
| 1. Client API Contract & UX Safety | Kiểm tra OpenAPI `:8001`, thống nhất DTO request/response, trạng thái UI, xử lý từ chối/422, nguyên tắc localhost | Bản contract mapping, mock API kiểm tra thành công, không sửa backend |
| 2. React Web Sandbox | Tạo dự án React + TypeScript, trang demo 3 operation và feedback rõ ràng | Web hoạt động với API mock local, có màn hình blocked/abstain |
| 3. Web–Backend Integration | Gọi FastAPI :8001 local qua adapter, xử lý lỗi offline/timeout; bảo đảm không leak secrets | E2E smoke có ít nhất các ca 200/422, blocked, offline; không cần backend live |
| 4. Mobile Architecture & Prototype | Chọn Flutter hay Kotlin Android native; dùng chung API schema; mô phỏng cùng flows | Mobile emulator render đủ ba luồng/screen states, không dùng bệnh án thật |
| 5. Mobile–Backend Integration | Kiểm tra chạy emulator/simulator và network localhost đúng cấu hình; xử lý trạng thái fail-closed | Các kịch bản giống Web; không để server public không auth |
| 6. Web/Mobile E2E & Report | Đánh giá UX, correctness, security checklist và tất cả test thực tế | Báo cáo có kết quả người dùng chạy; ghi rõ còn thiếu auth/clinical review |

## 3. Hợp đồng API thực tế cần dùng

**Backend đang có:** `POST http://127.0.0.1:8001/api/v1/research/agents/run` (`phase5/step5_api.py`).

**Ba operation:** `research_prediction` (features `RIDAGEYR`, `RIAGENDR`, `BMXBMI`), `knowledge_research_lookup` (`Q01–Q03`), `synthetic_rag_demo` (`S01–S06`). Request bắt buộc `synthetic_test_only: true` và `request_id`. Server từ chối trường tự gán `medical_gate`.

Response `Step5Response` có `status`, `medical_gate`, `prediction`, `evidence_metadata`, `synthetic_answer`, `synthetic_citations`, `llm_called`, `error_codes`, `warning`. Khách hàng phải sử dụng **đúng response schema thực tế** thay vì bản `06-API-Contract-Draft.yaml` của Giai đoạn 2 (bản đó chỉ là thiết kế).

## 4. Quy tắc an toàn giao diện

1. Hiển thị banner **“Nghiên cứu / Dữ liệu giả lập — không dùng để chẩn đoán”**.
2. Không hỏi tên, email, hồ sơ sức khỏe hay chi tiết định danh của người bệnh cho sandbox.
3. `knowledge_research_lookup` chỉ được hiển thị metadata và trạng thái `blocked_research_only`; không tạo lời khuyên y khoa.
4. `research_prediction` phải mô tả đúng là phân loại chỉ báo HbA1c ≥5,7% trong nghiên cứu, không dự báo bệnh type 2 về sau.
5. `synthetic_rag_demo` phải ghi rõ trả lời về phần mềm Atlas giả lập, không phải nội dung y khoa.
6. Giữ server bind `127.0.0.1`; emulator/device thật không dùng API public không auth để kết nối.
7. Không đưa mật khẩu Aura, khóa API, model checkpoint hoặc data người dùng vào frontend/mobile build.

## 5. Kỹ thuật cần quyết định trước khi công khai

- Backend **chưa hỗ trợ CORS cho trình duyệt Web dev server**: cần whitelist rõ `localhost` theo đúng origin hoặc dev proxy local, không `allow_origins=['*']` kèm credentials.
- Không có auth/user ownership, rate limits, dữ liệu lịch sử PostgreSQL production, privacy controls đủ cho người dùng thật.
- Cần chuẩn hóa status và error code cho Web và Mobile; lưu OpenAPI snapshot khi contract ổn định.
- Nếu dùng điện thoại thật khác máy: `127.0.0.1` sẽ trỏ về chính điện thoại; tránh đổi server thành `0.0.0.0` chỉ để thử khi chưa có bảo vệ. Ưu tiên emulator hoặc mô phỏng/mock.

## 6. Bước sẽ làm ngay

**Giai đoạn 6 – Bước 1:** kiểm tra route + OpenAPI hiện có trên `127.0.0.1:8001` ở chế độ mock, ghi lại response và map các màn hình (Prediction, Knowledge Blocked, Atlas Sandbox). Tiếp đó mới tạo React Web UI. Lựa chọn Mobile sẽ chốt khi bắt đầu Bước 4.

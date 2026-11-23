# GIAI ĐOẠN 5 — BƯỚC 2: TEST MATRIX

| Nhóm | Kiểm tra | Thành công khi |
|---|---|---|
| Schema (6+) | Tuổi, mã giới tính, BMI, unknown gate, synthetic flag | Input sai bị từ chối, không gọi mô hình |
| Upstream mock | Response đúng task/hash/threshold/nhãn | Pydantic validate không lỗi |
| Upstream mock | SHA sai, threshold sai, nhãn sai, warning nguy hiểm | `UPSTREAM_SCHEMA_MISMATCH`; không trả score |
| Upstream mock | Server không sẵn sàng | `UPSTREAM_UNAVAILABLE`; fail closed |
| Security URL | Không cho host bên ngoài/query/fragment | `UNSAFE_API_URL` |
| Mock Graph | `2` fixture qua 5 node; chỉ 2 node đã tích hợp | 2/2 `ok`, no LLM, medical gate blocked |
| Live Graph | `GET /health/ready` và `POST /predict` localhost | 2/2 response đúng hợp đồng, không train |

## Kết quả ở môi trường soạn bộ tài liệu (2026-11-03)

- Cú pháp Python: **PASS** (`py_compile`).
- Unit tests mock (không dùng LangGraph): **16/16 PASS**.
- LangGraph graph compile/invoke: **CHƯA CHẠY tại môi trường soạn** vì không có package `langgraph`; cần chạy trên máy bạn. Không coi các con số mock là kết quả API thực.
- FastAPI live trên máy người dùng: **CHƯA CHẠY** từ đây, cần bạn tự khởi động GĐ3 và gửi output.

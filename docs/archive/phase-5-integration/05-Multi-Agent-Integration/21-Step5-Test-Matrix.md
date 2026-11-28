# Giai đoạn 5 – Bước 5: Test Matrix

| Nhóm | Kiểm tra | Kết quả mong đợi | Tình trạng |
|---|---|---|---|
| Contract | Yêu cầu `synthetic_test_only` | Không có -> 422 / ValidationError | Đã kiểm tra local |
| Contract | Chèn `medical_gate` từ người gọi | 422 / ValidationError | Đã kiểm tra local |
| Contract | `query_id` ngoài Q01–Q03 | Bị từ chối | Đã kiểm tra local |
| Contract | `case_id` ngoài S01–S06 | Bị từ chối | Đã kiểm tra local |
| Contract | Trộn features vào Atlas | Bị từ chối | Đã kiểm tra local |
| Contract | Medical knowledge có `status=ok` | Bị từ chối | Đã kiểm tra local |
| Contract | Citation dùng mã NIDDK trong Atlas | Bị từ chối | Đã kiểm tra local |
| LangGraph | Graph có 5 nodes & 3 routes | Biên dịch và chạy | **Chờ máy người dùng** |
| Graph Mock | 2 prediction route | Thành công bằng mock only | Chờ |
| Graph Mock | 3 knowledge route | 3 × 3 metadata blocked | Chờ |
| Graph Mock | 6 Atlas cases | 3 answers mock, 3 abstain | Chờ |
| Graph Live | 2 prediction route | FastAPI real localhost, đúng hash | Chờ |
| Graph Live | 3 knowledge route | Chroma + Neo4j live, source matched | Chờ |
| Graph Live | 3 Atlas LLM attempts (opt-in) | Cần review thủ công | Chờ |
| HTTP API | `/health/live` | 200 và `alive` | **Đã thử local fake-graph** |
| HTTP API | `/api/v1/research/agents/run` | 200 hợp lệ / 422 input sai | **Đã thử local fake-graph** |

Tại môi trường soạn: `16/16` contract tests đạt, `5` LangGraph tests được **skip** vì thiếu package `langgraph`. Các kết quả graph thật cần lấy trên máy người dùng; không mô tả chúng là đã chạy thành công.

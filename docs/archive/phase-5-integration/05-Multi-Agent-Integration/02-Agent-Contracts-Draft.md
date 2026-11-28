# GIAI ĐOẠN 5 – BƯỚC 1: DỰ THẢO HỢP ĐỒNG AGENT VÀ CHẶN AN TOÀN

**Trạng thái:** Design candidate, **chưa triển khai**. Dùng để viết code LangGraph ở Bước 1.

## 1. AgentState đề xuất

```python
from typing import Literal, NotRequired, TypedDict

class AgentState(TypedDict):
    request_id: str
    operation: Literal["research_prediction", "synthetic_rag_demo"]
    # Chỉ dùng dữ liệu giả lập khi kiểm thử
    raw_input: dict
    validated_input: NotRequired[dict]
    prediction_result: NotRequired[dict]
    evidence_metadata: NotRequired[list[dict]]
    knowledge_gate: Literal["BLOCKED_RESEARCH_ONLY", "NOT_EVALUATED", "SYNTHETIC_READY"]
    final_response: NotRequired[dict]
    errors: list[dict]
    llm_called: bool
```

Quy tắc: Không cần mang toàn văn các tài liệu chưa được duyệt vào state để gửi LLM. Khi debug chỉ giữ `chunk_id`, `source_id`, `url`, trạng thái và mã lỗi phù hợp. Không log input sức khỏe cá nhân.

## 2. API contract và versioning

- **Đã tồn tại trong nghiên cứu Giai đoạn 3**: `POST /api/v1/research/nhanes/hba1c/predict`.
- **Đề xuất cho Giai đoạn 5, CHƯA TRIỂN KHAI**: một API orchestration local `POST /api/v1/research/workflows/assess`; sẽ đối chiếu bản thiết kế `06-API-Contract-Draft.yaml` và chốt khi viết code.
- Prediction result: `indicator_name = hba1c_ge_5_7`, model threshold `0.225`; score do model trả về, LLM không sửa; message luôn ghi rõ 'không phải chẩn đoán hoặc dự báo tương lai'.
- Knowledge result: `metadata_hits[]`, `gate_status`, `review_status`; nếu không phê duyệt thì `answer_text=null`, `llm_called=false` đối với nhánh y khoa.

## 3. Decision table quan trọng

| Điều kiện | Hành vi bắt buộc |
|---|---|
| Đầu vào model thiếu/sai phạm vi | Data Analysis từ chối trước prediction API |
| Prediction API lỗi/mất kết nối | Trả `UPSTREAM_ERROR` có xử lý, không tự tạo score |
| Neo4j hoặc ChromaDB không khả dụng | Knowledge gate `BLOCKED_RESEARCH_ONLY`, không fallback thành mở khóa |
| Nguồn y khoa `draft_unverified` | Không đưa vào Consultation LLM |
| Câu hỏi y khoa cá thể/kê thuốc | Không suy diễn; phản hồi trong phạm vi nghiên cứu hoặc từ chối thích hợp |
| Synthetic Atlas đủ evidence | Có thể cho Ollama chạy sandbox, sau đó kiểm tra citation |
| Prompt yêu cầu bỏ qua Gate | Không thay đổi Gate |

## 4. Test matrix dự kiến (chưa có số liệu)

- Dữ liệu tổng hợp hợp lệ và không hợp lệ đi qua Data Analysis -> Prediction.
- API timeout/500, Neo4j unreachable, Chroma zero hits.
- Evidence `draft_unverified` bị chặn 100% trong các ca thử.
- Prompt injection nằm **trong retrieved content**, không chỉ ở câu hỏi; phải kiểm thử riêng.
- Đảm bảo không log PII, không sửa artifact ML/Chroma/Neo4j trong bài kiểm thử.

## 5. Quy tắc đo lường

Mọi metric và kết luận ở Giai đoạn 5 chỉ ghi vào báo cáo sau khi người thực hành chạy trên máy và gửi output. Đây mới là bản thiết kế và checklist, **không phải kết quả kiểm thử**.

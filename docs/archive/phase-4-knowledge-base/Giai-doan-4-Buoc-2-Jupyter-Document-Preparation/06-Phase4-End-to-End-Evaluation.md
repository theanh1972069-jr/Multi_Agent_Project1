# Giai đoạn 4 – Bước 6: End-to-End Research Evaluation & Final Report

## Mục tiêu

Khóa phạm vi Giai đoạn 4 ở mức **nguyên mẫu nghiên cứu**. Không thêm nhiều bước Neo4j. Đối chiếu các báo cáo đã chạy thật: 5E (Graph Retrieval), 5L (Safe Retrieval), 5M (RAG Sandbox), rồi kiểm tra thủ công nội dung ba câu LLM.

**Không gọi LLM hoặc truy cập database** ở công cụ kiểm tra Bước 6. Chương trình chỉ đọc ba báo cáo JSON và ghi một bản tổng hợp. Đây là *report consistency check*, không phải live E2E test thay người dùng.

## Kết quả đầu vào đã nhận

- ChromaDB: 66 bản ghi, 7 nguồn; Neo4j: 66 `ChunkRef`, 66 `PART_OF`, 0 orphan; Provenance: 9/9 khớp (Bước 5E).
- Bước 5L: 9/9 đối chiếu; Answer Gate `BLOCKED_RESEARCH_ONLY`; 0 approved claims; không có truy vấn LLM.
- Bước 5M: 6/6 preflight; 3 câu có bằng chứng đã được gọi Ollama; 3 câu không phù hợp bị chặn mà không gọi LLM.
- Chưa có kiểm duyệt độc lập nguồn thật; không suy diễn mô hình đã được xác thực lâm sàng.

## Các thao tác người dùng tự thực hiện

**1.** Giải nén file ZIP Bước 6 vào thư mục Giai đoạn 4 đang dùng; không ghi đè các báo cáo cũ.

**2.** Mở `registry/06_manual_answer_review.csv`; đối chiếu các câu S01, S02, S03 với `data/sandbox/05M_synthetic_kb.json` từ bộ Bước 5M, và câu trả lời trong `step5m_rag_sandbox_report.json`. Mỗi dòng điền:

- `answer_fully_supported_yes_no`: `yes` nếu câu trả lời chỉ chứa thông tin có trong đoạn nguồn tương ứng.
- `citation_correct_yes_no`: `yes` khi citation trỏ đúng ID được truy xuất và thực sự hỗ trợ câu.
- `unsupported_claim_found_yes_no`: `no` nếu không có ý thêm ngoài nguồn.
- `reviewer`: tên/mã người thực sự kiểm tra (không ghi giả).
- `reviewed_at_utc`: thời điểm UTC thực tế, ISO 8601, ví dụ định dạng `2026-11-03T14:00:00Z` (chỉ là ví dụ, không dùng thay thời gian thực).
- `notes`: ghi lỗi, sai sót hoặc giới hạn.

**3.** Trong VS Code Terminal, tại thư mục Giai đoạn 4, chạy:

```powershell
python .\tools\06_phase4_e2e_check.py --project-root .
```

Chương trình mong đợi các đường dẫn:

```text
data/outputs/graph_retrieval_step5e/step5e_graph_retrieval_report.json
data/outputs/safe_retrieval_step5l/step5l_safe_retrieval_report.json
data/outputs/rag_sandbox_step5m/step5m_rag_sandbox_report.json
registry/06_manual_answer_review.csv
```

Nếu các báo cáo nằm thư mục khác, chạy với tùy chọn `--step5e`, `--step5l`, `--step5m`, `--manual-review` theo `--help`.

**4.** Gửi `data/outputs/phase4_e2e_step6/step6_phase4_e2e_report.json` và kết quả terminal. Không gửi URI/password Neo4j hoặc dữ liệu bệnh nhân.

## Điều kiện kết thúc Giai đoạn 4 (nghiên cứu)

1. Các báo cáo Bước 5E, 5L, 5M nhất quán với nhau và không có dấu hiệu bypass Gate.
2. Ba câu LLM S01–S03 đều đã được người dùng xác minh nội dung trên tài liệu Atlas hư cấu (phiếu review đã điền đủ).
3. Những giới hạn (bản quyền, kiểm duyệt y khoa, chưa có RAG thật được duyệt, an toàn chống injection chưa đầy đủ) được lưu rõ trong final report.
4. Không mở lại tập Test NHANES, không train lại ML, không chỉnh ChromaDB/Neo4j.

Khi đạt 1–4, có thể **đóng Giai đoạn 4 ở mức prototype nghiên cứu** và bắt đầu **Giai đoạn 5 – Tích hợp Multi-Agent**, nhưng phải giữ khóa cho các chức năng tư vấn y khoa chưa được phê duyệt.

## Cần làm ở những giai đoạn sau

- Xác minh độc lập quyền tái sử dụng và bằng chứng y khoa của 7 nguồn.
- Khắc phục Citation OK chỉ 25/42 và Rights Evidence chỉ 13/42 ở Bước 4.
- Đánh giá Retrieval trên tập câu hỏi độc lập, cải thiện Q01 và Q05.
- Kiểm thử prompt injection từ *retrieved content*, overclaim, trích dẫn sai và kiểm thử lâm sàng trước khi cân nhắc triển khai công khai.

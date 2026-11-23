# Giai đoạn 4 — Bước 5G: Medical Concepts & Claim Mentions

**Trạng thái:** Chuẩn bị để người dùng tự thực hiện trên Neo4j Aura Console. **Chưa chạy Cypher trên database của người dùng.**

## 1. Kết quả Bước 5F đã xác nhận

Theo ảnh và dòng dữ liệu người dùng cung cấp:

| Kiểm tra | Thực tế |
|---|---:|
| `MedicalClaim` ứng viên | 1 |
| `HAS_EVIDENCE_CANDIDATE` | 1 |
| Claim đã duyệt | 0 |
| Claim không bị chặn trả lời | 0 |

- Claim: `RESEARCH-CLAIM-001`, `draft_unverified`
- Chunk: `NIDDK-T2D-004__v1__9de2376433__0004`
- Nguồn: `NIDDK-T2D-004`
- Không thể kết luận đã được chuyên gia y tế độc lập phê duyệt.

## 2. Mục tiêu bước 5G

Tạo **5 node khái niệm** (một Disease, hai RiskFactor, một Mechanism, một GeneticFactor) và 5 cạnh `MENTIONS_CONCEPT` từ claim có sẵn.

**Chú ý:** `MENTIONS_CONCEPT` chỉ nói rằng claim *đề cập* đến khái niệm. Không biểu thị rằng một yếu tố *gây ra* bệnh, không xác thực cơ chế bệnh và không phải phê duyệt lâm sàng.

| Concept ID | Nhãn node | Tên Việt |
|---|---|---|
| `disease:type_2_diabetes` | `MedicalConcept:Disease` | Bệnh tiểu đường type 2 |
| `risk_factor:overweight_obesity` | `MedicalConcept:RiskFactor` | Thừa cân hoặc béo phì |
| `risk_factor:physical_inactivity` | `MedicalConcept:RiskFactor` | Ít hoạt động thể chất |
| `mechanism:insulin_resistance` | `MedicalConcept:Mechanism` | Kháng insulin |
| `genetic_factor:genes` | `MedicalConcept:GeneticFactor` | Yếu tố di truyền |

**Vì sao phân loại như vậy?** Dù chunk của NIDDK liệt kê 4 yếu tố góp phần, kháng insulin mô tả một cơ chế và genes mô tả yếu tố di truyền; không nên gộp máy móc cả bốn thành `RiskFactor`.

## 3. Trình tự thực hiện

1. Đăng nhập **https://console.neo4j.io/**, chọn AuraDB Instance → Query.
2. Mở `05G-Neo4j-Medical-Concepts.cypher` trong VS Code. **Chạy từng khối**, không dán toàn bộ một lượt.
3. Chạy `[0]` và so sánh `m.statement` với mệnh đề bạn đã ghi vào CSV ở Bước 5F. Nếu thiếu/khác ý, chưa chạy các khối ghi.
4. Chạy `[1]`, `[2A]`, `[2B]` để tạo uniqueness constraint và 5 node khái niệm. Dùng `MERGE` để hạn chế trùng dữ liệu khi chạy lại.
5. Chạy `[3]` để tạo 5 cạnh `MENTIONS_CONCEPT`. Khối này chỉ thực thi khi claim ở `draft_unverified`, bị chặn trả lời, và liên kết được đến nguồn NIDDK đã chỉ định.
6. Chạy `[4]`, `[5]`, `[6]`, `[7]` để kiểm tra và xem graph.

## 4. Kết quả kỳ vọng (nếu database hiện chưa có MedicalConcept)

| Thống kê | Kỳ vọng |
|---|---:|
| `concepts` | 5 |
| `mention_links` | 5 |
| `approved_claims` | 0 |
| `claims_not_blocked` | 0 |

Các số này là **kỳ vọng**, không phải dữ liệu đã thực thi. Nếu đã có concept từ thí nghiệm khác, số `concepts` có thể lớn hơn 5; phải đọc danh sách concept thực tế.

## 5. Lưu ý an toàn

- Không đổi `review_status` từ `draft_unverified` sang `approved`.
- Không đổi `usage_status` từ `blocked_for_answering`.
- Không tạo cạnh `CAUSES`, `INCREASES_RISK` hay `TREATS` trước khi có quy trình kiểm định quan hệ, bằng chứng và điều kiện quyền sử dụng.
- `MedicalClaim`, `ChunkRef` và `SourceDocument` hiện chưa được xác minh độc lập để phục vụ RAG tư vấn.
- Không chạy LLM, không sửa ChromaDB, không huấn luyện lại mô hình ML trong bước này.

## 6. Bằng chứng cần gửi lại

Gửi bảng kết quả khối `[4]` và ảnh Graph khối `[6]`. Ghi thêm nếu Cypher báo lỗi hoặc `linked_concepts` khác 5. Sau khi có kết quả sẽ cập nhật nhật ký nghiên cứu và thiết kế giai đoạn tiếp theo.

## Tài liệu tham khảo kỹ thuật

- Neo4j Cypher `MERGE`: https://neo4j.com/docs/cypher-manual/current/clauses/merge/
- Neo4j uniqueness constraints: https://neo4j.com/docs/cypher-manual/current/schema/constraints/create-constraints/

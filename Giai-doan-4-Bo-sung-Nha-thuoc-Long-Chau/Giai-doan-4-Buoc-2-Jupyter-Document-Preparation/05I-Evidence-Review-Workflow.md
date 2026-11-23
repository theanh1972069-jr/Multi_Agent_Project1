# Giai đoạn 4 · Bước 5I — Evidence Review & Knowledge Validation

**Trạng thái:** Hướng dẫn thực hành, chưa chạy trên Neo4j Aura của người dùng.  
**Mục tiêu:** Kiểm toán 4 RelationCandidate, ghi nhận sự đầy đủ của liên kết kỹ thuật; tuyệt đối không tự phê duyệt y khoa hoặc quyền tái sử dụng.

## 1. Kết quả đầu vào đã được người dùng xác nhận

| Chỉ số | Kết quả |
|---|---:|
| `relation_candidates` | 4 |
| `subject_links` | 4 |
| `object_links` | 4 |
| `claim_links` | 4 |
| `approved_relations` | 0 |
| `not_blocked_relations` | 0 |

Bốn relation candidate (đều **chưa xác minh**):

1. `REL-CAND-001`: `risk_factor:overweight_obesity` — `RISK_FACTOR_FOR` → `disease:type_2_diabetes`.
2. `REL-CAND-002`: `risk_factor:physical_inactivity` — `RISK_FACTOR_FOR` → `disease:type_2_diabetes`.
3. `REL-CAND-003`: `mechanism:insulin_resistance` — `MECHANISM_ASSOCIATED_WITH` → `disease:type_2_diabetes`.
4. `REL-CAND-004`: `genetic_factor:genes` — `GENETIC_CONTRIBUTION_TO` → `disease:type_2_diabetes`.

Tất cả hiện dựa trên `RESEARCH-CLAIM-001`, liên kết tới chunk `NIDDK-T2D-004__v1__9de2376433__0004`. **Một chunk là điểm xuất phát để truy vết, chưa đủ để tuyên bố bốn quan hệ đều đã được đánh giá lâm sàng.**

## 2. Phân biệt ba loại kiểm tra

| Kiểm tra | Có thể hoàn thành trong bước này? | Ý nghĩa |
|---|---|---|
| Technical provenance | Có, thông qua Neo4j Query | `RelationCandidate → MedicalClaim → ChunkRef → SourceDocument` hoạt động và ID hợp lệ |
| Source rights | Chưa được tự tuyên bố đạt | Kiểm tra ai sở hữu nội dung, điều khoản tái sử dụng và bằng chứng giấy phép cho từng nguồn |
| Clinical/medical review | Chưa được tự tuyên bố đạt | Đánh giá mệnh đề có chính xác, không nói quá phạm vi, phù hợp hướng dẫn cập nhật; cần người có chuyên môn phù hợp |

Các trường `approved`, `verified`, `blocked_for_answering` **không được sửa chỉ vì QA kỹ thuật đạt**. Long Châu và WHO còn phải có kiểm tra quyền riêng trước khi bật cho hệ thống trả lời.

## 3. Thực hành bằng Neo4j Aura Console

1. Mở `05I-Neo4j-Evidence-Review.cypher` bằng VS Code.
2. Chạy riêng **[0]**. Kết quả mục tiêu: 4 candidates, 0 approved, 0 not-blocked, 0 approved claims.
3. Chạy **[1]** để đọc 4 dòng: `relation_id`, `proposed_relation`, hai khái niệm, `claim_id`, `chunk_id`, `source_id`, URL và trạng thái. Ghi lại nếu có trường rỗng/sai.
4. Chạy **[2]** để tìm mối nối thiếu. Kết quả mục tiêu: `missing_subject=0`, `missing_object=0`, `missing_claim=0`, `missing_provenance=0`.
5. Chạy **[3]** và đối chiếu với chunk gốc trên máy (trong ChromaDB) cùng URL NIDDK. Đây là kiểm tra nguồn gốc, không phải phê duyệt độc lập.
6. **Tùy chọn:** Nếu [0]–[3] đạt, chạy **[4]** (constraint) rồi **[5]** để tạo các `TechnicalReview` với `result='awaiting_independent_review'`. Hai khối này **ghi database** nhưng không sửa MedicalClaim/RelationCandidate.
7. Chạy **[6]** để bảo đảm vẫn có 0 approved và 0 not-blocked, rồi xem graph bằng **[7]**.

> Mọi truy vấn có khả năng ghi đều được đánh dấu **WRITE**. Bạn trực tiếp quyết định khi nào chạy trên Aura. Không cần Jupyter.

## 4. Phiếu kiểm tra cho từng relation (ghi vào báo cáo, không đưa vào graph đã phê duyệt)

| Relation ID | Có concept đúng? | Có claim/chunk/source? | Nguồn quyền sử dụng đã kiểm tra độc lập? | Nội dung y khoa đã thẩm định độc lập? | Hành động |
|---|---|---|---|---|---|
| REL-CAND-001 | cần kiểm tra | cần kiểm tra | chưa | chưa | Giữ blocked |
| REL-CAND-002 | cần kiểm tra | cần kiểm tra | chưa | chưa | Giữ blocked |
| REL-CAND-003 | cần kiểm tra | cần kiểm tra | chưa | chưa | Giữ blocked |
| REL-CAND-004 | cần kiểm tra | cần kiểm tra | chưa | chưa | Giữ blocked |

**Chú ý về diễn giải:** kháng insulin là cơ chế sinh bệnh, không nên mặc định mô tả như yếu tố hành vi; di truyền là yếu tố góp phần, không có nghĩa nguyên nhân duy nhất. Các nhãn quan hệ chỉ là loại mô tả *ứng viên*.

## 5. Kết quả cần gửi

- Kết quả [0], [2], [6]; nếu chạy [5], số `technical_reviews_created_or_found`.
- Ảnh hoặc bảng kết quả [1] (có thể lược bỏ câu claim dài).
- Không gửi mật khẩu Neo4j, URI có thông tin bí mật hay văn bản nguồn chưa được phép chia sẻ.

## 6. Điều kiện chuyển bước

**Hoàn thành bước 5I kỹ thuật:** 4 relation có đủ đường truy vết; 0 đường mất; claim và relation vẫn blocked; audit rõ ràng.

**Chưa đủ điều kiện bật LLM:** quyền sử dụng chưa được xác minh độc lập; chưa có thẩm định y khoa; đánh giá Retrieval trước đó có citation OK 25/42 và Rights Evidence Yes 13/42; chưa có kiểm thử abstention/prompt injection đầy đủ.

Sau bước này sẽ thiết kế **5J — Review Queue & Safe Graph Retrieval**, trong đó chỉ các nguồn và claim đủ tiêu chí mới được xét dùng làm bằng chứng. Không tự giả định các tiêu chí đó đã đạt.

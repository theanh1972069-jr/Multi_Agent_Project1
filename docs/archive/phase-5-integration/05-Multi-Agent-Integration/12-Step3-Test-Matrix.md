# Giai đoạn 5 – Ma trận kiểm thử Bước 3

| Nhóm | ID | Kiểm tra | Kỳ vọng |
|---|---|---|---|
| Unit offline | T01–T03 | Audit, 3 câu mock, chặn ID tùy ý | Pass |
| Unit offline | T04–T07 | URI TLS, URI có thông tin đăng nhập, database name | Pass |
| Unit offline | T08–T11 | approved thay đổi, provenance sai, thiếu / trùng hit | Fail closed |
| Unit offline | T12–T15 | khóa allowed_to_answer, không rò text, sai rank / URL | Fail closed |
| Graph mock trên máy người dùng | G01 | Ba câu thử Q01–Q03 | 9/9 mock, gate blocked |
| Live ChromaDB + Neo4j | L01 | Snapshot, collection count | 66, đúng snapshot/model ID |
| Live ChromaDB + Neo4j | L02 | Node/relationship counts | 7 SourceDocument, 66 ChunkRef, 66 PART_OF, 0 orphan |
| Live ChromaDB + Neo4j | L03 | Candidate/Review/Approved | 4/4/0 claims/0 relations approved |
| Live ChromaDB + Neo4j | L04 | 3 queries × top 3 provenance | 9/9 khớp |
| Safety | S01 | Không trả về văn bản chunk | Không vào LangGraph/report |
| Safety | S02 | Không gọi LLM/không tạo câu trả lời | 0 |
| Safety | S03 | Không lệnh ghi dữ liệu / không huấn luyện | 0 |
| Safety | S04 | Mọi evidence metadata | `allowed_to_answer=false` |

Các trường LIVE **phải do người dùng chạy**, không suy từ unit/mock. Các unit và Graph mock không xác nhận quyền sử dụng nội dung hoặc độ tin cậy lâm sàng.

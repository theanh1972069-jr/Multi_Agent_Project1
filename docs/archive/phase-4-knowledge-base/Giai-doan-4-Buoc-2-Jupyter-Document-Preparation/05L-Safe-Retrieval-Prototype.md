# Giai đoạn 4 — Bước 5L: Safe Retrieval Prototype (ChromaDB + Neo4j Aura)

**Trạng thái:** đã chuẩn bị hướng dẫn và mã nghiên cứu; **người dùng chưa chạy Bước 5L**.  
**Điểm xuất phát:** người thực hành xác nhận các truy vấn Bước 5K đều đúng kỳ vọng; 4 RelationCandidate + 4 TechnicalReview; 0 approved/unblocked; 7 nguồn và 66 chunks.

## 1. Mục tiêu

- Dùng **VS Code + PowerShell** thực hiện truy xuất bằng ChromaDB và đối chiếu trạng thái các claim/quan hệ trong Neo4j Aura.
- Hai kiểu đầu ra: metadata phục vụ người rà soát; và quyết định chặn trả lời. **Không xuất nội dung tư vấn, không dùng LLM.**
- Giữ nguyên snapshot ChromaDB và graph. Không thay đổi ngưỡng hay mô hình NHANES, không mở lại Test.
- **Fail closed:** không có bằng chứng độc lập và trạng thái đã duyệt => chưa cho phép dùng để trả lời.

## 2. Đầu vào kỹ thuật và đầu ra

| Hạng mục | Giá trị |
|---|---|
| Chroma collection | `diabetes_kb_step3_e5small_v1` |
| Document snapshot SHA256 | `cc064ec7187192c9994180510412843f8d0908e3d6842e4a71c7cd` |
| Embedding model | `intfloat/multilingual-e5-small`, 384 chiều |
| Neo4j | Aura, kết nối `neo4j+s://...` với Python Driver |
| Graph preflight | 7 SourceDocument, 66 ChunkRef, 66 PART_OF, 4 RelationCandidate, 4 TechnicalReview, 0 approved claims/relations |
| Output | `data/outputs/safe_retrieval_step5l/step5l_safe_retrieval_report.json` |

> Để tránh lộ nội dung chưa xác minh quyền sử dụng, báo cáo chỉ xuất URL và metadata, **không lưu/hiển thị toàn văn chunks**.

## 3. Hướng dẫn chạy

1. Giữ thư mục dự án chứa `data/vector_store/chroma_step3`, `registry`, `tools` như Bước 5E. Giải nén bộ thực hành 5L vào cùng thư mục, không ghi đè dữ liệu cũ.
2. Mở `05L-Neo4j-ReadOnly-Gate.cypher` trong VS Code và chạy lần lượt ba khối ở Aura. Khối `[2]` dự kiến **0 dòng**.
3. Trong PowerShell ở project root, chọn đúng môi trường Python có ChromaDB đã cài:

```powershell
python -m pip install chromadb neo4j sentence-transformers
python .\tools\05L_safe_knowledge_retrieval.py --self-test
```

4. Cấu hình Aura trong terminal (không chia sẻ credential, không đưa vào Git):

```powershell
$env:NEO4J_URI = "neo4j+s://YOUR-INSTANCE.databases.neo4j.io"
$env:NEO4J_USERNAME = "neo4j"
$env:NEO4J_DATABASE = "neo4j"
```

5. Chạy (mật khẩu được nhập ẩn khi được hỏi):

```powershell
python .\tools\05L_safe_knowledge_retrieval.py --project-root .
```

Nếu project root hiện tại khác, truyền `--project-root "C:\\path\\to\\your\\project"` hoặc `--chroma-dir` theo README của Bước 5E. **Không dùng URL `console.neo4j.io` làm `NEO4J_URI`.**

6. Gửi lại stdout của chương trình và `step5l_safe_retrieval_report.json`. Không gửi mật khẩu, `.env` hoặc file chứa thông tin đăng nhập.

## 4. Mục tiêu kiểm thử

| Kiểm tra | Kỳ vọng |
|---|---|
| Offline policy self-test | `PASS` |
| Metadata Preflight | 7 nguồn, 66 chunks và link, 4 relation, 4 TechnicalReview |
| Chroma → Neo4j | Top 3 × 3 câu = 9 kết quả, kỳ vọng 9/9 provenance khớp |
| `approved_relations`, `approved_claims` | 0, 0 |
| `answer_gate` | `BLOCKED_RESEARCH_ONLY` trên mọi câu hỏi |
| LLM / DB writes / ML training | Không / Không / Không |

Một truy vấn có cosine distance thấp **không tự động** được đưa vào câu trả lời. Phải phân biệt metadata liên kết kỹ thuật, độ liên quan, giấy phép, đánh giá y khoa và bảo vệ an toàn.

## 5. Giới hạn và kế hoạch sau 5L

- Trạng thái review vẫn do nguồn thông tin nội bộ cung cấp; bản demo **không thay thế quy trình cấp quyền hay xác thực chuyên môn**.
- Mã 5L luôn đặt `allowed_to_answer=false` kể cả trong kịch bản phê duyệt giả định. Không có endpoint hoặc LLM để sinh câu trả lời.
- Sau Bước 5L: kiểm thử một RAG **môi trường sandbox với tri thức giả lập được phép sử dụng** để học cấu trúc prompt và citation, còn tri thức y khoa thực tế vẫn chặn cho đến khi có kiểm duyệt phù hợp.

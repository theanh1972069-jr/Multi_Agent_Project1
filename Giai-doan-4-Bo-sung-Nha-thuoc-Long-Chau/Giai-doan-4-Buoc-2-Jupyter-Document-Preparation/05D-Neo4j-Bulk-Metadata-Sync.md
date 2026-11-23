# Giai đoạn 4 – Bước 5D: Đồng bộ 66 ChunkRef từ ChromaDB sang Neo4j Aura

**Trạng thái:** Đã chuẩn bị mã và hướng dẫn; **người dùng chưa chạy**. Không được ghi “hoàn tất” trước khi nhận kết quả Aura Query.

## Kết quả thực tế trước bước 5D

Theo ảnh Neo4j do người dùng cung cấp: `SourceDocument = 7`, `Topic = 6`, `COVERS_TOPIC = 7`, `ChunkRef = 3`, `PART_OF = 3`, `MedicalClaim = 0`. Bước 3 ChromaDB có 66 vector trong collection `diabetes_kb_step3_e5small_v1`, snapshot SHA256 `cc064ec7187192c999418051cb2125a0510412843f8d0908e3d6842e4a71c7cd`.

## Ranh giới kỹ thuật và kiểm duyệt

- **ChromaDB** giữ nội dung và embeddings; **Neo4j** giữ `ChunkRef` và quan hệ nguồn `PART_OF`.
- Không gửi mật khẩu, API token, toàn văn tài liệu hoặc vector lên Neo4j ở bước này.
- Metadata các nguồn WHO/Long Châu vẫn cần xác minh quyền sử dụng độc lập; không tự đổi trạng thái thành verified.
- Chưa tạo hoặc phê duyệt `MedicalClaim`, chưa gọi LLM, chưa tái huấn luyện ML.
- Bộ kiểm thử mong đợi **66/66** ChunkRef; nếu không khớp, dừng và kiểm tra, không tự xóa node.

## A. Xuất file Cypher ngay trên máy bạn (VS Code Terminal/PowerShell)

Chạy tại **thư mục gốc Giai đoạn 4 có `data/` và `registry/`**. Bạn cần dùng đúng folder chứa ChromaDB hiện tại; có thể lồng trong `Giai-doan-4-Buoc-2-Jupyter-Document-Preparation` như báo cáo Bước 3 đã ghi.

1. Sao chép `tools/05D_export_chroma_metadata.py` vào thư mục `tools/` bên trong gốc dự án Giai đoạn 4.
2. Dùng Python của môi trường đã cài ChromaDB. Ví dụ từ PowerShell, tại project root:

```powershell
python .\tools\05D_export_chroma_metadata.py --project-root .
```

Nếu không tìm được ChromaDB, chỉ rõ đường dẫn trong báo cáo Bước 3 (không nhập mật khẩu):

```powershell
python .\tools\05D_export_chroma_metadata.py --project-root . --chroma-dir ".\data\vector_store\chroma_step3"
```

Script thực hiện **đọc-only** trên ChromaDB và đối chiếu `source_snapshot`, model embedding, số lượng 66, 7 source IDs và URL với `source_registry.csv`. Nếu sai thì dừng. Script **không** kết nối Neo4j hay tải nội dung tài liệu.

Kết quả tạo ra:

- `data/outputs/neo4j_sync_step5d/05D_import_66_chunks.cypher`
- `data/outputs/neo4j_sync_step5d/05D_export_manifest.json`

## B. Dán và chạy trên Neo4j Aura Console

1. Đăng nhập `https://console.neo4j.io/` → mở instance hiện tại → Query.
2. Chạy trước ô `5D-01` trong file `05D-Aura-Verification.cypher` để xem đủ 7 `SourceDocument`.
3. Mở `05D_import_66_chunks.cypher` trong VS Code; đọc qua, kiểm tra file **chỉ chứa metadata**.
4. Sao chép **toàn bộ một câu truy vấn UNWIND** vào một ô Neo4j Query; thực thi một lần.
5. Kết quả của lệnh import phải hiển thị: `processed_chunks=66`, `linked_sources=7`. Đây là số dòng được xử lý chứ chưa phải xác nhận cuối cùng.
6. Chạy riêng từng truy vấn `5D-02` → `5D-06` trong `05D-Aura-Verification.cypher`.

Script dùng `UNWIND` + `MATCH` + `MERGE`: 3 `ChunkRef` đã có được tái sử dụng, 63 node còn thiếu được thêm vào. Chạy lại cùng lệnh với cùng `chunk_id` không cố ý nhân bản node hoặc quan hệ.

## C. Kết quả kỳ vọng (database mới chỉ có dữ liệu các bước 5B–5C)

| Metric | Kỳ vọng |
|---|---:|
| `sources` | 7 |
| `topics` | 6 |
| `topic_links` | 7 |
| `chunk_refs` | 66 |
| `chunk_links` | 66 |
| `medical_claims` | 0 |
| `orphan_chunk_refs` | 0 |

Số chunks theo nguồn phải là CDC-T2D-001=4, CDC-RISK-002=3, NIDDK-DIAG-003=19, NIDDK-T2D-004=11, WHO-DIAB-005=5, LC-HBA1C-006=11, LC-STAGES-007=13.

Nếu `processed_chunks < 66`, có thể `SourceDocument` thiếu hoặc `source_id` không khớp; **không xóa database để chạy lại**. Hãy gửi ảnh và kết quả truy vấn, chúng ta sẽ chẩn đoán.

## D. Sản phẩm bàn giao và mốc chuyển bước

Người dùng gửi output export script, `05D_export_manifest.json` và ảnh kết quả Aura Query của `5D-02`, `5D-03`, `5D-04`. Không gửi credentials, document text hoặc vector.

Sau khi xác nhận 66 node và 66 liên kết, ta sẽ chuẩn bị **bước 5E – Graph Retrieval & kết hợp ChromaDB–Neo4j**. Đây vẫn là nguyên mẫu kỹ thuật. Evidence Gate của 7 nguồn vẫn chưa đạt; không cho LLM sử dụng graph làm bằng chứng y khoa chưa kiểm chứng.

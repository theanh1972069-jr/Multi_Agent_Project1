// GIAI ĐOẠN 4 – BƯỚC 5C
// Neo4j Aura / Cypher Query. Chạy từng khối độc lập; không chọn chạy cả file một lần.
// Chưa có quan hệ y khoa nào được phê duyệt. Không gọi LLM, không thay đổi ChromaDB.

// [0] PRE-FLIGHT: Bước 5B phải tạo 7 SourceDocument, 6 Topic, 7 COVERS_TOPIC.
MATCH (s:SourceDocument)
WITH count(s) AS source_count
MATCH (t:Topic)
WITH source_count, count(t) AS topic_count
MATCH ()-[r:COVERS_TOPIC]->()
RETURN source_count, topic_count, count(r) AS topic_link_count;

// [1A] Constraint unique cho chunk_id, chạy một mình.
CREATE CONSTRAINT chunkref_chunk_id IF NOT EXISTS
FOR (c:ChunkRef) REQUIRE c.chunk_id IS UNIQUE;

// [1B] Constraint unique cho claim_id, chạy một mình.
CREATE CONSTRAINT medical_claim_claim_id IF NOT EXISTS
FOR (m:MedicalClaim) REQUIRE m.claim_id IS UNIQUE;

// [2] Chỉ nhập metadata của 3 chunk đã xuất hiện trong REPORT BƯỚC 3.
// Không có văn bản claim, không coi các chunk này đã qua kiểm duyệt y khoa/bản quyền.
// Nếu SourceDocument Bước 5B chưa có, MATCH không tìm thấy và sẽ không tạo chunk.
UNWIND [
  {chunk_id:'NIDDK-T2D-004__v1__9de2376433__0004', source_id:'NIDDK-T2D-004', section:'What causes type 2 diabetes?'},
  {chunk_id:'NIDDK-DIAG-003__v1__f6849feb36__0004', source_id:'NIDDK-DIAG-003', section:'Type 2 diabetes testing'},
  {chunk_id:'LC-HBA1C-006__v1__a2458c0a11__0002', source_id:'LC-HBA1C-006', section:'HbA1c bao nhiêu là tiền tiểu đường?'}
] AS row
MATCH (s:SourceDocument {source_id:row.source_id})
MERGE (c:ChunkRef {chunk_id:row.chunk_id})
ON CREATE SET c.created_at = datetime(),
              c.rights_review_status = 'pending_independent_check',
              c.medical_review_status = 'pending',
              c.research_only = true
SET c.source_id = row.source_id,
    c.section = row.section,
    c.collection = 'diabetes_kb_step3_e5small_v1',
    c.source_snapshot_sha256 = 'cc064ec7187192c999418051cb2125a0510412843f8d0908e3d6842e4a71c7cd'
MERGE (c)-[:PART_OF]->(s)
RETURN count(c) AS linked_chunk_refs;

// [3] Kiểm tra metadata đối chiếu SourceDocument.
MATCH (c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
RETURN c.chunk_id AS chunk_id,
       c.section AS section,
       s.source_id AS source_id,
       s.provider AS provider,
       s.url AS url,
       c.medical_review_status AS medical_status,
       c.rights_review_status AS rights_status
ORDER BY source_id, chunk_id;

// [4] MẪU THỰC HÀNH MedicalClaim - KHÔNG CHẠY nguyên trạng.
// Bắt buộc mở tệp chunk có cùng chunk_id để đối chiếu.
// Thay DANG_CHO_BAN_DOI_CHIEU_NOI_DUNG bằng mệnh đề do chính bạn diễn đạt
// dựa trên nội dung chunk thật, kèm hồ sơ nguồn. Nếu chưa thay, câu lệnh KHÔNG tạo claim.
WITH 'RESEARCH-CLAIM-001' AS claim_id,
     'DANG_CHO_BAN_DOI_CHIEU_NOI_DUNG' AS statement,
     'NIDDK-T2D-004__v1__9de2376433__0004' AS chunk_id
WHERE statement <> 'DANG_CHO_BAN_DOI_CHIEU_NOI_DUNG'
  AND size(trim(statement)) >= 20
MATCH (c:ChunkRef {chunk_id:chunk_id})
MERGE (m:MedicalClaim {claim_id:claim_id})
ON CREATE SET m.created_at = datetime(),
              m.review_status = 'draft_unverified',
              m.usage_status = 'blocked_for_answering',
              m.reviewer = 'pending',
              m.rights_review_status = 'pending_independent_check'
SET m.statement = statement,
    m.origin = 'human_paraphrase_from_reviewed_chunk',
    m.review_status = 'draft_unverified',
    m.usage_status = 'blocked_for_answering'
MERGE (m)-[e:HAS_EVIDENCE_CANDIDATE]->(c)
ON CREATE SET e.created_at = datetime(),
              e.review_status = 'pending'
RETURN m.claim_id AS claim_id, m.review_status AS claim_status,
       c.chunk_id AS evidence_candidate;

// [5] Chỉ xem claims đang chờ kiểm duyệt; chưa kích hoạt phục vụ người dùng.
OPTIONAL MATCH (m:MedicalClaim)
OPTIONAL MATCH (m)-[:HAS_EVIDENCE_CANDIDATE]->(c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
RETURN m.claim_id AS claim_id, m.statement AS statement,
       m.review_status AS review_status, m.usage_status AS usage_status,
       c.chunk_id AS chunk_id, s.source_id AS source_id
ORDER BY claim_id;

// [6] Read-only graph visualization, chỉ gồm provenance.
MATCH p=(m:MedicalClaim)-[:HAS_EVIDENCE_CANDIDATE]->(:ChunkRef)-[:PART_OF]->(:SourceDocument)
RETURN p LIMIT 20;

// [7] Điều kiện an toàn: KHÔNG có MedicalClaim phê duyệt.
OPTIONAL MATCH (m:MedicalClaim {review_status:'approved'})
RETURN count(m) AS approved_claims;

// Khi mở rộng 66 chunk: chỉ xuất metadata từ tập chunk_id thực tế của bạn,
// kiểm tra trùng source_id và provenance, import có kiểm soát. Không giả định 66 đã import.

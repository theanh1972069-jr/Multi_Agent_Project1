// GIAI ĐOẠN 4 – BƯỚC 5F: MEDICAL CLAIM CANDIDATES
// Dùng trong Neo4j Aura > Query; chạy TỪNG KHỐI độc lập.
// Không tạo approved claims, không sửa ChromaDB, không khẳng định y khoa tự động.

// [0] PRE-FLIGHT READ-ONLY
CALL { MATCH (s:SourceDocument) RETURN count(s) AS sources }
CALL { MATCH (c:ChunkRef) RETURN count(c) AS chunks }
CALL { MATCH (:ChunkRef)-[r:PART_OF]->(:SourceDocument) RETURN count(r) AS chunk_links }
CALL { MATCH (c:ChunkRef) WHERE NOT (c)-[:PART_OF]->(:SourceDocument) RETURN count(c) AS orphans }
RETURN sources, chunks, chunk_links, orphans;

// [1] CONSTRAINT, chạy riêng; không ảnh hưởng claims đã có
CREATE CONSTRAINT medical_claim_claim_id IF NOT EXISTS
FOR (m:MedicalClaim) REQUIRE m.claim_id IS UNIQUE;

// [2] CHECK CHUNK / SOURCE: xác minh chunk_id thật trước khi điền claim
MATCH (c:ChunkRef {chunk_id:'NIDDK-T2D-004__v1__9de2376433__0004'})-[:PART_OF]->(s:SourceDocument)
RETURN c.chunk_id AS chunk_id, c.section AS section,
       s.source_id AS source_id, s.title AS source_title,
       s.url AS source_url, c.source_snapshot_sha256 AS snapshot,
       c.metadata_sync_status AS sync_status;

// [3] CREATE ONLY A USER-REVIEWED, UNVERIFIED CANDIDATE
// Thay statement bằng lời diễn đạt của bạn SAU KHI đọc và đối chiếu chunk THẬT.
// Nếu giữ nguyên DANG_CHO_BAN_DOI_CHIEU_NOI_DUNG, KHÔNG có node mới.
WITH 'RESEARCH-CLAIM-001' AS claim_id,
     'DANG_CHO_BAN_DOI_CHIEU_NOI_DUNG' AS statement,
     'NIDDK-T2D-004__v1__9de2376433__0004' AS chunk_id
WHERE statement <> 'DANG_CHO_BAN_DOI_CHIEU_NOI_DUNG'
  AND size(trim(statement)) >= 25
MATCH (c:ChunkRef {chunk_id: chunk_id})-[:PART_OF]->(s:SourceDocument)
MERGE (m:MedicalClaim {claim_id: claim_id})
ON CREATE SET m.statement = statement,
              m.created_at = datetime(),
              m.review_status = 'draft_unverified',
              m.usage_status = 'blocked_for_answering',
              m.rights_review_status = 'pending_independent_check',
              m.medical_review_status = 'pending',
              m.research_only = true,
              m.source_snapshot_sha256 = c.source_snapshot_sha256
MERGE (m)-[r:HAS_EVIDENCE_CANDIDATE]->(c)
ON CREATE SET r.created_at = datetime(), r.review_status = 'pending'
RETURN m.claim_id AS claim_id, m.review_status AS claim_status,
       c.chunk_id AS evidence_candidate, s.source_id AS source_id;

// [4] VERIFY CANDIDATE LINKS (read-only)
MATCH (m:MedicalClaim)-[r:HAS_EVIDENCE_CANDIDATE]->(c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
RETURN m.claim_id AS claim_id, m.review_status AS review_status,
       m.usage_status AS usage_status, r.review_status AS evidence_review,
       c.chunk_id AS chunk_id, s.source_id AS source_id
ORDER BY claim_id;

// [5] VISUALIZE PROVENANCE ONLY (read-only)
MATCH p=(m:MedicalClaim)-[:HAS_EVIDENCE_CANDIDATE]->(c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
RETURN p LIMIT 20;

// [6] SAFETY AUDIT (read-only)
CALL { MATCH (m:MedicalClaim) RETURN count(m) AS claim_candidates }
CALL { MATCH ()-[r:HAS_EVIDENCE_CANDIDATE]->() RETURN count(r) AS evidence_candidate_links }
CALL { MATCH (m:MedicalClaim {review_status:'approved'}) RETURN count(m) AS approved_claims }
CALL { MATCH (m:MedicalClaim) WHERE m.usage_status <> 'blocked_for_answering' OR m.usage_status IS NULL RETURN count(m) AS not_blocked_claims }
RETURN claim_candidates, evidence_candidate_links, approved_claims, not_blocked_claims;

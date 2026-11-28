// GIAI DOAN 4 - BUOC 5I: TECHNICAL EVIDENCE REVIEW - NEO4J AURA
// Chay tung khoi rieng, theo thu tu; cac khoi [0]-[3],[6]-[7] READ-ONLY.
// Chi [4] tao constraint va [5] ghi nhat ky QA KY THUAT.
// TUYET DOI KHONG cap nhat review_status='approved' hay usage_status.
// Khong xac minh thay chuyen gia y khoa / chu so huu ban quyen.

// [0] PRE-FLIGHT: kiem tra 4 ung vien va bat bien an toan (READ ONLY)
CALL { MATCH (r:RelationCandidate) RETURN count(r) AS relation_candidates }
CALL { MATCH (r:RelationCandidate) WHERE r.review_status='approved' RETURN count(r) AS approved_relations }
CALL { MATCH (r:RelationCandidate) WHERE r.usage_status IS NULL OR r.usage_status <> 'blocked_for_answering' RETURN count(r) AS not_blocked_relations }
CALL { MATCH (m:MedicalClaim) WHERE m.review_status='approved' RETURN count(m) AS approved_claims }
RETURN relation_candidates, approved_relations, not_blocked_relations, approved_claims;

// [1] REVIEW QUEUE: doc du 4 triples + evidence + trang thai (READ ONLY)
MATCH (r:RelationCandidate)-[:SUBJECT_CONCEPT]->(subject:MedicalConcept)
MATCH (r)-[:OBJECT_CONCEPT]->(object:MedicalConcept)
MATCH (r)-[:SUPPORTED_BY_CLAIM]->(claim:MedicalClaim)
OPTIONAL MATCH (claim)-[:HAS_EVIDENCE_CANDIDATE]->(chunk:ChunkRef)-[:PART_OF]->(source:SourceDocument)
RETURN r.relation_id AS relation_id,
       r.relation_type AS proposed_relation,
       subject.concept_id AS subject_id,
       object.concept_id AS object_id,
       claim.claim_id AS claim_id,
       claim.statement AS claim_statement,
       chunk.chunk_id AS chunk_id,
       source.source_id AS source_id,
       source.url AS source_url,
       r.review_status AS relation_review,
       r.usage_status AS relation_usage,
       claim.review_status AS claim_review,
       claim.usage_status AS claim_usage,
       claim.rights_review_status AS rights_status,
       claim.medical_review_status AS medical_status
ORDER BY relation_id;

// [2] KIEM TRA THIEU CANH / TRUY VET (READ ONLY)
CALL {
  MATCH (r:RelationCandidate)
  WHERE NOT EXISTS { MATCH (r)-[:SUBJECT_CONCEPT]->(:MedicalConcept) }
  RETURN count(r) AS missing_subject
}
CALL {
  MATCH (r:RelationCandidate)
  WHERE NOT EXISTS { MATCH (r)-[:OBJECT_CONCEPT]->(:MedicalConcept) }
  RETURN count(r) AS missing_object
}
CALL {
  MATCH (r:RelationCandidate)
  WHERE NOT EXISTS { MATCH (r)-[:SUPPORTED_BY_CLAIM]->(:MedicalClaim) }
  RETURN count(r) AS missing_claim
}
CALL {
  MATCH (r:RelationCandidate)
  WHERE NOT EXISTS {
    MATCH (r)-[:SUPPORTED_BY_CLAIM]->(:MedicalClaim)-[:HAS_EVIDENCE_CANDIDATE]->(:ChunkRef)-[:PART_OF]->(:SourceDocument)
  }
  RETURN count(r) AS missing_provenance
}
RETURN missing_subject, missing_object, missing_claim, missing_provenance;

// [3] KIEM TRA CLAIM VA NGUON GOC; chi la trace, KHONG chung nhan y khoa (READ ONLY)
MATCH (m:MedicalClaim {claim_id:'RESEARCH-CLAIM-001'})-[:HAS_EVIDENCE_CANDIDATE]->(c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
RETURN m.claim_id AS claim_id, m.statement AS claim_statement,
       c.chunk_id AS chunk_id, c.section AS section,
       s.source_id AS source_id, s.url AS source_url,
       m.review_status AS claim_review,
       m.rights_review_status AS rights_status,
       m.medical_review_status AS medical_status,
       m.usage_status AS usage_status;

// [4] OPTIONAL - tao unique constraint cho bien ban QA ky thuat (WRITE SCHEMA)
CREATE CONSTRAINT technical_review_id_unique IF NOT EXISTS
FOR (t:TechnicalReview) REQUIRE t.review_id IS UNIQUE;

// [5] OPTIONAL - LUu 4 bien ban QA KY THUAT (WRITE); KHONG PHE DUYET Y KHOA
// CHI CHAY NEU [0]-[3] dat: 4 candidates, tat ca blocked, 0 missing.
MATCH (r:RelationCandidate)-[:SUBJECT_CONCEPT]->(:MedicalConcept)
MATCH (r)-[:OBJECT_CONCEPT]->(:MedicalConcept)
MATCH (r)-[:SUPPORTED_BY_CLAIM]->(m:MedicalClaim)-[:HAS_EVIDENCE_CANDIDATE]->(c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
WHERE r.review_status='draft_unverified'
  AND r.usage_status='blocked_for_answering'
  AND m.review_status='draft_unverified'
  AND m.usage_status='blocked_for_answering'
WITH DISTINCT r, c, s
MERGE (t:TechnicalReview {review_id:'TECH-REVIEW-'+r.relation_id})
ON CREATE SET t.scope='graph_provenance_only',
              t.result='awaiting_independent_review',
              t.medical_verified=false,
              t.rights_verified=false,
              t.research_only=true,
              t.source_id=s.source_id,
              t.chunk_id=c.chunk_id,
              t.created_at=datetime()
MERGE (r)-[:HAS_TECHNICAL_REVIEW]->(t)
RETURN count(DISTINCT t) AS technical_reviews_created_or_found,
       count(DISTINCT r) AS reviewed_candidates;

// [6] SAFETY AUDIT SAU KHI GHI; KHONG CO BAT KY CLAIM/RELATION NAO DUOC PHE DUYET (READ ONLY)
CALL { MATCH (r:RelationCandidate) RETURN count(r) AS candidates }
CALL { MATCH (t:TechnicalReview) RETURN count(t) AS technical_reviews }
CALL { MATCH (:RelationCandidate)-[x:HAS_TECHNICAL_REVIEW]->(:TechnicalReview) RETURN count(x) AS review_links }
CALL { MATCH (r:RelationCandidate {review_status:'approved'}) RETURN count(r) AS approved_relations }
CALL { MATCH (r:RelationCandidate) WHERE r.usage_status IS NULL OR r.usage_status <> 'blocked_for_answering' RETURN count(r) AS not_blocked_relations }
CALL { MATCH (m:MedicalClaim {review_status:'approved'}) RETURN count(m) AS approved_claims }
RETURN candidates, technical_reviews, review_links, approved_relations, not_blocked_relations, approved_claims;

// [7] HIEN THI GRAPH VI DU: RelationCandidate + TechnicalReview (READ ONLY)
MATCH p=(r:RelationCandidate)-[:HAS_TECHNICAL_REVIEW]->(t:TechnicalReview)
RETURN p LIMIT 10;

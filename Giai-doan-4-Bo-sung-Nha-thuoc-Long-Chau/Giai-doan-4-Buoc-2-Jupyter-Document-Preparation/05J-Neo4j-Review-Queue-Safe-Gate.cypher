// GIAI DOAN 4 - BUOC 5J - READ ONLY REVIEW QUEUE & SAFE GRAPH GATE
// Neo4j Aura Query: CHAY TUNG KHOI doc lap; TAT CA DEU READ-ONLY.
// Khong sua MedicalClaim, RelationCandidate, TechnicalReview hay ChromaDB.
// Nguon va claim CHUA duoc review doc lap; khong dung cho RAG/LLM y khoa.

// [0] PRE-FLIGHT: so dem ky thuat da duoc nguoi dung bao cao
CALL { MATCH (r:RelationCandidate) RETURN count(r) AS relation_candidates }
CALL { MATCH (t:TechnicalReview) RETURN count(t) AS technical_reviews }
CALL { MATCH (:RelationCandidate)-[e:HAS_TECHNICAL_REVIEW]->(:TechnicalReview) RETURN count(e) AS review_links }
CALL { MATCH (m:MedicalClaim) WHERE m.review_status = 'approved' RETURN count(m) AS approved_claims }
CALL { MATCH (r:RelationCandidate) WHERE r.review_status = 'approved' RETURN count(r) AS approved_relations }
CALL { MATCH (r:RelationCandidate) WHERE r.usage_status IS NULL OR r.usage_status <> 'blocked_for_answering' RETURN count(r) AS not_blocked_relations }
RETURN relation_candidates, technical_reviews, review_links, approved_claims, approved_relations, not_blocked_relations;

// [1] REVIEW QUEUE: 4 dong, moi relation -> claim -> chunk -> source -> technical review
MATCH (r:RelationCandidate)-[:SUBJECT_CONCEPT]->(subject:MedicalConcept)
MATCH (r)-[:OBJECT_CONCEPT]->(object:MedicalConcept)
MATCH (r)-[:SUPPORTED_BY_CLAIM]->(m:MedicalClaim)
MATCH (m)-[:HAS_EVIDENCE_CANDIDATE]->(c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
MATCH (r)-[:HAS_TECHNICAL_REVIEW]->(t:TechnicalReview)
RETURN r.relation_id AS relation_id,
       r.relation_type AS proposed_relation,
       subject.concept_id AS subject_id,
       object.concept_id AS object_id,
       m.claim_id AS claim_id,
       c.chunk_id AS chunk_id,
       s.source_id AS source_id,
       s.url AS source_url,
       r.review_status AS relation_review_status,
       r.usage_status AS relation_usage,
       m.review_status AS claim_review_status,
       m.usage_status AS claim_usage,
       t.review_id AS technical_review_id,
       t.result AS technical_review_result,
       t.medical_verified AS medical_verified,
       t.rights_verified AS rights_verified
ORDER BY relation_id;

// [2] DATA INTEGRITY: mong doi 0 trong moi cot
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
CALL {
  MATCH (r:RelationCandidate)
  WHERE NOT EXISTS { MATCH (r)-[:HAS_TECHNICAL_REVIEW]->(:TechnicalReview) }
  RETURN count(r) AS missing_technical_review
}
RETURN missing_subject, missing_object, missing_claim, missing_provenance, missing_technical_review;

// [3] SAFE-GATE DEMO: KHONG cho phep technical review thay the medical/rights review.
// IndependentMedicalReview va IndependentRightsReview la labels DU KIEN CHO TUONG LAI,
// hien chua co Node nao duoc phê duyet; ket qua du kien = 0.
// KHONG dung query nay lam policy gate production neu chua thiet ke IAM va approval workflow.
MATCH (r:RelationCandidate)-[:SUPPORTED_BY_CLAIM]->(m:MedicalClaim)
MATCH (m)-[:HAS_EVIDENCE_CANDIDATE]->(c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
WHERE r.review_status = 'approved'
  AND r.usage_status = 'allowed_for_answering'
  AND m.review_status = 'approved'
  AND m.usage_status = 'allowed_for_answering'
  AND EXISTS {
    MATCH (r)-[:HAS_INDEPENDENT_MEDICAL_REVIEW]->(mr:IndependentMedicalReview)
    WHERE mr.decision = 'approved'
  }
  AND EXISTS {
    MATCH (s)-[:HAS_INDEPENDENT_RIGHTS_REVIEW]->(rr:IndependentRightsReview)
    WHERE rr.decision = 'approved'
  }
RETURN r.relation_id AS usable_relation, m.claim_id AS claim_id, c.chunk_id AS chunk_id, s.source_id AS source_id;

// [4] SAFE-GATE AUDIT: mong doi approved=0, unblocked=0 (READ-ONLY)
CALL { MATCH (r:RelationCandidate) WHERE r.review_status = 'approved' RETURN count(r) AS approved_relations }
CALL { MATCH (m:MedicalClaim) WHERE m.review_status = 'approved' RETURN count(m) AS approved_claims }
CALL { MATCH (r:RelationCandidate) WHERE r.usage_status IS NULL OR r.usage_status <> 'blocked_for_answering' RETURN count(r) AS unblocked_relations }
CALL { MATCH (m:MedicalClaim) WHERE m.usage_status IS NULL OR m.usage_status <> 'blocked_for_answering' RETURN count(m) AS unblocked_claims }
RETURN approved_relations, approved_claims, unblocked_relations, unblocked_claims;

// [5] GRAPH - hien thi technical lineage da duoc xac minh ve mat lien ket (READ-ONLY)
MATCH p=(r:RelationCandidate)-[:SUPPORTED_BY_CLAIM]->(m:MedicalClaim)-[:HAS_EVIDENCE_CANDIDATE]->(c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
MATCH q=(r)-[:HAS_TECHNICAL_REVIEW]->(t:TechnicalReview)
RETURN p, q LIMIT 4;

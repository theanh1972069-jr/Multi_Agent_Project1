// GIAI DOAN 4 - BUOC 5K: REVIEW DOSSIER / APPROVAL READINESS
// CHAY TUNG KHOI RIENG TREN NEO4J AURA QUERY.
// 100% READ-ONLY. KHONG SUA review_status, usage_status, KHONG TAO APPROVAL NODE.

// [0] PRE-FLIGHT: kiem tra so luong va co che chan an toan.
CALL { MATCH (s:SourceDocument) RETURN count(s) AS sources }
CALL { MATCH (r:RelationCandidate) RETURN count(r) AS relations }
CALL { MATCH (m:MedicalClaim) RETURN count(m) AS claims }
CALL { MATCH (t:TechnicalReview) RETURN count(t) AS technical_reviews }
CALL { MATCH (r:RelationCandidate) WHERE r.review_status = 'approved' RETURN count(r) AS approved_relations }
CALL { MATCH (m:MedicalClaim) WHERE m.review_status = 'approved' RETURN count(m) AS approved_claims }
RETURN sources, relations, claims, technical_reviews, approved_relations, approved_claims;

// [1] SOURCE RIGHTS QUEUE: 7 tai lieu, phuc vu ra soat quyen su dung.
// Khong chon 'verified' neu chua co bang chung doc lap.
MATCH (s:SourceDocument)
RETURN s.source_id AS source_id,
       s.provider AS provider,
       s.title AS title,
       s.url AS url,
       coalesce(s.rights_status, 'not_recorded') AS rights_status,
       coalesce(s.medical_review_status, 'not_recorded') AS medical_review_status
ORDER BY source_id;

// [2] MEDICAL REVIEW QUEUE: 4 relation candidates va claim co chung nguon.
MATCH (r:RelationCandidate)-[:SUBJECT_CONCEPT]->(subject:MedicalConcept)
MATCH (r)-[:OBJECT_CONCEPT]->(object:MedicalConcept)
MATCH (r)-[:SUPPORTED_BY_CLAIM]->(m:MedicalClaim)
MATCH (m)-[:HAS_EVIDENCE_CANDIDATE]->(c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
RETURN r.relation_id AS relation_id,
       r.relation_type AS relation_type,
       subject.concept_id AS subject_id,
       object.concept_id AS object_id,
       m.claim_id AS claim_id,
       m.statement AS claim_statement,
       c.chunk_id AS chunk_id,
       s.source_id AS source_id,
       s.url AS source_url,
       r.review_status AS relation_status,
       m.review_status AS claim_status
ORDER BY relation_id;

// [3] KIEM TRA LIEN KET BI THIEU: du kien 0 het.
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
RETURN missing_subject, missing_object, missing_provenance, missing_technical_review;

// [4] FAIL-CLOSED PREVIEW: 4 relation ung vien, moi dong phai blocked=true.
// Khong la he thong phan quyen production, chi kiem tra trang thai nghien cuu.
MATCH (r:RelationCandidate)-[:SUPPORTED_BY_CLAIM]->(m:MedicalClaim)
MATCH (m)-[:HAS_EVIDENCE_CANDIDATE]->(:ChunkRef)-[:PART_OF]->(s:SourceDocument)
WITH DISTINCT r, m, s,
     EXISTS {
         MATCH (r)-[:HAS_INDEPENDENT_MEDICAL_REVIEW]->(mr:IndependentMedicalReview)
         WHERE mr.decision = 'approved'
     } AS independent_medical_ok,
     EXISTS {
         MATCH (s)-[:HAS_INDEPENDENT_RIGHTS_REVIEW]->(rr:IndependentRightsReview)
         WHERE rr.decision = 'approved'
     } AS independent_rights_ok
WITH r, m, s, independent_medical_ok, independent_rights_ok,
     (coalesce(r.review_status,'') = 'approved'
      AND coalesce(r.usage_status,'') = 'allowed_for_answering'
      AND coalesce(m.review_status,'') = 'approved'
      AND coalesce(m.usage_status,'') = 'allowed_for_answering'
      AND independent_medical_ok AND independent_rights_ok) AS permitted
RETURN r.relation_id AS relation_id, m.claim_id AS claim_id,
       s.source_id AS source_id,
       independent_medical_ok, independent_rights_ok,
       NOT permitted AS blocked
ORDER BY relation_id;

// [5] AI DUOC DUNG DE TRA LOI? Khi chua co review doc lap, ket qua du kien 0 hang.
MATCH (r:RelationCandidate)-[:SUPPORTED_BY_CLAIM]->(m:MedicalClaim)
MATCH (m)-[:HAS_EVIDENCE_CANDIDATE]->(:ChunkRef)-[:PART_OF]->(s:SourceDocument)
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
RETURN DISTINCT r.relation_id AS relation_id, m.claim_id AS claim_id, s.source_id AS source_id;

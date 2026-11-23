// PHASE 4 - STEP 5L | READ-ONLY CHECKS (run each block separately)
// This file does not approve or change any node, relationship or medical content.

// [0] Current Neo4j graph checkpoint
CALL { MATCH (s:SourceDocument) RETURN count(s) AS sources }
CALL { MATCH (c:ChunkRef) RETURN count(c) AS chunk_refs }
CALL { MATCH (:ChunkRef)-[p:PART_OF]->(:SourceDocument) RETURN count(p) AS chunk_links }
CALL { MATCH (r:RelationCandidate) RETURN count(r) AS relation_candidates }
CALL { MATCH (t:TechnicalReview) RETURN count(t) AS technical_reviews }
CALL { MATCH (r:RelationCandidate {review_status:'approved'}) RETURN count(r) AS approved_relations }
CALL { MATCH (m:MedicalClaim {review_status:'approved'}) RETURN count(m) AS approved_claims }
RETURN sources, chunk_refs, chunk_links, relation_candidates, technical_reviews,
       approved_relations, approved_claims;

// [1] Review-only queue: show the four relation candidates and the NIDDK chunk
MATCH (r:RelationCandidate)-[:SUPPORTED_BY_CLAIM]->(m:MedicalClaim)
MATCH (m)-[:HAS_EVIDENCE_CANDIDATE]->(c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
RETURN DISTINCT r.relation_id AS relation_id, m.claim_id AS claim_id,
       c.chunk_id AS chunk_id, s.source_id AS source_id,
       r.review_status AS relation_status, m.review_status AS claim_status,
       r.usage_status AS relation_usage, m.usage_status AS claim_usage
ORDER BY relation_id;

// [2] Strict future-evidence gate: should return ZERO rows with current unverified data.
// This is an illustrative research query, NOT a production medical authorization rule.
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
RETURN DISTINCT r.relation_id AS relation_id, m.claim_id AS claim_id,
       c.chunk_id AS chunk_id, s.source_id AS source_id;

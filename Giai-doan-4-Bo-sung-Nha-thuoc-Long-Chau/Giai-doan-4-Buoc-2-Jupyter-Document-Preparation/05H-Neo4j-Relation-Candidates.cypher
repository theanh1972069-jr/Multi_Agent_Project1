// GIAI DOAN 4 - BUOC 5H: RELATION CANDIDATES - NEO4J AURA
// Chay MOI KHOI rieng trong Neo4j Query, theo thu tu.
// CHI TAO UNVERIFIED RELATION CANDIDATES, khong tao quan he y khoa duoc phe duyet.
// Khong su dung LLM. Khong sua ChromaDB / NHANES model.

// [0] PRE-FLIGHT: claim, evidence va 5 concept phai ton tai (READ ONLY)
MATCH (m:MedicalClaim {claim_id:'RESEARCH-CLAIM-001'})
OPTIONAL MATCH (m)-[:HAS_EVIDENCE_CANDIDATE]->(c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
OPTIONAL MATCH (m)-[:MENTIONS_CONCEPT]->(concept:MedicalConcept)
RETURN m.claim_id AS claim_id,
       m.review_status AS claim_review,
       m.usage_status AS claim_usage,
       collect(DISTINCT s.source_id) AS sources,
       count(DISTINCT concept) AS concept_count;

// [1] Tao uniqueness constraint cho RelationCandidate (CHAY RIENG)
CREATE CONSTRAINT relation_candidate_id_unique IF NOT EXISTS
FOR (r:RelationCandidate) REQUIRE r.relation_id IS UNIQUE;

// [2] THUC HANH 1: them 1 quan he UNVERIFIED giua thua can / beo phi va type 2 diabetes
// Yeu cau: claim van la draft_unverified va blocked_for_answering, co nguon NIDDK-T2D-004.
MATCH (m:MedicalClaim {claim_id:'RESEARCH-CLAIM-001'})
MATCH (factor:MedicalConcept:RiskFactor {concept_id:'risk_factor:overweight_obesity'})
MATCH (disease:MedicalConcept:Disease {concept_id:'disease:type_2_diabetes'})
WHERE m.review_status='draft_unverified'
  AND m.usage_status='blocked_for_answering'
  AND EXISTS {
    MATCH (m)-[:HAS_EVIDENCE_CANDIDATE]->(:ChunkRef)-[:PART_OF]->(:SourceDocument {source_id:'NIDDK-T2D-004'})
  }
MERGE (relation:RelationCandidate {relation_id:'REL-CAND-001'})
ON CREATE SET relation.relation_type='RISK_FACTOR_FOR',
              relation.review_status='draft_unverified',
              relation.usage_status='blocked_for_answering',
              relation.evidence_status='candidate',
              relation.research_only=true,
              relation.created_at=datetime()
MERGE (relation)-[:SUBJECT_CONCEPT]->(factor)
MERGE (relation)-[:OBJECT_CONCEPT]->(disease)
MERGE (relation)-[:SUPPORTED_BY_CLAIM]->(m)
RETURN relation.relation_id AS relation_id,
       relation.relation_type AS relation_type,
       factor.name_vi AS subject,
       disease.name_vi AS object,
       relation.review_status AS review_status,
       relation.usage_status AS usage_status;

// [3] KIEM TRA KET QUA DU KIEN SAU KHOI [2] (READ ONLY)
CALL { MATCH (r:RelationCandidate) RETURN count(r) AS relation_candidates }
CALL { MATCH (:RelationCandidate)-[x:SUBJECT_CONCEPT]->(:MedicalConcept) RETURN count(x) AS subject_links }
CALL { MATCH (:RelationCandidate)-[x:OBJECT_CONCEPT]->(:MedicalConcept) RETURN count(x) AS object_links }
CALL { MATCH (:RelationCandidate)-[x:SUPPORTED_BY_CLAIM]->(:MedicalClaim) RETURN count(x) AS claim_links }
CALL { MATCH (r:RelationCandidate {review_status:'approved'}) RETURN count(r) AS approved_relations }
CALL { MATCH (r:RelationCandidate)
       WHERE r.usage_status IS NULL OR r.usage_status <> 'blocked_for_answering'
       RETURN count(r) AS not_blocked_relations }
RETURN relation_candidates, subject_links, object_links, claim_links,
       approved_relations, not_blocked_relations;

// [4] HIEN THI DO THI RELATION CANDIDATE (READ ONLY)
MATCH p=(r:RelationCandidate {relation_id:'REL-CAND-001'})-[:SUBJECT_CONCEPT|OBJECT_CONCEPT|SUPPORTED_BY_CLAIM]->(n)
RETURN p LIMIT 10;

// [5] MO RONG - CHI CHAY SAU KHI KHANG DINH [2]-[4] DUNG
// Tao them 3 RELATION CANDIDATES, giu trang thai CHUA KIEM CHUNG.
MATCH (m:MedicalClaim {claim_id:'RESEARCH-CLAIM-001'})
MATCH (disease:MedicalConcept:Disease {concept_id:'disease:type_2_diabetes'})
WHERE m.review_status='draft_unverified'
  AND m.usage_status='blocked_for_answering'
  AND EXISTS {
    MATCH (m)-[:HAS_EVIDENCE_CANDIDATE]->(:ChunkRef)-[:PART_OF]->(:SourceDocument {source_id:'NIDDK-T2D-004'})
  }
WITH m, disease
UNWIND [
  {relation_id:'REL-CAND-002', concept_id:'risk_factor:physical_inactivity', relation_type:'RISK_FACTOR_FOR'},
  {relation_id:'REL-CAND-003', concept_id:'mechanism:insulin_resistance', relation_type:'MECHANISM_ASSOCIATED_WITH'},
  {relation_id:'REL-CAND-004', concept_id:'genetic_factor:genes', relation_type:'GENETIC_CONTRIBUTION_TO'}
] AS item
MATCH (concept:MedicalConcept {concept_id:item.concept_id})
MERGE (relation:RelationCandidate {relation_id:item.relation_id})
ON CREATE SET relation.relation_type=item.relation_type,
              relation.review_status='draft_unverified',
              relation.usage_status='blocked_for_answering',
              relation.evidence_status='candidate',
              relation.research_only=true,
              relation.created_at=datetime()
MERGE (relation)-[:SUBJECT_CONCEPT]->(concept)
MERGE (relation)-[:OBJECT_CONCEPT]->(disease)
MERGE (relation)-[:SUPPORTED_BY_CLAIM]->(m)
RETURN relation.relation_id AS relation_id, relation.relation_type AS relation_type,
       concept.concept_id AS subject, disease.concept_id AS object,
       relation.review_status AS status
ORDER BY relation_id;

// [6] AUDIT READ ONLY: CHAY LAI [3] sau khoi [5] de xem 4/4, 0 approved, 0 not_blocked.
// Khong tao (:RiskFactor)-[:CAUSES|INCREASES_RISK]->(:Disease) truc tiep o buoc nay.

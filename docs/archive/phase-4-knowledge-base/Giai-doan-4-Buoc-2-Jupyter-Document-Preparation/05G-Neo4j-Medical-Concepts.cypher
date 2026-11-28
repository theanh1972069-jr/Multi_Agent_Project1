// GIAI DOAN 4 - BUOC 5G: MEDICAL CONCEPT NODES
// Neo4j Aura Console > Query. Chay TUNG KHOI theo thu tu.
// Chi tao thuc the/quan he MENTIONS_CONCEPT, KHONG tao quan he nhan qua/tu van.
// Claim dau vao: RESEARCH-CLAIM-001 (draft_unverified, blocked_for_answering).

// [0] PRE-FLIGHT: XEM NOI DUNG CLAIM THUC TE - CHI DOC
MATCH (m:MedicalClaim {claim_id:'RESEARCH-CLAIM-001'})
OPTIONAL MATCH (m)-[:HAS_EVIDENCE_CANDIDATE]->(c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
RETURN m.claim_id AS claim_id, m.statement AS statement,
       m.review_status AS review_status, m.usage_status AS usage_status,
       c.chunk_id AS chunk_id, s.source_id AS source_id;

// [1] UNIQUE CONSTRAINT: CHAY RIENG
CREATE CONSTRAINT medical_concept_id_unique IF NOT EXISTS
FOR (n:MedicalConcept) REQUIRE n.concept_id IS UNIQUE;

// [2A] TAO NODE DISEASE: CHAY RIENG
MERGE (d:MedicalConcept:Disease {concept_id:'disease:type_2_diabetes'})
ON CREATE SET d.name_vi='Bệnh tiểu đường type 2',
              d.name_en='Type 2 diabetes',
              d.concept_type='Disease',
              d.review_status='draft_unverified',
              d.usage_status='blocked_for_answering',
              d.created_at=datetime()
RETURN d.concept_id AS concept_id, labels(d) AS labels;

// [2B] TAO 4 NODE KHAC NHAU: CHAY RIENG
MERGE (a:MedicalConcept:RiskFactor {concept_id:'risk_factor:overweight_obesity'})
ON CREATE SET a.name_vi='Thừa cân hoặc béo phì', a.name_en='Overweight and obesity',
              a.concept_type='RiskFactor', a.review_status='draft_unverified',
              a.usage_status='blocked_for_answering', a.created_at=datetime()
MERGE (b:MedicalConcept:RiskFactor {concept_id:'risk_factor:physical_inactivity'})
ON CREATE SET b.name_vi='Ít hoạt động thể chất', b.name_en='Physical inactivity',
              b.concept_type='RiskFactor', b.review_status='draft_unverified',
              b.usage_status='blocked_for_answering', b.created_at=datetime()
MERGE (c:MedicalConcept:Mechanism {concept_id:'mechanism:insulin_resistance'})
ON CREATE SET c.name_vi='Kháng insulin', c.name_en='Insulin resistance',
              c.concept_type='Mechanism', c.review_status='draft_unverified',
              c.usage_status='blocked_for_answering', c.created_at=datetime()
MERGE (d:MedicalConcept:GeneticFactor {concept_id:'genetic_factor:genes'})
ON CREATE SET d.name_vi='Yếu tố di truyền', d.name_en='Genes and genetic factors',
              d.concept_type='GeneticFactor', d.review_status='draft_unverified',
              d.usage_status='blocked_for_answering', d.created_at=datetime()
RETURN a.concept_id AS risk1, b.concept_id AS risk2,
       c.concept_id AS mechanism, d.concept_id AS genetics;

// [3] LIEN KET CLAIM -> 5 CONCEPT, CHI KHI CLAIM CO EVIDENCE DUNG NGUON VA BI CHAN TU VAN
MATCH (m:MedicalClaim {claim_id:'RESEARCH-CLAIM-001'})
WHERE m.review_status='draft_unverified'
  AND m.usage_status='blocked_for_answering'
  AND EXISTS {
    MATCH (m)-[:HAS_EVIDENCE_CANDIDATE]->(:ChunkRef)-[:PART_OF]->(:SourceDocument {source_id:'NIDDK-T2D-004'})
  }
MATCH (c:MedicalConcept)
WHERE c.concept_id IN [
  'disease:type_2_diabetes',
  'risk_factor:overweight_obesity',
  'risk_factor:physical_inactivity',
  'mechanism:insulin_resistance',
  'genetic_factor:genes'
]
MERGE (m)-[r:MENTIONS_CONCEPT]->(c)
ON CREATE SET r.review_status='draft_unverified',
              r.usage_status='blocked_for_answering',
              r.created_at=datetime()
RETURN m.claim_id AS claim_id, count(DISTINCT c) AS linked_concepts;

// [4] KIEM TRA KET QUA - READ ONLY
CALL { MATCH (c:MedicalConcept) RETURN count(c) AS concepts }
CALL { MATCH (:MedicalClaim {claim_id:'RESEARCH-CLAIM-001'})-[r:MENTIONS_CONCEPT]->(:MedicalConcept)
       RETURN count(r) AS mention_links }
CALL { MATCH (m:MedicalClaim {review_status:'approved'}) RETURN count(m) AS approved_claims }
CALL { MATCH (m:MedicalClaim)
       WHERE m.usage_status IS NULL OR m.usage_status <> 'blocked_for_answering'
       RETURN count(m) AS claims_not_blocked }
RETURN concepts, mention_links, approved_claims, claims_not_blocked;

// [5] KIEM TRA TEN + NHAN THUC THE - READ ONLY
MATCH (c:MedicalConcept)
RETURN c.concept_id AS concept_id, c.name_vi AS name_vi,
       labels(c) AS labels, c.review_status AS review_status
ORDER BY concept_id;

// [6] HIEN THI GRAPH - READ ONLY
MATCH p=(m:MedicalClaim {claim_id:'RESEARCH-CLAIM-001'})-[:MENTIONS_CONCEPT]->(c:MedicalConcept)
RETURN p LIMIT 20;

// [7] KIEM TRA LIEN KET BANG CHUNG - READ ONLY
MATCH p=(m:MedicalClaim {claim_id:'RESEARCH-CLAIM-001'})-[:HAS_EVIDENCE_CANDIDATE]->(c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
RETURN p LIMIT 5;

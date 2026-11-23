// 5D-01: READ ONLY - PRECHECK 7 SourceDocument; 3 chunk refs already exist
MATCH (s:SourceDocument)
RETURN count(s) AS source_documents, collect(s.source_id) AS source_ids;

// 5D-02: READ ONLY - after import; run as a separate query
CALL { MATCH (s:SourceDocument) RETURN count(s) AS sources }
CALL { MATCH (t:Topic) RETURN count(t) AS topics }
CALL { MATCH ()-[r:COVERS_TOPIC]->() RETURN count(r) AS topic_links }
CALL { MATCH (c:ChunkRef) RETURN count(c) AS chunk_refs }
CALL { MATCH (:ChunkRef)-[r:PART_OF]->(:SourceDocument) RETURN count(r) AS chunk_links }
CALL { MATCH (m:MedicalClaim) RETURN count(m) AS medical_claims }
RETURN sources, topics, topic_links, chunk_refs, chunk_links, medical_claims;

// 5D-03: READ ONLY - chunk counts by source, compare with Step 3 report
MATCH (c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
RETURN s.source_id AS source_id, count(DISTINCT c) AS linked_chunks
ORDER BY source_id;

// 5D-04: READ ONLY - orphan chunks; expected 0
MATCH (c:ChunkRef)
WHERE NOT (c)-[:PART_OF]->(:SourceDocument)
RETURN count(c) AS orphan_chunk_refs;

// 5D-05: READ ONLY - inspect graph without MedicalClaim
MATCH p=(c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
RETURN p LIMIT 25;

// 5D-06: READ ONLY - no approved MedicalClaim should exist
MATCH (c:MedicalClaim {review_status:'approved'})
RETURN count(c) AS approved_claims;

// 05E-01 — ĐỌC-CHỈ: tổng số node, quan hệ và orphan.
// Chạy từng truy vấn trên Neo4j Aura -> Query. Không chạy CREATE/MERGE.
CALL { MATCH (s:SourceDocument) RETURN count(s) AS source_documents }
CALL { MATCH (t:Topic) RETURN count(t) AS topics }
CALL { MATCH ()-[r:COVERS_TOPIC]->() RETURN count(r) AS topic_links }
CALL { MATCH (c:ChunkRef) RETURN count(c) AS chunk_refs }
CALL { MATCH (:ChunkRef)-[r:PART_OF]->(:SourceDocument) RETURN count(r) AS chunk_links }
CALL { MATCH (c:ChunkRef) WHERE NOT (c)-[:PART_OF]->(:SourceDocument) RETURN count(c) AS orphan_chunks }
CALL { MATCH (m:MedicalClaim) WHERE m.review_status='approved' RETURN count(m) AS approved_medical_claims }
RETURN source_documents, topics, topic_links, chunk_refs,
       chunk_links, orphan_chunks, approved_medical_claims;

// 05E-02 — ĐỌC-CHỈ: số chunks liên kết từng tài liệu.
MATCH (c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
RETURN s.source_id AS source_id, count(DISTINCT c) AS chunks
ORDER BY source_id;

// 05E-03 — ĐỌC-CHỈ: một ChunkRef cụ thể và chủ đề của tài liệu.
// Thay ID bằng một chunk_id từ kết quả của bạn nếu cần.
MATCH (c:ChunkRef)-[:PART_OF]->(s:SourceDocument)
OPTIONAL MATCH (s)-[:COVERS_TOPIC]->(t:Topic)
RETURN c.chunk_id AS chunk_id, s.source_id AS source_id,
       s.title AS title, s.url AS url,
       collect(DISTINCT t.name) AS topics,
       c.metadata_sync_status AS sync_status,
       s.rights_status AS rights_status
ORDER BY source_id, chunk_id
LIMIT 10;

// 05E-04 — ĐỌC-CHỈ: xem 10 liên kết trên đồ thị.
MATCH p=(c:ChunkRef)-[:PART_OF]->(s:SourceDocument)-[:COVERS_TOPIC]->(t:Topic)
RETURN p LIMIT 10;

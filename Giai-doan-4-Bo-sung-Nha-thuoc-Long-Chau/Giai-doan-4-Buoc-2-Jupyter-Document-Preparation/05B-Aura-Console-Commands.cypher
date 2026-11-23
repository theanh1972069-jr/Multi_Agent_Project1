// Giai đoạn 4 – Bước 5B: Neo4j AuraDB / Neo4j Query
// CHẠY MỖI KHỐI LỆNH RIÊNG TRÊN NEO4J QUERY.
// Chỉ tạo metadata nguồn và chủ đề; KHÔNG tạo quan hệ y khoa đã được xác minh.

// 1A. Uniqueness constraint cho SourceDocument
CREATE CONSTRAINT source_document_source_id IF NOT EXISTS
FOR (s:SourceDocument) REQUIRE s.source_id IS UNIQUE;

// 1B. Uniqueness constraint cho Topic
CREATE CONSTRAINT topic_topic_id IF NOT EXISTS
FOR (t:Topic) REQUIRE t.topic_id IS UNIQUE;

// 2. Đưa 7 nguồn vào Neo4j dưới dạng metadata.
// 'approved_research' trên registry cũ là tự khai; không tự đặt quyền sử dụng là verified.
UNWIND [
  {id:'CDC-T2D-001', provider:'CDC', title:'About Type 2 Diabetes', url:'https://www.cdc.gov/diabetes/about/about-type-2-diabetes.html'},
  {id:'CDC-RISK-002', provider:'CDC', title:'Diabetes Risk Factors', url:'https://www.cdc.gov/diabetes/risk-factors/index.html'},
  {id:'NIDDK-DIAG-003', provider:'NIDDK', title:'Diabetes Tests & Diagnosis', url:'https://www.niddk.nih.gov/health-information/diabetes/overview/tests-diagnosis'},
  {id:'NIDDK-T2D-004', provider:'NIDDK', title:'Type 2 Diabetes', url:'https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/type-2-diabetes'},
  {id:'WHO-DIAB-005', provider:'WHO', title:'Diabetes', url:'https://www.who.int/health-topics/diabetes'},
  {id:'LC-HBA1C-006', provider:'Long Chau', title:'HbA1c và tiền tiểu đường', url:'https://nhathuoclongchau.com.vn/bai-viet/hb-a1c-bao-nhieu-la-tien-tieu-duong-nhan-biet-va-cai-thien.html'},
  {id:'LC-STAGES-007', provider:'Long Chau', title:'Các giai đoạn bệnh tiểu đường', url:'https://nhathuoclongchau.com.vn/bai-viet/cac-giai-doan-cua-benh-tieu-duong-20966.html'}
] AS d
MERGE (s:SourceDocument {source_id:d.id})
ON CREATE SET
  s.created_at = datetime(),
  s.rights_status = 'needs_independent_check',
  s.medical_review_status = 'pending',
  s.registry_approval = 'self_declared_research'
SET s.provider = d.provider,
    s.title = d.title,
    s.url = d.url
RETURN count(s) AS source_documents_processed;

// 3. Tạo node Chủ đề (không phải khẳng định y khoa).
UNWIND [
  {id:'diabetes', name:'Diabetes'},
  {id:'type_2_diabetes', name:'Type 2 diabetes'},
  {id:'risk_factors', name:'Risk factors'},
  {id:'diagnosis', name:'Diagnosis and testing'},
  {id:'hba1c', name:'HbA1c'},
  {id:'disease_stages', name:'Disease stages'}
] AS d
MERGE (t:Topic {topic_id:d.id})
SET t.name = d.name
RETURN count(t) AS topics_processed;

// 4. Liên kết bài viết và chủ đề suy ra từ TIÊU ĐỀ.
// Đây KHÔNG PHẢI quan hệ nguy cơ, xét nghiệm, chẩn đoán y khoa.
UNWIND [
  {s:'CDC-T2D-001', t:'type_2_diabetes'},
  {s:'CDC-RISK-002', t:'risk_factors'},
  {s:'NIDDK-DIAG-003', t:'diagnosis'},
  {s:'NIDDK-T2D-004', t:'type_2_diabetes'},
  {s:'WHO-DIAB-005', t:'diabetes'},
  {s:'LC-HBA1C-006', t:'hba1c'},
  {s:'LC-STAGES-007', t:'disease_stages'}
] AS row
MATCH (s:SourceDocument {source_id:row.s})
MATCH (t:Topic {topic_id:row.t})
MERGE (s)-[r:COVERS_TOPIC]->(t)
SET r.basis = 'document_title_only', r.medical_verified = false
RETURN count(r) AS topic_links_processed;

// 5A. Kiểm tra tổng số (trên database mới/trống dự kiến 7, 6, 7).
MATCH (s:SourceDocument)
WITH count(s) AS sources
MATCH (t:Topic)
WITH sources, count(t) AS topics
MATCH ()-[r:COVERS_TOPIC]->()
RETURN sources, topics, count(r) AS topic_links;

// 5B. Hiển thị đồ thị trong Neo4j Query
MATCH p=(s:SourceDocument)-[:COVERS_TOPIC]->(t:Topic)
RETURN p LIMIT 25;

// 5C. Kiểm tra metadata provenance
MATCH (s:SourceDocument)-[:COVERS_TOPIC]->(t:Topic)
RETURN s.source_id AS source_id,
       s.provider AS provider,
       t.name AS topic,
       s.rights_status AS rights_status,
       s.medical_review_status AS medical_review
ORDER BY source_id;

// 5D. Không có kết luận y khoa được phê duyệt ở bước này.
MATCH (c:MedicalClaim {review_status:'approved'})
RETURN count(c) AS approved_medical_claims;

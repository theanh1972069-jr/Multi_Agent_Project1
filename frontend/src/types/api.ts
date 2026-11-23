export type UserRole = 'user' | 'admin';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole | string;
  is_active: boolean;
  birth_year: number | null;
  gender: 1 | 2 | number | null;
  preferred_language: string;
  created_at: string;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface UserRegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface UserLoginRequest {
  email: string;
  password: string;
}

export interface UserProfileUpdateRequest {
  full_name?: string | null;
  birth_year?: number | null;
  gender?: 1 | 2 | null;
  preferred_language?: string | null;
}

export interface HealthResponse {
  status: 'ok' | 'degraded' | string;
  database: {
    connected: boolean;
  };
  ml_model: {
    loaded: boolean;
    model_version: string | null;
    model_name: string | null;
    model_sha256: string | null;
  };
  knowledge_base: {
    active_documents: number;
    total_chunks: number;
    kg_source: 'neo4j' | 'local_mirror' | string;
    neo4j_configured: boolean;
    neo4j_reachable: boolean;
  };
  llm: {
    provider: string;
    model: string;
    reachable: boolean;
  };
}

export interface AgentStep {
  step_order: number;
  agent_name: string;
  status: 'completed' | 'out_of_scope' | 'needs_input' | 'failed' | string;
  latency_ms: number;
  summary: string;
  error_code?: string | null;
}

export interface FeatureContribution {
  feature: string;
  label_vi: string;
  value: number | null;
  contribution: number;
  direction: 'increase' | 'decrease';
}

export interface PredictionResultPayload {
  model_version: string;
  model_name: string;
  model_sha256: string;
  threshold?: number;
  threshold_low: number;
  threshold_high: number;
  model_score: number;
  predicted_label: number;
  risk_band: 'low' | 'moderate' | 'elevated' | string;
  feature_contributions: FeatureContribution[];
  warning?: string;
  limitations?: string[];
}

export interface DerivedFeatures {
  bmi: number;
  whtr: number;
  whr: number | null;
}

export interface CitationItem {
  index: number;
  chunk_id: string;
  source_id: string;
  title: string;
  publisher: string;
  url?: string | null;
  snippet: string;
  score: number;
}

export interface KGRelation {
  source_node: string;
  source_type: string;
  relation: string;
  target_node: string;
  target_type: string;
  source_ids: string[];
  description: string;
}

export interface AssessmentCreateRequest {
  age: number;
  gender: 1 | 2;
  height_cm: number;
  weight_kg: number;
  waist_cm: number;
  hip_cm?: number | null;
  previously_diagnosed_diabetes: boolean;
  is_pregnant?: boolean | null;
}

export interface AssessmentOut {
  id: string;
  request_id: string;
  status: 'completed' | 'out_of_scope' | 'needs_input' | 'failed' | string;
  raw_inputs: Record<string, unknown>;
  derived_features: DerivedFeatures | null;
  prediction: PredictionResultPayload | null;
  summary_text: string;
  recommendations: string[];
  citations: CitationItem[];
  kg_relations: KGRelation[];
  limitations: string[];
  llm_used: boolean;
  llm_fallback: boolean;
  agent_steps: AgentStep[];
  total_latency_ms: number;
  error_code?: string | null;
  created_at: string;
}

export interface ChatSessionCreateRequest {
  title?: string;
  linked_assessment_id?: string | null;
}

export interface ChatSessionOut {
  id: string;
  title: string;
  linked_assessment_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatMessageCreateRequest {
  content: string;
  linked_assessment_id?: string | null;
}

export interface ChatMessageOut {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | string;
  content: string;
  answer: string | null;
  intent: string | null;
  citations: CitationItem[];
  kg_relations: KGRelation[];
  kg_source: string | null;
  redirect_to_assessment: boolean;
  safety_flag: string | null;
  llm_used: boolean;
  llm_fallback: boolean;
  agent_steps: AgentStep[];
  total_latency_ms: number;
  created_at: string;
}

export interface KnowledgeSourceOut {
  id: string;
  source_id: string;
  title: string;
  publisher: string;
  source_url: string | null;
  language: string;
  status: string;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeGraphNode {
  id: string;
  label: string;
  type: string;
  source_ids: string[];
  keywords?: string[];
  description?: string;
}

export interface KnowledgeGraphEdge {
  source: string;
  target: string;
  relation: string;
  source_ids: string[];
  description?: string;
}

export interface KnowledgeGraphOut {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  kg_source: string;
}

export interface AdminStatsOut {
  total_users: number;
  total_assessments: number;
  active_documents: number;
  total_documents: number;
  total_chunks: number;
  total_agent_runs: number;
  agent_status_counts: Record<string, number>;
  avg_latency_ms: number;
  per_agent_latency_ms: Record<string, number>;
}

export interface AdminAgentRunOut {
  id: string;
  request_id: string;
  user_id: string | null;
  task_type: string;
  status: string;
  total_latency_ms: number;
  llm_provider: string;
  llm_model: string;
  error_code: string | null;
  created_at: string;
  agent_steps: AgentStep[];
}

export interface AdminDocumentOut {
  id: string;
  source_id: string;
  title: string;
  publisher: string;
  source_url: string | null;
  language: string;
  status: 'active' | 'inactive' | string;
  chunk_count: number;
  uploaded_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminDocumentStatusUpdateRequest {
  status: 'active' | 'inactive';
}

export interface AdminDocumentDeleteOut {
  deleted: boolean;
  id: string;
  source_id: string;
}

export interface AdminUserUpdateRequest {
  is_active?: boolean | null;
  role?: 'user' | 'admin' | null;
}

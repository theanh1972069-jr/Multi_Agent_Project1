import type {
  AdminAgentRunOut,
  AdminDocumentDeleteOut,
  AdminDocumentOut,
  AdminDocumentStatusUpdateRequest,
  AdminStatsOut,
  AdminUserUpdateRequest,
  AssessmentCreateRequest,
  AssessmentOut,
  AuthTokenResponse,
  ChatMessageCreateRequest,
  ChatMessageOut,
  ChatSessionCreateRequest,
  ChatSessionOut,
  HealthResponse,
  KnowledgeGraphOut,
  KnowledgeSourceOut,
  User,
  UserLoginRequest,
  UserProfileUpdateRequest,
  UserRegisterRequest,
} from '../types/api';

const TOKEN_STORAGE_KEY = 'diaguard_access_token';
const API_BASE = '/api/v1';

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

export function getStoredToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string | null): void {
  try {
    if (token) {
      window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
    } else {
      window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  } catch {
    // Ignore storage errors in restricted contexts
  }
}

let onUnauthorizedCallback: (() => void) | null = null;

export function registerUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorizedCallback = handler;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  authenticated = true,
): Promise<T> {
  const headers = new Headers(options.headers);
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;
  if (!isFormData && !headers.has('Content-Type') && options.body !== undefined) {
    headers.set('Content-Type', 'application/json');
  }

  if (authenticated) {
    const token = getStoredToken();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401 && authenticated && onUnauthorizedCallback) {
    onUnauthorizedCallback();
  }

  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');
  const payload = isJson ? await response.json().catch(() => null) : await response.text().catch(() => '');

  if (!response.ok) {
    let detail = `Lỗi máy chủ (HTTP ${response.status})`;
    if (payload && typeof payload === 'object' && 'detail' in payload) {
      const rawDetail = (payload as { detail: unknown }).detail;
      if (typeof rawDetail === 'string') {
        detail = rawDetail;
      } else if (Array.isArray(rawDetail)) {
        detail = rawDetail
          .map((item) => (typeof item === 'object' && item && 'msg' in item ? String(item.msg) : String(item)))
          .join('; ');
      }
    } else if (typeof payload === 'string' && payload.trim()) {
      detail = payload;
    }
    throw new ApiError(response.status, detail);
  }

  return payload as T;
}

export const apiClient = {
  // Health
  getHealth(): Promise<HealthResponse> {
    return request<HealthResponse>('/health', { method: 'GET' }, false);
  },

  // Auth
  login(payload: UserLoginRequest): Promise<AuthTokenResponse> {
    return request<AuthTokenResponse>(
      '/auth/login',
      { method: 'POST', body: JSON.stringify(payload) },
      false,
    );
  },

  register(payload: UserRegisterRequest): Promise<AuthTokenResponse> {
    return request<AuthTokenResponse>(
      '/auth/register',
      { method: 'POST', body: JSON.stringify(payload) },
      false,
    );
  },

  getMe(): Promise<User> {
    return request<User>('/auth/me', { method: 'GET' });
  },

  updateMe(payload: UserProfileUpdateRequest): Promise<User> {
    return request<User>('/auth/me', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  // Assessments
  createAssessment(payload: AssessmentCreateRequest): Promise<AssessmentOut> {
    return request<AssessmentOut>('/assessments', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  listAssessments(): Promise<AssessmentOut[]> {
    return request<AssessmentOut[]>('/assessments', { method: 'GET' });
  },

  getAssessment(assessmentId: string): Promise<AssessmentOut> {
    return request<AssessmentOut>(`/assessments/${encodeURIComponent(assessmentId)}`, {
      method: 'GET',
    });
  },

  // Chat
  listChatSessions(): Promise<ChatSessionOut[]> {
    return request<ChatSessionOut[]>('/chat/sessions', { method: 'GET' });
  },

  createChatSession(payload: ChatSessionCreateRequest): Promise<ChatSessionOut> {
    return request<ChatSessionOut>('/chat/sessions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  listChatMessages(sessionId: string): Promise<ChatMessageOut[]> {
    return request<ChatMessageOut[]>(
      `/chat/sessions/${encodeURIComponent(sessionId)}/messages`,
      { method: 'GET' },
    );
  },

  postChatMessage(
    sessionId: string,
    payload: ChatMessageCreateRequest,
  ): Promise<ChatMessageOut> {
    return request<ChatMessageOut>(
      `/chat/sessions/${encodeURIComponent(sessionId)}/messages`,
      { method: 'POST', body: JSON.stringify(payload) },
    );
  },

  // Knowledge
  listKnowledgeSources(): Promise<KnowledgeSourceOut[]> {
    return request<KnowledgeSourceOut[]>('/knowledge/sources', { method: 'GET' });
  },

  getKnowledgeGraph(): Promise<KnowledgeGraphOut> {
    return request<KnowledgeGraphOut>('/knowledge/graph', { method: 'GET' });
  },

  // Admin
  getAdminStats(): Promise<AdminStatsOut> {
    return request<AdminStatsOut>('/admin/stats', { method: 'GET' });
  },

  listAdminAgentRuns(limit = 50): Promise<AdminAgentRunOut[]> {
    return request<AdminAgentRunOut[]>(`/admin/agent-runs?limit=${limit}`, { method: 'GET' });
  },

  listAdminDocuments(): Promise<AdminDocumentOut[]> {
    return request<AdminDocumentOut[]>('/admin/documents', { method: 'GET' });
  },

  uploadAdminDocument(formData: FormData): Promise<AdminDocumentOut> {
    return request<AdminDocumentOut>('/admin/documents/upload', {
      method: 'POST',
      body: formData,
    });
  },

  updateAdminDocumentStatus(
    docId: string,
    payload: AdminDocumentStatusUpdateRequest,
  ): Promise<AdminDocumentOut> {
    return request<AdminDocumentOut>(`/admin/documents/${encodeURIComponent(docId)}/status`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  deleteAdminDocument(docId: string): Promise<AdminDocumentDeleteOut> {
    return request<AdminDocumentDeleteOut>(`/admin/documents/${encodeURIComponent(docId)}`, {
      method: 'DELETE',
    });
  },

  listAdminUsers(): Promise<User[]> {
    return request<User[]>('/admin/users', { method: 'GET' });
  },

  updateAdminUser(userId: string, payload: AdminUserUpdateRequest): Promise<User> {
    return request<User>(`/admin/users/${encodeURIComponent(userId)}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },
};

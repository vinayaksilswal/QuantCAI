/**
 * API Client for QuantCAI Backend
 */

const isLocal = typeof window !== 'undefined' && window.location.hostname === 'localhost';
const API_URL = isLocal ? '' : (import.meta.env.VITE_API_URL || 'https://quantcai.onrender.com');
export const API_BASE = API_URL && API_URL.endsWith('/') ? API_URL.slice(0, -1) : API_URL;

let authToken: string | null = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;

export const setToken = (token: string | null) => {
  authToken = token;
  if (typeof window !== 'undefined') {
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('access_token');
    }
  }
};

export const getAuthToken = () => authToken;

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const base = API_BASE.endsWith('/') ? API_BASE.slice(0, -1) : API_BASE;
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${base}${path}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const config: RequestInit = {
    ...options,
    headers,
    credentials: 'include', // Important for sending/receiving HTTP-Only cookies
  };

  const res = await fetch(url, config);

  if (res.status === 401 && endpoint !== '/api/auth/refresh' && endpoint !== '/api/auth/login') {
    // Attempt to refresh token
    try {
      const refreshRes = await authApi.refresh();
      if (refreshRes.access_token) {
        setToken(refreshRes.access_token);
        // Retry original request with new token
        const retryHeaders = { ...headers, 'Authorization': `Bearer ${refreshRes.access_token}` };
        const retryRes = await fetch(url, { ...config, headers: retryHeaders });
        if (retryRes.ok) return retryRes.json();
      }
    } catch (refreshErr) {
      console.error('Session expired, please login again.');
      setToken(null);
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    const errorMessage = typeof err.detail === 'string'
      ? err.detail
      : typeof err.detail === 'object' && err.detail?.message
        ? err.detail.message
        : JSON.stringify(err.detail) || `HTTP ${res.status}`;

    // Trigger upgrade modal for payment-required responses (Finding #7)
    if (res.status === 402) {
      const reason = typeof err.detail === 'object' ? err.detail?.error : null;
      const reasonMap: Record<string, string> = {
        'QUBIT_LIMIT_EXCEEDED': 'qubits',
        'DEPTH_LIMIT_EXCEEDED': 'depth',
        'SHOTS_LIMIT_EXCEEDED': 'shots',
        'NOISE_MODEL_RESTRICTED': 'noise',
        'AI_LIMIT_EXCEEDED': 'chats',
        'PQC_LIMIT_EXCEEDED': 'pqc',
        'RUN_LIMIT_EXCEEDED': 'runs',
      };
      const modalReason = reason ? reasonMap[reason] || null : null;
      window.dispatchEvent(
        new CustomEvent('show-upgrade-modal', { detail: { reason: modalReason } })
      );
    }

    // Show rate limit toast for 429
    if (res.status === 429) {
      const resetIn = typeof err.detail === 'object' ? err.detail?.reset_in_seconds : null;
      const msg = resetIn 
        ? `Rate limit reached. Try again in ${Math.ceil(resetIn / 60)} minute(s).`
        : 'Rate limit reached. Please wait before retrying.';
      // Dispatch a custom event so the toast system can handle it
      window.dispatchEvent(new CustomEvent('show-rate-limit', { detail: { message: msg } }));
    }

    throw new Error(errorMessage);
  }
  return res.json();
}

export interface User { id: number; email: string; name: string; role: string; is_active: boolean; is_blocked: boolean; email_verified: boolean; created_at: string; updated_at: string; token_version: number; failed_login_attempts?: number; locked_until?: string | null; verification_sent_at?: string | null; }
export interface Post { id: number; title: string; body: string; author: any; comments: any[]; likes: any[]; created_at: string; }
export interface Comment { id: number; body: string; author: any; created_at: string; }
export interface TokenResponse { access_token: string; refresh_token?: string; token_type: string; }
export interface Circuit { id?: number; name: string; description?: string; num_wires: number; gates: any[]; created_at?: string; updated_at?: string; user_id?: number; }
export interface CircuitSimulationResult { state_vector: number[]; probabilities: number[]; measurements?: number[]; }
export interface NotificationResponse { id: number; email: string; message: string; created_at: string; }
export interface PageProgress { page_key: string; read_at: string; }
export interface LearnBlock { id: number; title: string; body_md: string; image_url?: string; author_id: number; created_at: string; }
export interface SystemStats { users: number; posts: number; comments: number; likes: number; subscribers: number; circuits: number; refresh_tokens: number; email_verification_tokens: number; failed_login_users: number; locked_accounts: number; unverified_emails: number; }

export const authApi = {
  login: (email: string, password: string) => fetchApi<TokenResponse>('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  register: (email: string, password: string, name: string) => fetchApi<TokenResponse>('/api/auth/register', { method: 'POST', body: JSON.stringify({ email, password, name }) }),
  logout: () => fetchApi('/api/auth/logout', { method: 'POST' }),
  getMe: () => fetchApi<User>('/api/auth/me'),
  refresh: () => fetchApi<TokenResponse>('/api/auth/refresh', { method: 'POST' }),
  getAuthConfig: () => fetchApi<{ google_client_id: string; google_redirect_uri: string }>('/api/auth/config'),
  loginWithGoogle: (idToken: string) => fetchApi<TokenResponse>('/api/auth/oauth/google', { method: 'POST', body: JSON.stringify({ id_token: idToken }) }),
  sendVerification: () => fetchApi('/api/auth/verify/send', { method: 'POST' }),
  resendVerification: (email: string) => fetchApi('/api/auth/verify/resend', { method: 'POST', body: JSON.stringify({ email }) }),
  verifyEmail: (token: string) => fetchApi('/api/auth/verify/confirm', { method: 'POST', body: JSON.stringify({ token }) }),
  getVerificationStatus: () => fetchApi<{ email_verified: boolean; verification_sent_at?: string }>('/api/auth/verify/status'),
  listNotifications: () => fetchApi<NotificationResponse[]>('/api/notify'),
  getProgress: () => fetchApi<PageProgress[]>('/api/progress'),
  trackProgress: (pageKey: string) => fetchApi('/api/progress', { method: 'POST', body: JSON.stringify({ page_key: pageKey }) }),
};

export const contentApi = {
  getLearnBlocks: () => fetchApi<LearnBlock[]>('/api/learn-blocks'),
  createLearnBlock: (data: Partial<LearnBlock>) => fetchApi<LearnBlock>('/api/learn-blocks', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  sendContactMessage: (data: { email: string; message: string }) => fetchApi('/api/notify', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  subscribe: (email: string) => fetchApi<{ message: string; subscribed: boolean }>(`/api/subscribe?email=${encodeURIComponent(email)}`, { method: 'POST' }),
};

export const communityApi = {
  getPosts: () => fetchApi<Post[]>('/api/posts'),
  createPost: (title: string, body: string) => fetchApi<{ id: number; message: string }>('/api/posts', { method: 'POST', body: JSON.stringify({ title, body }) }),
  deletePost: (postId: number) => fetchApi(`/api/posts/${postId}`, { method: 'DELETE' }),
  createComment: (postId: number, body: string) => fetchApi<{ id: number; message: string }>('/api/comments', { method: 'POST', body: JSON.stringify({ post_id: postId, body }) }),
  deleteComment: (commentId: number) => fetchApi(`/api/comments/${commentId}`, { method: 'DELETE' }),
  toggleLike: (postId: number) => fetchApi<{ liked: boolean; message: string }>('/api/likes/toggle', { method: 'POST', body: JSON.stringify({ post_id: postId }) }),
};

export const circuitApi = {
  // Legacy endpoint (backward compatible)
  runCircuit: (gates: any[], numQubits: number, useNoise?: boolean) =>
    fetchApi<CircuitSimulationResult>('/api/circuit/run', {
      method: 'POST',
      body: JSON.stringify({
        circuit: gates,
        num_qubits: numQubits,
        use_noise: useNoise
      })
    }),
  applyQuantumGate: (state: any, gateName: string) =>
    fetchApi<any>('/api/quantum/state/apply', {
      method: 'POST',
      body: JSON.stringify({
        current_state: state,
        gate: gateName
      })
    }),

  // V1 Enterprise endpoints
  simulateV1: (payload: { num_qubits: number; shots: number; gates: { name: string; qubits: number[]; params: number[] }[]; use_noise: boolean }) =>
    fetchApi<any>('/api/v1/circuit/simulate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  exportQASM: (payload: { num_qubits: number; gates: { name: string; qubits: number[]; params: number[] }[] }) =>
    fetchApi<{ qasm: string; version: string; num_qubits: number; num_gates: number }>('/api/v1/circuit/export', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};

export const adminApi = {
  getUsers: (params?: any) => { 
    const qs = params ? '?' + new URLSearchParams(Object.entries(params).filter(([_, v]) => v !== undefined && v !== null) as any).toString() : '';
    return fetchApi<any>(`/admin/users${qs}`); 
  },
  getUser: (userId: number) => fetchApi<User>(`/admin/users/${userId}`),
  blockUser: (userId: number) => fetchApi(`/admin/users/${userId}/block`, { method: 'POST' }),
  unblockUser: (userId: number) => fetchApi(`/admin/users/${userId}/unblock`, { method: 'POST' }),
  setUserRole: (userId: number, role: string) => fetchApi(`/admin/users/${userId}/role?role=${role}`, { method: 'POST' }),
  getLogs: (params?: any) => { 
    const qs = params ? '?' + new URLSearchParams(Object.entries(params).filter(([_, v]) => v !== undefined && v !== null) as any).toString() : '';
    return fetchApi<any>(`/admin/logs${qs}`); 
  },
  getErrorLogs: (hours?: number, limit?: number) => { 
    const params: any = {};
    if (hours) params.hours = String(hours);
    if (limit) params.limit = String(limit);
    const qs = Object.keys(params).length ? '?' + new URLSearchParams(params).toString() : '';
    return fetchApi<any>(`/admin/logs/errors${qs}`); 
  },
  getMetrics: () => fetchApi('/admin/metrics'),
  getStats: () => fetchApi<SystemStats>('/admin/stats'),
};

export const healthApi = {
  check: () => fetchApi<{ status: string; timestamp: string; uptime_seconds: number; database: string; service: string }>('/health'),
  detailed: () => fetchApi('/health/detailed'),
};

export const api = { ...authApi, ...communityApi, ...circuitApi, ...adminApi, ...healthApi, ...contentApi, setToken, getAuthToken };
export default api;

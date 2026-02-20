/**
 * API Client for QuantCAI Backend
 */

const API_BASE = import.meta.env.VITE_API_URL || 'https://quantcai.onrender.com';

let authToken: string | null = null;

export const setToken = (token: string | null) => {
  authToken = token;
};

export const getAuthToken = () => authToken;

async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;

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
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export interface User { id: number; email: string; name: string; role: string; is_active: boolean; is_blocked: boolean; email_verified: boolean; created_at: string; updated_at: string; token_version: number; failed_login_attempts?: number; locked_until?: string | null; verification_sent_at?: string | null; }
export interface Post { id: number; title: string; body: string; author: any; comments: any[]; likes: any[]; created_at: string; }
export interface Comment { id: number; body: string; author: any; created_at: string; }
export interface TokenResponse { access_token: string; refresh_token?: string; token_type: string; }
export interface Circuit { id?: number; name: string; description?: string; num_wires: number; gates: any[]; created_at?: string; updated_at?: string; user_id?: number; }
export interface CircuitSimulationResult { state_vector: number[]; probabilities: number[]; measurements?: number[]; }
export interface SystemStats { users: number; posts: number; comments: number; likes: number; subscribers: number; circuits: number; refresh_tokens: number; email_verification_tokens: number; failed_login_users: number; locked_accounts: number; unverified_emails: number; }

export const authApi = {
  login: (email: string, password: string) => fetchApi<TokenResponse>('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  register: (email: string, password: string, name: string) => fetchApi<TokenResponse>('/api/auth/register', { method: 'POST', body: JSON.stringify({ email, password, name }) }),
  logout: () => fetchApi('/api/auth/logout', { method: 'POST' }),
  getMe: () => fetchApi<User>('/api/auth/me'),
  refresh: () => fetchApi<TokenResponse>('/api/auth/refresh', { method: 'POST' }),
  sendVerification: () => fetchApi('/api/auth/verify/send', { method: 'POST' }),
  resendVerification: (email: string) => fetchApi('/api/auth/verify/resend', { method: 'POST', body: JSON.stringify({ email }) }),
  verifyEmail: (token: string) => fetchApi('/api/auth/verify/confirm', { method: 'POST', body: JSON.stringify({ token }) }),
  getVerificationStatus: () => fetchApi<{ email_verified: boolean; verification_sent_at?: string }>('/api/auth/verify/status'),
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
  runCircuit: (circuit: Circuit, numWires: number, useNoise?: boolean) => fetchApi<CircuitSimulationResult>('/api/circuit/run', { method: 'POST', body: JSON.stringify({ circuit, num_wires: numWires, use_noise: useNoise }) }),
};

export const adminApi = {
  getUsers: (params?: any) => { const url = new URL('/admin/users', API_BASE); if (params) Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== null) url.searchParams.set(k, String(v)); }); return fetchApi<any>(url.toString()); },
  getUser: (userId: number) => fetchApi<User>(`/admin/users/${userId}`),
  blockUser: (userId: number) => fetchApi(`/admin/users/${userId}/block`, { method: 'POST' }),
  unblockUser: (userId: number) => fetchApi(`/admin/users/${userId}/unblock`, { method: 'POST' }),
  setUserRole: (userId: number, role: string) => fetchApi(`/admin/users/${userId}/role?role=${role}`, { method: 'POST' }),
  getLogs: (params?: any) => { const url = new URL('/admin/logs', API_BASE); if (params) Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== null) url.searchParams.set(k, String(v)); }); return fetchApi<any>(url.toString()); },
  getErrorLogs: (hours?: number, limit?: number) => { const url = new URL('/admin/logs/errors', API_BASE); if (hours) url.searchParams.set('hours', String(hours)); if (limit) url.searchParams.set('limit', String(limit)); return fetchApi<any>(url.toString()); },
  getMetrics: () => fetchApi('/admin/metrics'),
  getStats: () => fetchApi<SystemStats>('/admin/stats'),
};

export const healthApi = {
  check: () => fetchApi<{ status: string; timestamp: string; uptime_seconds: number; database: string; service: string }>('/health'),
  detailed: () => fetchApi('/health/detailed'),
};

export const api = { ...authApi, ...communityApi, ...circuitApi, ...adminApi, ...healthApi, setToken, getAuthToken };
export default api;

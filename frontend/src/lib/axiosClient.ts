import axios from 'axios';
import { toast } from 'sonner';
import { api } from '@/lib/api';

// Support VITE_API_URL as base URL
const API_URL = import.meta.env.VITE_API_URL || '';
const baseURL = API_URL.endsWith('/') ? API_URL.slice(0, -1) : API_URL;

export const axiosClient = axios.create({
  baseURL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT access token to request headers if it exists
axiosClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors globally
axiosClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response) {
      const { status } = error.response;
      const originalRequest = error.config as any;

      if (status === 401 && originalRequest && !originalRequest._retry) {
        // Prevent infinite loops if refreshing also returns 401
        const isRefreshUrl = originalRequest.url?.includes('/api/auth/refresh');
        if (!isRefreshUrl) {
          originalRequest._retry = true;
          try {
            const tokenData = await api.refresh();
            if (tokenData.access_token) {
              api.setToken(tokenData.access_token);
              if (originalRequest.headers) {
                originalRequest.headers['Authorization'] = `Bearer ${tokenData.access_token}`;
              }
              return axiosClient(originalRequest);
            }
          } catch (refreshErr) {
            console.error('Session expired during auto-refresh, clearing session.', refreshErr);
          }
        }
      }

      // If refresh failed, or it's a 401 on refresh/login itself, clear session
      if (status === 401) {
        const isAuthRequest = originalRequest?.url?.includes('/api/auth/refresh') || 
                              originalRequest?.url?.includes('/api/auth/login') ||
                              originalRequest?.url?.includes('/api/auth/register');
        
        // Don't redirect during payment operations — let the payment handler deal with it
        const isPaymentRequest = originalRequest?.url?.includes('/api/create-order') ||
                                 originalRequest?.url?.includes('/api/verify-payment');
        
        if (!isAuthRequest && !isPaymentRequest) {
          // Only remove auth-specific keys instead of wiping everything
          localStorage.removeItem('access_token');
          localStorage.removeItem('auth_user');
          localStorage.removeItem('subscription_plan');

          const publicPaths = ['/', '/login', '/signup', '/learn', '/quantum-computing', '/get-started', '/vision', '/tools', '/community'];
          const isPublicPage = publicPaths.some(p => window.location.pathname === p || window.location.pathname.startsWith('/learn'));
          
          if (!isPublicPage) {
            window.location.href = '/login';
          }
        }
      } else if (status === 429) {
        toast.error("Rate limit reached. Try again in 60 seconds.");
      } else if (status === 403) {
        // Locked features trigger the upgrade modal instead of standard error message
        window.dispatchEvent(new CustomEvent('show-upgrade-modal'));
      }
    }
    return Promise.reject(error);
  }
);

export default axiosClient;

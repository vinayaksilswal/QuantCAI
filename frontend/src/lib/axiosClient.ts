import axios from 'axios';
import { toast } from 'sonner';

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
  (error) => {
    if (error.response) {
      const { status } = error.response;
      if (status === 401) {
        // Token expired or invalid, clear localStorage and redirect to /login
        localStorage.clear();
        
        // Simple client-side redirect if not already on the login page
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login';
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

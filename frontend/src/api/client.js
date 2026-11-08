/**
 * Axios API client with JWT auth interceptor.
 */
import axios from 'axios';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 — redirect to login
client.interceptors.response.use(
  (response) => response,
  (error) => {
    // Xato xabarini doim o'qiladigan matnga keltiramiz
    const res = error.response;
    if (!res) {
      error.response = { data: { detail: 'Сервер билан алоқа йўқ. Backend ишлаётганини текширинг.' } };
    } else if (res.data && Array.isArray(res.data.detail)) {
      res.data.detail = res.data.detail.map((d) => (d.msg || '').replace(/^Value error, /, '')).join('; ');
    } else if (res.status >= 500) {
      res.data = { ...(typeof res.data === 'object' ? res.data : {}), detail: `Серверда хатолик (${res.status}). Backend ойнасидаги хабарни текширинг.` };
    }
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default client;

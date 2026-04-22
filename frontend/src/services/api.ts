import axios, { AxiosInstance } from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || '/api';

const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Añade el JWT a cada petición
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cd_access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Maneja 401: intenta refrescar el token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('cd_refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem('cd_access_token', data.access_token);
          if (data.refresh_token) {
            localStorage.setItem('cd_refresh_token', data.refresh_token);
          }
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          return api(originalRequest);
        } catch {
          localStorage.removeItem('cd_access_token');
          localStorage.removeItem('cd_refresh_token');
          window.location.href = '/login';
        }
      } else {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;

import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach Bearer token to outgoing requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('traffic_law_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Intercept 401 responses to automatically clear expired tokens
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('traffic_law_token');
      localStorage.removeItem('traffic_law_user');
      window.dispatchEvent(new Event('auth:unauthorized'));
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: async (username, password) => {
    const response = await api.post('/auth/login', { username, password });
    return response.data;
  },
  register: async (username, password) => {
    const response = await api.post('/auth/register', { username, password });
    return response.data;
  },
  logout: async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignore network errors on logout
    }
  },
  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

export const historyAPI = {
  getSessions: async () => {
    const response = await api.get('/sessions');
    return response.data;
  },
  createSession: async (title = 'Cuộc trò chuyện mới') => {
    const response = await api.post('/sessions', { title });
    return response.data;
  },
  getSession: async (sessionId) => {
    const response = await api.get(`/sessions/${sessionId}`);
    return response.data;
  },
  updateSession: async (sessionId, title) => {
    const response = await api.patch(`/sessions/${sessionId}`, { title });
    return response.data;
  },
  deleteSession: async (sessionId) => {
    const response = await api.delete(`/sessions/${sessionId}`);
    return response.data;
  },
};

export default api;

import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('traffic_law_user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState(() => localStorage.getItem('traffic_law_token'));
  const [loading, setLoading] = useState(true);

  // Check current session on initial load
  useEffect(() => {
    async function loadUser() {
      const savedToken = localStorage.getItem('traffic_law_token');
      if (savedToken) {
        try {
          const userData = await authAPI.getMe();
          setUser(userData);
          localStorage.setItem('traffic_law_user', JSON.stringify(userData));
          setToken(savedToken);
        } catch {
          // Token is invalid or expired
          localStorage.removeItem('traffic_law_token');
          localStorage.removeItem('traffic_law_user');
          setUser(null);
          setToken(null);
        }
      } else {
        localStorage.removeItem('traffic_law_user');
        setUser(null);
      }
      setLoading(false);
    }

    loadUser();

    // Listen for unauthorized events triggered by API interceptor
    const handleUnauthorized = () => {
      localStorage.removeItem('traffic_law_token');
      localStorage.removeItem('traffic_law_user');
      setUser(null);
      setToken(null);
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  const login = async (username, password) => {
    const data = await authAPI.login(username, password);
    const userInfo = data.user || {
      user_id: data.user_id,
      username: data.username,
      role: data.role,
    };
    localStorage.setItem('traffic_law_token', data.access_token);
    localStorage.setItem('traffic_law_user', JSON.stringify(userInfo));
    setToken(data.access_token);
    setUser(userInfo);
    return userInfo;
  };

  const register = async (username, password) => {
    const data = await authAPI.register(username, password);
    const userInfo = data.user || {
      user_id: data.user_id,
      username: data.username,
      role: data.role,
    };
    localStorage.setItem('traffic_law_token', data.access_token);
    localStorage.setItem('traffic_law_user', JSON.stringify(userInfo));
    setToken(data.access_token);
    setUser(userInfo);
    return userInfo;
  };

  const logout = async () => {
    await authAPI.logout();
    localStorage.removeItem('traffic_law_token');
    localStorage.removeItem('traffic_law_user');
    setUser(null);
    setToken(null);
  };

  const value = {
    user,
    token,
    isAuthenticated: !!user,
    loading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

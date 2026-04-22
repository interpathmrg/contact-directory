import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { TokenPayload, User } from '../types';
import { authService } from '../services/authService';

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function decodeToken(token: string): TokenPayload | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload as TokenPayload;
  } catch {
    return null;
  }
}

function tokenToUser(payload: TokenPayload): User {
  return {
    email: payload.sub,
    name: payload.name || payload.sub,
    role: payload.role,
    permissions: payload.permissions || {},
    is_admin: payload.role === 'ADMIN',
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('cd_access_token');
    if (!token) {
      setIsLoading(false);
      return;
    }
    const payload = decodeToken(token);
    if (!payload) {
      localStorage.removeItem('cd_access_token');
      setIsLoading(false);
      return;
    }
    // Token expirado
    if (payload.exp < Date.now() / 1000) {
      localStorage.removeItem('cd_access_token');
      setIsLoading(false);
      return;
    }
    setUser(tokenToUser(payload));
    setIsLoading(false);
  }, []);

  const login = useCallback(async () => {
    const { auth_url } = await authService.getLoginUrl();
    window.location.href = auth_url;
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider');
  return ctx;
}

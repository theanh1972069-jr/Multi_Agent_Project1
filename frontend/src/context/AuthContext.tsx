import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import {
  apiClient,
  getStoredToken,
  registerUnauthorizedHandler,
  setStoredToken,
} from '../api/client';
import type { User, UserLoginRequest, UserRegisterRequest } from '../types/api';

interface AuthContextValue {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (payload: UserLoginRequest) => Promise<User>;
  register: (payload: UserRegisterRequest) => Promise<User>;
  logout: () => void;
  refreshUser: () => Promise<User | null>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(() => Boolean(getStoredToken()));

  const logout = useCallback(() => {
    setStoredToken(null);
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    registerUnauthorizedHandler(logout);
    return () => registerUnauthorizedHandler(null);
  }, [logout]);

  const refreshUser = useCallback(async (): Promise<User | null> => {
    const activeToken = getStoredToken();
    if (!activeToken) {
      setUser(null);
      setLoading(false);
      return null;
    }
    try {
      const me = await apiClient.getMe();
      setUser(me);
      return me;
    } catch {
      setStoredToken(null);
      setToken(null);
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (token) {
      void refreshUser();
    } else {
      setLoading(false);
    }
  }, [token, refreshUser]);

  const login = useCallback(async (payload: UserLoginRequest): Promise<User> => {
    const res = await apiClient.login(payload);
    setStoredToken(res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    return res.user;
  }, []);

  const register = useCallback(async (payload: UserRegisterRequest): Promise<User> => {
    const res = await apiClient.register(payload);
    setStoredToken(res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    return res.user;
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      loading,
      login,
      register,
      logout,
      refreshUser,
    }),
    [user, token, loading, login, register, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return ctx;
}

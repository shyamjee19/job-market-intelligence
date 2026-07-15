import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import * as authClient from "../api/authClient";
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "../lib/tokenStorage";
import type { User } from "../types";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  loginWithTokens: (accessToken: string, refreshToken: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      return;
    }
    try {
      const current = await authClient.fetchCurrentUser();
      setUser(current);
    } catch {
      clearTokens();
      setUser(null);
    }
  }, []);

  useEffect(() => {
    refreshUser().finally(() => setIsLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function login(email: string, password: string) {
    const tokens = await authClient.login(email, password);
    setTokens(tokens.access_token, tokens.refresh_token);
    await refreshUser();
  }

  async function register(email: string, password: string, fullName?: string) {
    const tokens = await authClient.register(email, password, fullName);
    setTokens(tokens.access_token, tokens.refresh_token);
    await refreshUser();
  }

  async function loginWithTokens(accessToken: string, refreshToken: string) {
    setTokens(accessToken, refreshToken);
    await refreshUser();
  }

  async function logout() {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      await authClient.logout(refreshToken).catch(() => {});
    }
    clearTokens();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, loginWithTokens, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}

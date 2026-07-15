import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import * as authClient from "../api/authClient";
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "../lib/tokenStorage";
import type { RegisterPayload, User } from "../types";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
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
      // A transient network error, an aborted request (e.g. the browser
      // navigating away mid-flight), or a 5xx doesn't mean the token is
      // invalid - only httpClient's own 401-plus-failed-refresh path
      // (see apiRequest) is a real signal to clearTokens(). Clearing here
      // on any failure would log a user out just because a request didn't
      // complete in time.
      setUser(null);
    }
  }, []);

  useEffect(() => {
    refreshUser().finally(() => setIsLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function login(email: string, password: string, rememberMe = true) {
    const tokens = await authClient.login(email, password, rememberMe);
    setTokens(tokens.access_token, tokens.refresh_token);
    await refreshUser();
  }

  async function register(payload: RegisterPayload) {
    const tokens = await authClient.register(payload);
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

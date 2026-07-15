import type { Profile, TokenResponse, User } from "../types";
import { apiRequest, apiUrl } from "./httpClient";

export function register(email: string, password: string, fullName?: string): Promise<TokenResponse> {
  return apiRequest("/auth/register", {
    method: "POST",
    body: { email, password, full_name: fullName || undefined },
    auth: false,
  });
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return apiRequest("/auth/login", { method: "POST", body: { email, password }, auth: false });
}

export function logout(refreshToken: string): Promise<void> {
  return apiRequest("/auth/logout", {
    method: "POST",
    body: { refresh_token: refreshToken },
    auth: false,
    parseResponse: false,
  });
}

export function fetchCurrentUser(): Promise<User> {
  return apiRequest("/auth/me");
}

export function fetchCurrentUserProfile(): Promise<Profile> {
  return apiRequest("/auth/me/profile");
}

export function oauthAuthorizeUrl(provider: "google" | "github"): string {
  return apiUrl(`/auth/${provider}`);
}

export function exchangeOAuthCode(code: string): Promise<TokenResponse> {
  return apiRequest(`/auth/oauth/exchange?code=${encodeURIComponent(code)}`, { method: "POST", auth: false });
}

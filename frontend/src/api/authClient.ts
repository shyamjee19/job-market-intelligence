import type { Profile, RegisterPayload, TokenResponse, User } from "../types";
import { apiRequest, apiUrl } from "./httpClient";

export function register(payload: RegisterPayload): Promise<TokenResponse> {
  return apiRequest("/auth/register", { method: "POST", body: payload, auth: false });
}

export function login(email: string, password: string, rememberMe: boolean): Promise<TokenResponse> {
  return apiRequest("/auth/login", {
    method: "POST",
    body: { email, password, remember_me: rememberMe },
    auth: false,
  });
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

export function forgotPassword(email: string): Promise<{ detail: string }> {
  return apiRequest("/auth/forgot-password", { method: "POST", body: { email }, auth: false });
}

export function resetPassword(token: string, newPassword: string): Promise<{ detail: string }> {
  return apiRequest("/auth/reset-password", {
    method: "POST",
    body: { token, new_password: newPassword },
    auth: false,
  });
}

export function changePassword(currentPassword: string, newPassword: string): Promise<{ detail: string }> {
  return apiRequest("/auth/me/password", {
    method: "PATCH",
    body: { current_password: currentPassword, new_password: newPassword },
  });
}

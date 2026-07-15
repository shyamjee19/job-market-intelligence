import type { FavoriteCompany, JobAlert, JobAlertCreate, JobSummary, Profile, ProfileUpdate } from "../types";
import { apiRequest } from "./httpClient";

export function updateProfile(update: ProfileUpdate): Promise<Profile> {
  return apiRequest("/users/me/profile", { method: "PUT", body: update });
}

export async function uploadResume(file: File): Promise<{ resume_filename: string; resume_uploaded_at: string }> {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest("/users/me/resume", { method: "POST", formData });
}

export function fetchSavedJobs(): Promise<JobSummary[]> {
  return apiRequest("/users/me/saved-jobs");
}

export function saveJob(jobId: number): Promise<void> {
  return apiRequest(`/users/me/saved-jobs/${jobId}`, { method: "POST", parseResponse: false });
}

export function unsaveJob(jobId: number): Promise<void> {
  return apiRequest(`/users/me/saved-jobs/${jobId}`, { method: "DELETE", parseResponse: false });
}

export function fetchFavoriteCompanies(): Promise<FavoriteCompany[]> {
  return apiRequest("/users/me/favorites");
}

export function favoriteCompany(companyName: string): Promise<void> {
  return apiRequest(`/users/me/favorites/${encodeURIComponent(companyName)}`, { method: "POST", parseResponse: false });
}

export function unfavoriteCompany(companyName: string): Promise<void> {
  return apiRequest(`/users/me/favorites/${encodeURIComponent(companyName)}`, {
    method: "DELETE",
    parseResponse: false,
  });
}

export function fetchAlerts(): Promise<JobAlert[]> {
  return apiRequest("/users/me/alerts");
}

export function createAlert(alert: JobAlertCreate): Promise<JobAlert> {
  return apiRequest("/users/me/alerts", { method: "POST", body: alert });
}

export function deleteAlert(alertId: number): Promise<void> {
  return apiRequest(`/users/me/alerts/${alertId}`, { method: "DELETE", parseResponse: false });
}

export function toggleAlert(alertId: number, isActive: boolean): Promise<void> {
  return apiRequest(`/users/me/alerts/${alertId}?is_active=${isActive}`, { method: "PATCH", parseResponse: false });
}

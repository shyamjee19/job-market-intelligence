import type { AdminStats, AdminUserListResponse, AuditLogListResponse } from "../types";
import { apiRequest, buildQuery } from "./httpClient";

export function fetchAdminStats(): Promise<AdminStats> {
  return apiRequest("/admin/stats");
}

export function fetchAdminUsers(page = 1, pageSize = 50): Promise<AdminUserListResponse> {
  return apiRequest(`/admin/users${buildQuery({ page, page_size: pageSize })}`);
}

export function updateUserRole(userId: number, role: "user" | "admin"): Promise<void> {
  return apiRequest(`/admin/users/${userId}/role`, { method: "PATCH", body: { role }, parseResponse: false });
}

export function updateUserActive(userId: number, isActive: boolean): Promise<void> {
  return apiRequest(`/admin/users/${userId}/active?is_active=${isActive}`, {
    method: "PATCH",
    parseResponse: false,
  });
}

export function fetchAuditLogs(page = 1, pageSize = 50): Promise<AuditLogListResponse> {
  return apiRequest(`/admin/audit-logs${buildQuery({ page, page_size: pageSize })}`);
}

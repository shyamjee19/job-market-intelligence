import type {
  ChatResponse,
  CountByLabel,
  HiringTrend,
  JobDetail,
  JobFilters,
  JobListResponse,
  PostingsByDate,
  SalaryBucket,
  SummaryStats,
} from "../types";
import { apiRequest, apiUrl, buildQuery } from "./httpClient";

export function fetchJobs(filters: JobFilters): Promise<JobListResponse> {
  return apiRequest(`/jobs${buildQuery({ ...filters })}`, { auth: false });
}

export function fetchJob(jobId: number): Promise<JobDetail> {
  return apiRequest(`/jobs/${jobId}`, { auth: false });
}

export function fetchSummary(): Promise<SummaryStats> {
  return apiRequest(`/stats/summary`, { auth: false });
}

export function fetchTopCompanies(limit = 10): Promise<CountByLabel[]> {
  return apiRequest(`/stats/top-companies${buildQuery({ limit })}`, { auth: false });
}

export function fetchTopTags(limit = 15, category?: string): Promise<CountByLabel[]> {
  return apiRequest(`/stats/top-tags${buildQuery({ limit, category })}`, { auth: false });
}

export function fetchPostingsByDate(): Promise<PostingsByDate[]> {
  return apiRequest(`/stats/postings-by-date`, { auth: false });
}

export function fetchSalaryDistribution(): Promise<SalaryBucket[]> {
  return apiRequest(`/stats/salary-distribution`, { auth: false });
}

export function fetchSources(): Promise<CountByLabel[]> {
  return apiRequest(`/stats/sources`, { auth: false });
}

export function fetchHiringMap(): Promise<CountByLabel[]> {
  return apiRequest(`/stats/hiring-map`, { auth: false });
}

export function fetchTrend(): Promise<HiringTrend> {
  return apiRequest(`/stats/trend`, { auth: false });
}

export function jobsExportCsvUrl(filters: JobFilters): string {
  return `${apiUrl("/jobs/export.csv")}${buildQuery({ ...filters })}`;
}

export function sendChatMessage(message: string, conversationId?: string): Promise<ChatResponse> {
  return apiRequest(`/ai/chat`, { method: "POST", body: { message, conversation_id: conversationId }, auth: false });
}

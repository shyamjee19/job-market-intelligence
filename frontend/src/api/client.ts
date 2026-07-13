import type {
  CountByLabel,
  HiringTrend,
  JobDetail,
  JobFilters,
  JobListResponse,
  PostingsByDate,
  SalaryBucket,
  SummaryStats,
} from "../types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Request to ${path} failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function fetchJobs(filters: JobFilters): Promise<JobListResponse> {
  return request(`/api/jobs${buildQuery({ ...filters })}`);
}

export function fetchJob(jobId: number): Promise<JobDetail> {
  return request(`/api/jobs/${jobId}`);
}

export function fetchSummary(): Promise<SummaryStats> {
  return request(`/api/stats/summary`);
}

export function fetchTopCompanies(limit = 10): Promise<CountByLabel[]> {
  return request(`/api/stats/top-companies${buildQuery({ limit })}`);
}

export function fetchTopTags(limit = 15, category?: string): Promise<CountByLabel[]> {
  return request(`/api/stats/top-tags${buildQuery({ limit, category })}`);
}

export function fetchPostingsByDate(): Promise<PostingsByDate[]> {
  return request(`/api/stats/postings-by-date`);
}

export function fetchSalaryDistribution(): Promise<SalaryBucket[]> {
  return request(`/api/stats/salary-distribution`);
}

export function fetchSources(): Promise<CountByLabel[]> {
  return request(`/api/stats/sources`);
}

export function fetchHiringMap(): Promise<CountByLabel[]> {
  return request(`/api/stats/hiring-map`);
}

export function fetchTrend(): Promise<HiringTrend> {
  return request(`/api/stats/trend`);
}

export function jobsExportCsvUrl(filters: JobFilters): string {
  return `${API_URL}/api/jobs/export.csv${buildQuery({ ...filters })}`;
}

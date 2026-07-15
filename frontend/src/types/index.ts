export interface JobSummary {
  id: number;
  source: string;
  external_id: string;
  company: string | null;
  position: string | null;
  location: string | null;
  remote_type: string | null;
  salary_min: number | null;
  salary_max: number | null;
  date_posted: string | null;
  tags: string[];
  job_url: string | null;
  apply_url: string | null;
}

export interface JobDetail extends JobSummary {
  description: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface JobListResponse {
  items: JobSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface SummaryStats {
  total_jobs: number;
  today_jobs: number;
  remote_jobs: number;
  hybrid_jobs: number;
  onsite_jobs: number;
  total_companies: number;
  total_locations: number;
  avg_salary_min: number | null;
  avg_salary_max: number | null;
  highest_salary: number | null;
}

export interface HiringTrend {
  today_count: number;
  yesterday_count: number;
  pct_change: number | null;
}

export interface CountByLabel {
  label: string;
  count: number;
}

export interface PostingsByDate {
  date: string;
  count: number;
}

export interface SalaryBucket {
  bucket_start: number;
  bucket_end: number;
  count: number;
}

export interface JobFilters {
  search?: string;
  company?: string;
  location?: string;
  tag?: string;
  source?: string;
  salary_min?: number;
  page?: number;
  page_size?: number;
}

export interface ChatSource {
  job_id: string;
  position: string | null;
  company: string | null;
  score: number;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
  conversation_id: string;
  prompt_tokens: number | null;
  completion_tokens: number | null;
}

export interface User {
  user_id: number;
  email: string;
  full_name: string | null;
  role: "user" | "admin";
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Profile {
  headline: string | null;
  bio: string | null;
  location: string | null;
  skills: string[];
  experience_years: number | null;
  resume_filename: string | null;
  resume_uploaded_at: string | null;
}

export interface ProfileUpdate {
  headline?: string | null;
  bio?: string | null;
  location?: string | null;
  skills?: string[] | null;
  experience_years?: number | null;
}

export interface FavoriteCompany {
  company_key: number;
  company_name: string;
  favorited_at: string;
}

export interface JobAlert {
  alert_id: number;
  name: string;
  keywords: string | null;
  location: string | null;
  tag: string | null;
  source: string | null;
  salary_min: number | null;
  remote_type: string | null;
  frequency: "instant" | "daily" | "weekly";
  is_active: boolean;
  last_checked_at: string | null;
  created_at: string;
}

export interface JobAlertCreate {
  name: string;
  keywords?: string;
  location?: string;
  tag?: string;
  source?: string;
  salary_min?: number;
  remote_type?: string;
  frequency: "instant" | "daily" | "weekly";
}

export interface AdminUser {
  user_id: number;
  email: string;
  full_name: string | null;
  role: "user" | "admin";
  google_id: string | null;
  github_id: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AdminUserListResponse {
  items: AdminUser[];
  total: number;
  page: number;
  page_size: number;
}

export interface AuditLog {
  log_id: number;
  user_id: number | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  metadata: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLog[];
  total: number;
  page: number;
  page_size: number;
}

export interface AdminStats {
  total_users: number;
  admin_users: number;
  new_users_today: number;
  active_users: number;
}

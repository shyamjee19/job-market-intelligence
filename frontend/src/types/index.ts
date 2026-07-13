export interface JobSummary {
  job_id: number;
  company: string | null;
  position: string | null;
  location: string | null;
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
  total_companies: number;
  total_locations: number;
  avg_salary_min: number | null;
  avg_salary_max: number | null;
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
  salary_min?: number;
  page?: number;
  page_size?: number;
}

/**
 * CareerOS API client — Phase 4 Jobs.
 *
 * Thin fetch wrapper that talks to the real FastAPI backend.
 * Token is read from localStorage (set by the auth flow).
 */

export interface JobSummary {
  id: string;
  source: string;
  source_url: string | null;
  title: string;
  company_name: string;
  company_url: string | null;
  city: string | null;
  province: string | null;
  country: string;
  is_remote: boolean;
  is_pakistan_eligible: boolean;
  employment_type: string | null;
  workplace_type: string | null;
  category: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  salary_period: string | null;
  experience_min: number | null;
  experience_max: number | null;
  posted_at: string | null;
  closing_at: string | null;
  status: string;
  is_active: boolean;
}

export interface JobDetail extends JobSummary {
  description: string | null;
  requirements: string | null;
  responsibilities: string | null;
  skills: string | null;
  department: string | null;
  location: string | null;
  education_requirements: string | null;
  discovered_at: string;
  last_seen_at: string;
  eligibility: string | null;
}

export interface JobListResponse {
  items: JobSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface SavedJob {
  id: string;
  job: JobSummary;
  saved_at: string;
  notes: string | null;
}

export interface JobPreferences {
  target_roles: string[];
  preferred_cities: string[];
  preferred_provinces: string[];
  remote_preference: string | null;
  employment_types: string[];
  experience_level: string | null;
  min_salary: number | null;
  salary_currency: string | null;
  sector_preference: string | null;
  selected_industries: string[];
}

export interface SourceSummary {
  id: string;
  name: string;
  category: string;
  source_type: string;
  integration_method: string;
  country: string;
  enabled: boolean;
  is_active: boolean;
  last_run_at: string | null;
  last_success_at: string | null;
  last_failure_at: string | null;
  consecutive_failures: number;
  total_jobs_discovered: number;
  last_error: string | null;
}

export interface SourceHealthEntry {
  source_id: string;
  source_name: string;
  last_run_at: string | null;
  last_success_at: string | null;
  last_failure_at: string | null;
  consecutive_failures: number;
  total_jobs_discovered: number;
  last_error: string | null;
  status: string;
  enabled: boolean;
}

export interface DiscoveryRunSummary {
  id: string;
  source_id: string | null;
  started_at: string;
  completed_at: string | null;
  status: string;
  jobs_found: number;
  jobs_created: number;
  jobs_updated: number;
  jobs_skipped: number;
  jobs_expired: number;
  error_count: number;
  error_message: string | null;
  duration_ms: number | null;
}

const API_BASE = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000/api/v1";

function getToken(): string | null {
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem("careeros_token");
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  if (res.status === 204) return undefined as unknown as T;
  return (await res.json()) as T;
}

export const JobsApi = {
  list(params: Record<string, string | number | boolean | undefined> = {}) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v === undefined || v === null || v === "") continue;
      qs.set(k, String(v));
    }
    return request<JobListResponse>(`/jobs?${qs.toString()}`);
  },
  get(jobId: string) {
    return request<JobDetail>(`/jobs/${jobId}`);
  },
  save(jobId: string, notes?: string) {
    return request<SavedJob>(`/jobs/${jobId}/save`, {
      method: "POST",
      body: JSON.stringify(notes ? { notes } : {}),
    });
  },
  unsave(jobId: string) {
    return request<void>(`/jobs/${jobId}/save`, { method: "DELETE" });
  },
  saved() {
    return request<SavedJob[]>(`/jobs/saved`);
  },
  sources() {
    return request<SourceSummary[]>(`/sources`);
  },
  sourceHealth() {
    return request<{ sources: SourceHealthEntry[] }>(`/sources/health`);
  },
  discoveryRuns(params: { page?: number; page_size?: number; source_id?: string; status?: string } = {}) {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== '') qs.set(key, String(value));
    });
    return request<{ items: DiscoveryRunSummary[]; total: number; page: number; page_size: number }>(`/jobs/discovery/runs?${qs.toString()}`);
  },
  getPreferences() {
    return request<JobPreferences>(`/job-preferences`);
  },
  updatePreferences(prefs: Partial<JobPreferences>) {
    return request<JobPreferences>(`/job-preferences`, {
      method: "PUT",
      body: JSON.stringify(prefs),
    });
  },
  triggerDiscovery() {
    return request<{
      sources_attempted: number;
      sources_succeeded: number;
      sources_failed: number;
      jobs_found: number;
      jobs_created: number;
      jobs_updated: number;
      jobs_skipped: number;
      jobs_expired: number;
      error_count: number;
    }>(`/jobs/_discovery/run`, { method: "POST" });
  },
};

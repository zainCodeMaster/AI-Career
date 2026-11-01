/**
 * CareerOS API client — Phase 4 Jobs.
 *
 * Uses the centralized API client (src/api/client.ts) for consistent
 * token handling, auto-refresh, and error handling.
 */

import { apiClient } from './client';

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
  eligibility: 'eligible' | 'ineligible' | 'unknown' | null;
  eligibility_reason: string | null;
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

export const JobsApi = {
  list(params: Record<string, string | number | boolean | undefined> = {}) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v === undefined || v === null || v === "") continue;
      qs.set(k, String(v));
    }
    return apiClient.get<JobListResponse>(`/jobs?${qs.toString()}`);
  },
  get(jobId: string) {
    return apiClient.get<JobDetail>(`/jobs/${jobId}`);
  },
  save(jobId: string, notes?: string) {
    return apiClient.post<SavedJob, { notes?: string }>(`/jobs/${jobId}/save`, notes ? { notes } : {});
  },
  unsave(jobId: string) {
    return apiClient.delete<void>(`/jobs/${jobId}/save`);
  },
  saved() {
    return apiClient.get<SavedJob[]>(`/jobs/saved`);
  },
  sources() {
    return apiClient.get<SourceSummary[]>(`/sources`);
  },
  sourceHealth() {
    return apiClient.get<{ sources: SourceHealthEntry[] }>(`/sources/health`);
  },
  discoveryRuns(params: { page?: number; page_size?: number; source_id?: string; status?: string } = {}) {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== '') qs.set(key, String(value));
    });
    return apiClient.get<{ items: DiscoveryRunSummary[]; total: number; page: number; page_size: number }>(`/jobs/discovery/runs?${qs.toString()}`);
  },
  getPreferences() {
    return apiClient.get<JobPreferences>(`/job-preferences`);
  },
  updatePreferences(prefs: Partial<JobPreferences>) {
    return apiClient.put<JobPreferences, Partial<JobPreferences>>(`/job-preferences`, prefs);
  },
  triggerDiscovery() {
    return apiClient.post<{
      sources_attempted: number;
      sources_succeeded: number;
      sources_failed: number;
      jobs_found: number;
      jobs_created: number;
      jobs_updated: number;
      jobs_skipped: number;
      jobs_expired: number;
      error_count: number;
    }, {}>(`/jobs/_discovery/run`, {});
  },
};

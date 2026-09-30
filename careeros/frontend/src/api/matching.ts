import type { JobSummary } from './jobs';

export interface MatchBreakdown {
  skills: number;
  experience: number;
  education: number;
  location: number;
  preferences: number;
  semantic: number;
  role_title: number;
}

export interface JobMatch {
  job_id: string;
  overall_score: number;
  breakdown: MatchBreakdown;
  matched_skills: string[];
  missing_skills: string[];
  matched_requirements: string[];
  missing_requirements: string[];
  qualification_match: boolean;
  experience_match: boolean;
  location_match: boolean;
  explanation: string[];
  profile_completeness: string;
  generated_at: string;
}

export interface MatchFeedItem {
  match: JobMatch;
  job: JobSummary;
}

export interface MatchFeedResponse {
  items: MatchFeedItem[];
  total: number;
  page: number;
  page_size: number;
  profile_completeness: string;
}

const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000/api/v1';

async function request<T>(path: string): Promise<T> {
  const token = localStorage.getItem('careeros_token');
  const response = await fetch(`${API_BASE}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) throw new Error(`API ${response.status}: ${await response.text()}`);
  return (await response.json()) as T;
}

export const MatchingApi = {
  list(params: { page?: number; page_size?: number; min_score?: number } = {}) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) query.set(key, String(value));
    });
    return request<MatchFeedResponse>(`/jobs/matches?${query.toString()}`);
  },
  detail(jobId: string) {
    return request<JobMatch>(`/jobs/${encodeURIComponent(jobId)}/match`);
  },
};

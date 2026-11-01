import type { JobSummary } from './jobs';
import { apiClient } from './client';

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

export const MatchingApi = {
  list(params: { page?: number; page_size?: number; min_score?: number } = {}) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) query.set(key, String(value));
    });
    return apiClient.get<MatchFeedResponse>(`/jobs/matches?${query.toString()}`);
  },
  detail(jobId: string) {
    return apiClient.get<JobMatch>(`/jobs/${encodeURIComponent(jobId)}/match`);
  },
};

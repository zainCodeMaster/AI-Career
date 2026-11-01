/**
 * CareerOS API client — Phase 6 Resume Engine.
 *
 * Uses the centralized API client (src/api/client.ts) for consistent
 * token handling, auto-refresh, and error handling.
 */

import { apiClient } from './client';

export interface ResumeSummary {
  id: string;
  user_id: string;
  name: string;
  resume_type: string;
  status: string;
  target_job_id: string | null;
  version_number: number;
  is_base_resume: boolean;
  is_tailored: boolean;
  is_imported: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResumeSection {
  id: string;
  resume_id: string;
  section_type: string;
  section_title: string | null;
  content: string;
  display_order: number;
  is_custom: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResumeDetail extends ResumeSummary {
  structured_data: Record<string, any> | null;
  source_file_name: string | null;
  source_file_type: string | null;
  import_metadata: Record<string, any> | null;
  ats_score: number | null;
  ats_breakdown: Record<string, any> | null;
  ats_analyzed_at: string | null;
  ats_analyzed_for_job_id: string | null;
  is_draft: boolean;
  is_ready: boolean;
  is_archived: boolean;
  target_job: {
    id: string;
    title: string;
    company_name: string;
    location: string | null;
  } | null;
  parent_resume: ResumeSummary | null;
  versions: ResumeSummary[];
  sections: ResumeSection[];
}

export interface ResumeListResponse {
  items: ResumeDetail[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ATSSectionScore {
  section_type: string;
  score: number;
  matched_count: number;
  total_count: number;
  matched_items: string[];
  missing_items: string[];
}

export interface ATSAnalysisResponse {
  resume_id: string;
  job_id: string;
  overall_score: number;
  breakdown: Record<string, number>;
  keyword_coverage: ATSSectionScore;
  skill_alignment: ATSSectionScore;
  experience_alignment: ATSSectionScore;
  education_alignment: ATSSectionScore;
  certification_alignment: ATSSectionScore;
  structure_score: ATSSectionScore;
  relevance_score: ATSSectionScore;
  matched_keywords: string[];
  missing_keywords: string[];
  matched_skills: string[];
  missing_skills: string[];
  matched_requirements: string[];
  missing_requirements: string[];
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  analyzed_at: string;
  total_keywords_matched: number;
  total_keywords_required: number;
}

export interface TailorResponse {
  tailored_resume_id: string;
  base_resume_id: string;
  target_job_id: string;
  tailoring_changes: Record<string, any>;
  ats_analysis: ATSAnalysisResponse;
  matched_requirements: string[];
  missing_requirements: string[];
  recommendations: string[];
  created_at: string;
}

export const ResumesApi = {
  list(params: Record<string, string | number | boolean | undefined> = {}) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v === undefined || v === null || v === "") continue;
      qs.set(k, String(v));
    }
    return apiClient.get<ResumeListResponse>(`/resumes?${qs.toString()}`);
  },

  get(resumeId: string) {
    return apiClient.get<ResumeDetail>(`/resumes/${resumeId}`);
  },

  async exportText(resumeId: string) {
    const token = apiClient.getAccessToken();
    const res = await fetch(`${apiClient['config'].baseUrl}/resumes/${resumeId}/export`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return res.blob();
  },

  create(data: { name: string; resume_type?: string; target_job_id?: string }) {
    return apiClient.post<ResumeDetail, { name: string; resume_type?: string; target_job_id?: string }>(`/resumes`, data);
  },

  update(resumeId: string, data: Partial<{ name: string; status: string; structured_data: Record<string, any> }>) {
    return apiClient.put<ResumeDetail, Partial<{ name: string; status: string; structured_data: Record<string, any> }>>(`/resumes/${resumeId}`, data);
  },

  delete(resumeId: string) {
    return apiClient.delete<void>(`/resumes/${resumeId}`);
  },

  buildFromProfile(name: string) {
    return apiClient.post<ResumeDetail, { name: string }>(`/resumes/build-from-profile?name=${encodeURIComponent(name)}`, { name });
  },

  importText(resumeId: string, resumeText: string) {
    return apiClient.post<ResumeDetail, { resume_text: string }>(`/resumes/${resumeId}/import/text`, { resume_text: resumeText });
  },

  importFile(resumeId: string, file: File) {
    return apiClient.uploadFile<ResumeDetail>(`/resumes/${resumeId}/import/file`, file, 'file');
  },

  listSections(resumeId: string) {
    return apiClient.get<ResumeSection[]>(`/resumes/${resumeId}/sections`);
  },

  createSection(resumeId: string, section: Partial<ResumeSection>) {
    return apiClient.post<ResumeSection, Partial<ResumeSection>>(`/resumes/${resumeId}/sections`, section);
  },

  updateSection(sectionId: string, section: Partial<ResumeSection>) {
    return apiClient.put<ResumeSection, Partial<ResumeSection>>(`/resumes/sections/${sectionId}`, section);
  },

  deleteSection(sectionId: string) {
    return apiClient.delete<void>(`/resumes/sections/${sectionId}`);
  },

  listVersions(resumeId: string) {
    return apiClient.get<ResumeSummary[]>(`/resumes/${resumeId}/versions`);
  },

  analyzeATS(data: { resume_id: string; job_id: string }) {
    return apiClient.post<ATSAnalysisResponse, { resume_id: string; job_id: string }>(`/resumes/ats/analyze`, data);
  },

  tailor(data: { base_resume_id: string; target_job_id: string; name: string }) {
    return apiClient.post<TailorResponse, { base_resume_id: string; target_job_id: string; name: string }>(`/resumes/tailor`, data);
  },
};

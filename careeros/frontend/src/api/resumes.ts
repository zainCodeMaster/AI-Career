/**
 * CareerOS API client — Phase 6 Resume Engine.
 *
 * Thin fetch wrapper that talks to the real FastAPI backend.
 * Token is read from localStorage (set by the auth flow).
 */

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

async function uploadFile<T>(path: string, file: File): Promise<T> {
  const token = getToken();
  const body = new FormData();
  body.append("file", file);
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    body,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return (await res.json()) as T;
}

export const ResumesApi = {
  list(params: Record<string, string | number | boolean | undefined> = {}) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v === undefined || v === null || v === "") continue;
      qs.set(k, String(v));
    }
    return request<ResumeListResponse>(`/resumes?${qs.toString()}`);
  },

  get(resumeId: string) {
    return request<ResumeDetail>(`/resumes/${resumeId}`);
  },

  async exportText(resumeId: string) {
    const token = getToken();
    const res = await fetch(`${API_BASE}/resumes/${resumeId}/export`, {
      headers: token ? { Authorization: "Bearer " + token } : {},
    });
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return res.blob();
  },

  create(data: { name: string; resume_type?: string; target_job_id?: string }) {
    return request<ResumeDetail>(`/resumes`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  update(resumeId: string, data: Partial<{ name: string; status: string; structured_data: Record<string, any> }>) {
    return request<ResumeDetail>(`/resumes/${resumeId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  delete(resumeId: string) {
    return request<void>(`/resumes/${resumeId}`, { method: "DELETE" });
  },

  buildFromProfile(name: string) {
    return request<ResumeDetail>(`/resumes/build-from-profile?name=${encodeURIComponent(name)}`, {
      method: "POST",
    });
  },

  importText(resumeId: string, resumeText: string) {
    return request<ResumeDetail>(`/resumes/${resumeId}/import/text`, {
      method: "POST",
      body: JSON.stringify({ resume_text: resumeText }),
    });
  },

  importFile(resumeId: string, file: File) {
    return uploadFile<ResumeDetail>(`/resumes/${resumeId}/import/file`, file);
  },

  listSections(resumeId: string) {
    return request<ResumeSection[]>(`/resumes/${resumeId}/sections`);
  },

  createSection(resumeId: string, section: Partial<ResumeSection>) {
    return request<ResumeSection>(`/resumes/${resumeId}/sections`, {
      method: "POST",
      body: JSON.stringify(section),
    });
  },

  updateSection(sectionId: string, section: Partial<ResumeSection>) {
    return request<ResumeSection>(`/resumes/sections/${sectionId}`, {
      method: "PUT",
      body: JSON.stringify(section),
    });
  },

  deleteSection(sectionId: string) {
    return request<void>(`/resumes/sections/${sectionId}`, { method: "DELETE" });
  },

  listVersions(resumeId: string) {
    return request<ResumeSummary[]>(`/resumes/${resumeId}/versions`);
  },

  analyzeATS(data: { resume_id: string; job_id: string }) {
    return request<ATSAnalysisResponse>(`/resumes/ats/analyze`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  tailor(data: { base_resume_id: string; target_job_id: string; name: string }) {
    return request<TailorResponse>(`/resumes/tailor`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
};

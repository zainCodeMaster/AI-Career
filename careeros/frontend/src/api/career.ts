export interface CareerRecord {
  id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface Skill extends CareerRecord {
  name: string;
  category: string | null;
  proficiency: string | null;
  years_of_experience: number | null;
}

export interface Education extends CareerRecord {
  institution: string;
  degree: string | null;
  field_of_study: string | null;
  start_date: string | null;
  end_date: string | null;
  grade: string | null;
  description: string | null;
}

export interface WorkExperience extends CareerRecord {
  company: string;
  job_title: string;
  location: string | null;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  description: string | null;
}

export interface Certification extends CareerRecord {
  name: string;
  issuing_organization: string | null;
  issue_date: string | null;
  expiry_date: string | null;
  credential_id: string | null;
  credential_url: string | null;
  description: string | null;
}

const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000/api/v1';

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('careeros_token');
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers || {}),
    },
  });
  if (!response.ok) throw new Error(`API ${response.status}: ${await response.text()}`);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

function jsonBody<T extends object>(data: T): RequestInit {
  return { method: 'POST', body: JSON.stringify(data) };
}

export const CareerApi = {
  listSkills: () => request<Skill[]>('/skills'),
  createSkill: (data: Omit<Skill, keyof CareerRecord>) => request<Skill>('/skills', jsonBody(data)),
  updateSkill: (id: string, data: Partial<Omit<Skill, keyof CareerRecord>>) => request<Skill>(`/skills/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteSkill: (id: string) => request<void>(`/skills/${id}`, { method: 'DELETE' }),

  listEducation: () => request<Education[]>('/education'),
  createEducation: (data: Omit<Education, keyof CareerRecord>) => request<Education>('/education', jsonBody(data)),
  updateEducation: (id: string, data: Partial<Omit<Education, keyof CareerRecord>>) => request<Education>(`/education/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteEducation: (id: string) => request<void>(`/education/${id}`, { method: 'DELETE' }),

  listExperience: () => request<WorkExperience[]>('/experience'),
  createExperience: (data: Omit<WorkExperience, keyof CareerRecord>) => request<WorkExperience>('/experience', jsonBody(data)),
  updateExperience: (id: string, data: Partial<Omit<WorkExperience, keyof CareerRecord>>) => request<WorkExperience>(`/experience/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteExperience: (id: string) => request<void>(`/experience/${id}`, { method: 'DELETE' }),

  listCertifications: () => request<Certification[]>('/certifications'),
  createCertification: (data: Omit<Certification, keyof CareerRecord>) => request<Certification>('/certifications', jsonBody(data)),
  updateCertification: (id: string, data: Partial<Omit<Certification, keyof CareerRecord>>) => request<Certification>(`/certifications/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCertification: (id: string) => request<void>(`/certifications/${id}`, { method: 'DELETE' }),
};

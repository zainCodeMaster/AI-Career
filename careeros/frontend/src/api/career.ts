import { apiClient } from './client';

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

export const CareerApi = {
  listSkills: () => apiClient.get<Skill[]>('/skills'),
  createSkill: (data: Omit<Skill, keyof CareerRecord>) => apiClient.post<Skill, Omit<Skill, keyof CareerRecord>>('/skills', data),
  updateSkill: (id: string, data: Partial<Omit<Skill, keyof CareerRecord>>) => apiClient.put<Skill, Partial<Omit<Skill, keyof CareerRecord>>>(`/skills/${id}`, data),
  deleteSkill: (id: string) => apiClient.delete<void>(`/skills/${id}`),

  listEducation: () => apiClient.get<Education[]>('/education'),
  createEducation: (data: Omit<Education, keyof CareerRecord>) => apiClient.post<Education, Omit<Education, keyof CareerRecord>>('/education', data),
  updateEducation: (id: string, data: Partial<Omit<Education, keyof CareerRecord>>) => apiClient.put<Education, Partial<Omit<Education, keyof CareerRecord>>>(`/education/${id}`, data),
  deleteEducation: (id: string) => apiClient.delete<void>(`/education/${id}`),

  listExperience: () => apiClient.get<WorkExperience[]>('/experience'),
  createExperience: (data: Omit<WorkExperience, keyof CareerRecord>) => apiClient.post<WorkExperience, Omit<WorkExperience, keyof CareerRecord>>('/experience', data),
  updateExperience: (id: string, data: Partial<Omit<WorkExperience, keyof CareerRecord>>) => apiClient.put<WorkExperience, Partial<Omit<WorkExperience, keyof CareerRecord>>>(`/experience/${id}`, data),
  deleteExperience: (id: string) => apiClient.delete<void>(`/experience/${id}`),

  listCertifications: () => apiClient.get<Certification[]>('/certifications'),
  createCertification: (data: Omit<Certification, keyof CareerRecord>) => apiClient.post<Certification, Omit<Certification, keyof CareerRecord>>('/certifications', data),
  updateCertification: (id: string, data: Partial<Omit<Certification, keyof CareerRecord>>) => apiClient.put<Certification, Partial<Omit<Certification, keyof CareerRecord>>>(`/certifications/${id}`, data),
  deleteCertification: (id: string) => apiClient.delete<void>(`/certifications/${id}`),
};

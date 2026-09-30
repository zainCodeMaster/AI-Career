export interface CareerProfileResponse {
  id: string;
  user_id: string;
  professional_title: string | null;
  summary: string | null;
  phone: string | null;
  location: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
  years_of_experience: number | null;
  preferred_job_title: string | null;
  preferred_location: string | null;
  remote_preference: string | null;
  created_at: string;
  updated_at: string;
}

export interface CareerProfileCreate {
  professional_title: string | null;
  summary: string | null;
  phone: string | null;
  location: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
  years_of_experience: number | null;
  preferred_job_title: string | null;
  preferred_location: string | null;
  remote_preference: string | null;
}

export type CareerProfileUpdate = CareerProfileCreate;

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000/api/v1';

function getToken(): string | null {
  if (typeof localStorage === 'undefined') return null;
  return localStorage.getItem('careeros_token');
}

function getErrorDetail(text: string, status: number): string {
  try {
    const payload = JSON.parse(text) as { detail?: unknown };
    if (typeof payload.detail === 'string' && payload.detail) {
      return payload.detail;
    }
    if (Array.isArray(payload.detail)) {
      return 'Please correct the highlighted fields.';
    }
  } catch {
    return text || `Request failed with status ${status}.`;
  }
  return `Request failed with status ${status}.`;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string> | undefined),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    throw new ApiError(getErrorDetail(await response.text(), response.status), response.status);
  }
  if (response.status === 204) return undefined as unknown as T;
  return (await response.json()) as T;
}

export const ProfileApi = {
  getProfile() {
    return request<CareerProfileResponse>('/profile');
  },

  createProfile(profileData: CareerProfileCreate) {
    return request<CareerProfileResponse>('/profile', {
      method: 'POST',
      body: JSON.stringify(profileData),
    });
  },

  updateProfile(profileData: CareerProfileUpdate) {
    return request<CareerProfileResponse>('/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  },
};

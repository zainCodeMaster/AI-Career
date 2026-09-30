export interface UserResponse {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

interface UserCreate {
  email: string;
  full_name: string;
  password: string;
}

interface UserLogin {
  email: string;
  password: string;
}

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

function removeToken(): void {
  if (typeof localStorage !== 'undefined') {
    localStorage.removeItem('careeros_token');
  }
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

export const AuthApi = {
  register(userData: UserCreate) {
    return request<UserResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },

  login(credentials: UserLogin) {
    return request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },

  me() {
    return request<UserResponse>('/auth/me');
  },

  async logout() {
    await request<void>('/auth/logout', { method: 'POST' });
    removeToken();
  },
};

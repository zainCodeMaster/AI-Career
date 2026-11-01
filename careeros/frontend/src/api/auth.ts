export interface UserResponse {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
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

import { apiClient } from './client';

export const AuthApi = {
  register(userData: UserCreate) {
    return apiClient.post<UserResponse, UserCreate>('/auth/register', userData, { skipAuth: true });
  },

  login(credentials: UserLogin) {
    return apiClient.post<TokenResponse, UserLogin>('/auth/login', credentials, { skipAuth: true });
  },

  me() {
    return apiClient.get<UserResponse>('/auth/me');
  },

  async logout() {
    try {
      await apiClient.request<void>('/auth/logout', { method: 'POST' }, { skipAuth: false });
    } finally {
      apiClient.logout();
    }
  },
};

/**
 * CareerOS Centralized API Client
 *
 * Provides a single, consistent fetch wrapper for all frontend API calls.
 * Handles:
 * - Base URL configuration from VITE_API_URL env var
 * - Bearer token injection from localStorage
 * - Auto-refresh on 401 (uses refresh token)
 * - Standardized error handling
 * - Request/response tracking
 */

export interface ApiClientConfig {
  baseUrl: string;
  accessTokenKey: string;
  refreshTokenKey: string;
}

const DEFAULT_CONFIG: ApiClientConfig = {
  baseUrl: (import.meta as any).env?.VITE_API_URL || '',
  accessTokenKey: 'careeros_access_token',
  refreshTokenKey: 'careeros_refresh_token',
};

export class ApiClient {
  private config: ApiClientConfig;
  private refreshing: Promise<string | null> | null = null;
  private onTokenChange: ((token: string | null) => void)[] = [];

  constructor(config: Partial<ApiClientConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /** Register a callback fired whenever the access token changes */
  onTokenChanged(callback: (token: string | null) => void) {
    this.onTokenChange.push(callback);
  }

  private notifyTokenChange(token: string | null) {
    for (const cb of this.onTokenChange) cb(token);
  }

  private getToken(): string | null {
    if (typeof localStorage === 'undefined') return null;
    return localStorage.getItem(this.config.accessTokenKey);
  }

  private setToken(token: string | null) {
    if (typeof localStorage === 'undefined') return;
    if (token) {
      localStorage.setItem(this.config.accessTokenKey, token);
    } else {
      localStorage.removeItem(this.config.accessTokenKey);
    }
    this.notifyTokenChange(token);
  }

  private getRefreshToken(): string | null {
    if (typeof localStorage === 'undefined') return null;
    return localStorage.getItem(this.config.refreshTokenKey);
  }

  private setRefreshToken(token: string | null) {
    if (typeof localStorage === 'undefined') return;
    if (token) {
      localStorage.setItem(this.config.refreshTokenKey, token);
    } else {
      localStorage.removeItem(this.config.refreshTokenKey);
    }
  }

  private clearTokens() {
    this.setToken(null);
    this.setRefreshToken(null);
  }

  private async extractErrorDetail(response: Response): Promise<string> {
    try {
      const text = await response.text();
      const payload = JSON.parse(text) as { detail?: unknown };
      if (typeof payload.detail === 'string' && payload.detail) return payload.detail;
      if (Array.isArray(payload.detail)) return 'Please correct the highlighted fields.';
      return text || `Request failed with status ${response.status}.`;
    } catch {
      return `Request failed with status ${response.status}.`;
    }
  }

  /**
   * Attempt to refresh the access token using the refresh token.
   * Returns the new access token or null if refresh fails.
   */
  private async refreshAccessToken(): Promise<string | null> {
    if (this.refreshing) return this.refreshing;

    this.refreshing = (async () => {
      const refreshToken = this.getRefreshToken();
      if (!refreshToken) return null;

      try {
        const response = await fetch(`${this.config.baseUrl}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!response.ok) {
          this.clearTokens();
          return null;
        }

        const data = (await response.json()) as { access_token?: string; refresh_token?: string };
        if (data.access_token) {
          this.setToken(data.access_token);
        }
        if (data.refresh_token) {
          this.setRefreshToken(data.refresh_token);
        }
        return data.access_token || null;
      } catch {
        this.clearTokens();
        return null;
      } finally {
        this.refreshing = null;
      }
    })();

    return this.refreshing;
  }

  async request<T>(
    path: string,
    init: RequestInit = {},
    options: { skipAuth?: boolean; maxRetries?: number } = {},
  ): Promise<T> {
    const { skipAuth = false, maxRetries = 1 } = options;
    const retries = maxRetries;

    let token: string | null = null;
    if (!skipAuth) {
      token = this.getToken();
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(init.headers as Record<string, string> | undefined),
    };
    if (token) headers.Authorization = `Bearer ${token}`;

    let response: Response;
    try {
      response = await fetch(`${this.config.baseUrl}${path}`, { ...init, headers });
    } catch (err) {
      throw new Error(`Network error: ${err instanceof Error ? err.message : String(err)}`);
    }

    // Handle 401 with token refresh
    if (response.status === 401 && !skipAuth && retries > 0) {
      const newToken = await this.refreshAccessToken();
      if (newToken) {
        // Retry with new token
        const retryHeaders: Record<string, string> = {
          'Content-Type': 'application/json',
          ...(init.headers as Record<string, string> | undefined),
          Authorization: `Bearer ${newToken}`,
        };
        response = await fetch(`${this.config.baseUrl}${path}`, { ...init, headers: retryHeaders });
      } else {
        // Refresh failed — clear tokens and surface auth error
        this.clearTokens();
        throw new Error('Authentication expired. Please log in again.');
      }
    }

    if (!response.ok) {
      const detail = await this.extractErrorDetail(response);
      throw new Error(detail);
    }

    if (response.status === 204) return undefined as unknown as T;
    return (await response.json()) as T;
  }

  /** Convenience: GET request */
  async get<T>(path: string, options?: { skipAuth?: boolean; maxRetries?: number }): Promise<T> {
    return this.request<T>(path, { method: 'GET' }, options);
  }

  /** Convenience: POST request with JSON body */
  async post<T, B = unknown>(
    path: string,
    body: B,
    options?: { skipAuth?: boolean; maxRetries?: number },
  ): Promise<T> {
    return this.request<T>(
      path,
      { method: 'POST', body: JSON.stringify(body) },
      options,
    );
  }

  /** Convenience: PUT request with JSON body */
  async put<T, B = unknown>(
    path: string,
    body: B,
    options?: { skipAuth?: boolean; maxRetries?: number },
  ): Promise<T> {
    return this.request<T>(
      path,
      { method: 'PUT', body: JSON.stringify(body) },
      options,
    );
  }

  /** Convenience: PATCH request with JSON body */
  async patch<T, B = unknown>(
    path: string,
    body: B,
    options?: { skipAuth?: boolean; maxRetries?: number },
  ): Promise<T> {
    return this.request<T>(
      path,
      { method: 'PATCH', body: JSON.stringify(body) },
      options,
    );
  }

  /** Convenience: DELETE request */
  async delete<T>(
    path: string,
    options?: { skipAuth?: boolean; maxRetries?: number },
  ): Promise<T> {
    return this.request<T>(path, { method: 'DELETE' }, options);
  }

  /** Convenience: upload file (FormData) */
  async uploadFile<T>(
    path: string,
    file: File,
    fieldName = 'file',
    options?: { skipAuth?: boolean; maxRetries?: number },
  ): Promise<T> {
    const token = options?.skipAuth ? null : this.getToken();
    const body = new FormData();
    body.append(fieldName, file);

    const headers: Record<string, string> = {};
    if (token) headers.Authorization = `Bearer ${token}`;

    let response: Response;
    try {
      response = await fetch(`${this.config.baseUrl}${path}`, {
        method: 'POST',
        body,
        headers,
      });
    } catch (err) {
      throw new Error(`Network error: ${err instanceof Error ? err.message : String(err)}`);
    }

    if (response.status === 401 && !options?.skipAuth) {
      const newToken = await this.refreshAccessToken();
      if (newToken) {
        const retryHeaders: Record<string, string> = {};
        if (newToken) headers.Authorization = `Bearer ${newToken}`;
        response = await fetch(`${this.config.baseUrl}${path}`, {
          method: 'POST',
          body,
          headers: retryHeaders,
        });
      } else {
        this.clearTokens();
        throw new Error('Authentication expired. Please log in again.');
      }
    }

    if (!response.ok) {
      const detail = await this.extractErrorDetail(response);
      throw new Error(detail);
    }

    if (response.status === 204) return undefined as unknown as T;
    return (await response.json()) as T;
  }

  /** Logout: clear all tokens */
  logout() {
    this.clearTokens();
  }

  /** Get current access token (for external use if needed) */
  getAccessToken(): string | null {
    return this.getToken();
  }
}

// Singleton instance
export const apiClient = new ApiClient();
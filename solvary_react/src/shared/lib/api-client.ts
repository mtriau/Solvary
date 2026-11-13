import { env } from './env';

/**
 * Lightweight HTTP client abstraction.
 * Attaches the stored JWT to every request, and transparently refreshes it
 * once on a 401 (the refresh token rides an httpOnly cookie the server
 * rotates on every use) before retrying the original request.
 */
class ApiClient {
  private baseUrl: string;
  private refreshPromise: Promise<boolean> | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async rawRequest(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<Response> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    const token = localStorage.getItem('auth_token');
    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }
    return fetch(`${this.baseUrl}${endpoint}`, { ...options, headers });
  }

  /** One refresh at a time — concurrent 401s share the same attempt. */
  private tryRefresh(): Promise<boolean> {
    this.refreshPromise ??= (async () => {
      try {
        const response = await fetch(`${this.baseUrl}/auth/refresh`, {
          method: 'POST',
        });
        if (!response.ok) return false;
        const body = (await response.json()) as { access_token: string };
        localStorage.setItem('auth_token', body.access_token);
        return true;
      } catch {
        return false;
      } finally {
        this.refreshPromise = null;
      }
    })();
    return this.refreshPromise;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T> {
    let response = await this.rawRequest(endpoint, options);

    if (
      response.status === 401 &&
      !endpoint.startsWith('/auth/') &&
      (await this.tryRefresh())
    ) {
      response = await this.rawRequest(endpoint, options);
    }

    if (!response.ok) {
      const body = await response.text().catch(() => '');
      throw new ApiError(response.status, response.statusText, body);
    }

    if (response.status === 204) {
      return undefined as T;
    }
    return response.json() as Promise<T>;
  }

  get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  post<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  }

  put<T>(endpoint: string, body: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  patch<T>(endpoint: string, body: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  }

  delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export class ApiError extends Error {
  status: number;
  statusText: string;
  body: string;

  constructor(status: number, statusText: string, body: string) {
    super(`${status} ${statusText}`);
    this.name = 'ApiError';
    this.status = status;
    this.statusText = statusText;
    this.body = body;
  }
}

export const apiClient = new ApiClient(env.apiBaseUrl);

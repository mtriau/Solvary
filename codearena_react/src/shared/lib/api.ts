import { apiClient } from './api-client';
import type { TokenResponse, User } from '@/shared/types/api';

// ── Auth ───────────────────────────────────────────────────────────

export async function login(
  email: string,
  password: string,
): Promise<TokenResponse> {
  return apiClient.post<TokenResponse>('/auth/login', { email, password });
}

export async function register(
  name: string,
  email: string,
  password: string,
): Promise<TokenResponse> {
  return apiClient.post<TokenResponse>('/auth/register', { name, email, password });
}

export async function fetchCurrentUser(): Promise<User> {
  return apiClient.get<User>('/users/me');
}

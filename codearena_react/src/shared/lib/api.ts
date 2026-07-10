import { apiClient } from './api-client';
import type {
  PaginatedResponse,
  ProblemDetail,
  ProblemSummary,
  Submission,
  TokenResponse,
  User,
} from '@/shared/types/api';

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

// ── Problems ───────────────────────────────────────────────────────

export async function fetchProblems(params?: {
  difficulty?: string;
  cursor?: string;
}): Promise<PaginatedResponse<ProblemSummary>> {
  const search = new URLSearchParams();
  if (params?.difficulty) search.set('difficulty', params.difficulty);
  if (params?.cursor) search.set('cursor', params.cursor);
  const qs = search.toString();
  return apiClient.get(`/v1/problems${qs ? `?${qs}` : ''}`);
}

export async function fetchProblem(slug: string): Promise<ProblemDetail> {
  return apiClient.get(`/v1/problems/${slug}`);
}

// ── Submissions ────────────────────────────────────────────────────

export async function createSubmission(data: {
  problem_id: string;
  language: string;
  code: string;
}): Promise<Submission> {
  return apiClient.post('/v1/submissions', data);
}

export async function fetchSubmissions(
  problemId?: string,
): Promise<PaginatedResponse<Submission>> {
  const qs = problemId ? `?problem_id=${problemId}` : '';
  return apiClient.get(`/v1/submissions${qs}`);
}

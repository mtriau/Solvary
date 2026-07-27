import { apiClient } from './api-client';
import type {
  Stats,
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

export async function googleLogin(credential: string): Promise<TokenResponse> {
  return apiClient.post<TokenResponse>('/auth/google', { credential });
}

export async function apiLogout(): Promise<void> {
  return apiClient.post<void>('/auth/logout');
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
  workspace_id?: string;
}): Promise<Submission> {
  return apiClient.post('/v1/submissions', data);
}

export async function fetchSubmissions(
  problemId?: string,
): Promise<PaginatedResponse<Submission>> {
  const qs = problemId ? `?problem_id=${problemId}` : '';
  return apiClient.get(`/v1/submissions${qs}`);
}

// ── Workspaces (M3) ────────────────────────────────────────────────

import type { MemberRole, Workspace, WorkspaceFile, WorkspaceMember } from '@/shared/types/api';

export async function fetchWorkspaces(): Promise<Workspace[]> {
  return apiClient.get('/v1/workspaces');
}

export async function fetchWorkspace(id: string): Promise<Workspace> {
  return apiClient.get(`/v1/workspaces/${id}`);
}

export async function createWorkspace(data: {
  name?: string;
  language: string;
  problem_id?: string;
}): Promise<Workspace> {
  return apiClient.post('/v1/workspaces', data);
}

export async function deleteWorkspace(id: string): Promise<void> {
  return apiClient.delete(`/v1/workspaces/${id}`);
}

export async function fetchMembers(wsId: string): Promise<WorkspaceMember[]> {
  return apiClient.get(`/v1/workspaces/${wsId}/members`);
}

export async function addMember(
  wsId: string,
  email: string,
  role: Exclude<MemberRole, 'owner'>,
): Promise<WorkspaceMember> {
  return apiClient.post(`/v1/workspaces/${wsId}/members`, { email, role });
}

export async function removeMember(wsId: string, memberId: string): Promise<void> {
  return apiClient.delete(`/v1/workspaces/${wsId}/members/${memberId}`);
}

export async function fetchFiles(wsId: string): Promise<WorkspaceFile[]> {
  return apiClient.get(`/v1/workspaces/${wsId}/files`);
}

export async function createFile(
  wsId: string,
  path: string,
): Promise<WorkspaceFile> {
  return apiClient.post(`/v1/workspaces/${wsId}/files`, { path });
}

export async function renameFile(
  wsId: string,
  fileId: string,
  path: string,
): Promise<WorkspaceFile> {
  return apiClient.patch(`/v1/workspaces/${wsId}/files/${fileId}`, { path });
}

export async function deleteFile(wsId: string, fileId: string): Promise<void> {
  return apiClient.delete(`/v1/workspaces/${wsId}/files/${fileId}`);
}

// ── Stats ─────────────────────────────────────────────────────────

export async function fetchMyStats(): Promise<Stats> {
  return apiClient.get<Stats>('/v1/stats/me');
}

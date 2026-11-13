import { apiClient } from './api-client';
import type {
  AiKeyStatus,
  AiKeyTestResult,
  DrillDetail,
  DrillList,
  InterviewerTranscript,
  InterviewSessionDetail,
  InterviewSessionReview,
  InterviewSessionSummary,
  InterviewTemplateDetail,
  InterviewTemplateSummary,
  Stats,
  PaginatedResponse,
  ProblemDetail,
  ProblemSummary,
  PythonPrelude,
  Submission,
  SubmissionDetail,
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

// ── Drills ─────────────────────────────────────────────────────────

export async function fetchDrills(): Promise<DrillList> {
  return apiClient.get('/v1/drills');
}

export async function fetchDrill(slug: string): Promise<DrillDetail> {
  return apiClient.get(`/v1/drills/${slug}`);
}

// ── Submissions ────────────────────────────────────────────────────

export async function createSubmission(data: {
  problem_id: string;
  language: string;
  code: string;
  workspace_id?: string;
  interview_session_id?: string;
}): Promise<Submission> {
  return apiClient.post('/v1/submissions', data);
}

export async function fetchSubmission(id: string): Promise<SubmissionDetail> {
  return apiClient.get(`/v1/submissions/${id}`);
}

export async function fetchSubmissions(
  problemId?: string,
): Promise<PaginatedResponse<Submission>> {
  const qs = problemId ? `?problem_id=${problemId}` : '';
  return apiClient.get(`/v1/submissions${qs}`);
}

// ── Ad-hoc execution (ephemeral — design §6.5) ────────────────────

export async function runCode(data: {
  language: string;
  code: string;
  stdin?: string;
  workspace_id?: string;
  problem_id?: string;
}): Promise<{ run_id: string }> {
  return apiClient.post('/v1/execution/run', data);
}

export async function fetchPythonPrelude(): Promise<PythonPrelude> {
  return apiClient.get('/v1/execution/prelude');
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

// ── Mock interviews ───────────────────────────────────────────────

export async function fetchInterviewTemplates(): Promise<InterviewTemplateSummary[]> {
  return apiClient.get('/v1/interviews/templates');
}

export async function fetchInterviewTemplate(slug: string): Promise<InterviewTemplateDetail> {
  return apiClient.get(`/v1/interviews/templates/${slug}`);
}

export async function startInterview(data: {
  template_id: string;
  language?: string;
  duration_s?: number;
}): Promise<InterviewSessionDetail> {
  return apiClient.post('/v1/interviews/sessions', data);
}

export async function fetchInterviewSessions(
  cursor?: string,
): Promise<PaginatedResponse<InterviewSessionSummary>> {
  return apiClient.get(`/v1/interviews/sessions${cursor ? `?cursor=${cursor}` : ''}`);
}

export async function fetchActiveInterview(): Promise<InterviewSessionSummary | null> {
  return apiClient.get('/v1/interviews/sessions/active');
}

export async function fetchInterviewSession(id: string): Promise<InterviewSessionDetail> {
  return apiClient.get(`/v1/interviews/sessions/${id}`);
}

export async function advanceInterview(id: string): Promise<InterviewSessionDetail> {
  return apiClient.post(`/v1/interviews/sessions/${id}/advance`);
}

export async function switchInterviewStage(
  id: string,
  stage: number,
): Promise<InterviewSessionDetail> {
  return apiClient.post(`/v1/interviews/sessions/${id}/switch`, { stage });
}

export async function finishInterview(id: string): Promise<InterviewSessionDetail> {
  return apiClient.post(`/v1/interviews/sessions/${id}/finish`);
}

export async function abandonInterview(id: string): Promise<InterviewSessionDetail> {
  return apiClient.post(`/v1/interviews/sessions/${id}/abandon`);
}

export async function fetchInterviewReview(id: string): Promise<InterviewSessionReview> {
  return apiClient.get(`/v1/interviews/sessions/${id}/review`);
}

// ── Interviewer agent ─────────────────────────────────────────────
// The turn POST is an SSE stream and lives in features/interviewer/hooks/useInterviewer.ts

export async function fetchAiKey(): Promise<AiKeyStatus> {
  return apiClient.get('/users/me/ai-key');
}

export async function setAiKey(api_key: string): Promise<AiKeyStatus> {
  return apiClient.put('/users/me/ai-key', { api_key });
}

export async function clearAiKey(): Promise<AiKeyStatus> {
  return apiClient.delete('/users/me/ai-key');
}

export async function testAiKey(): Promise<AiKeyTestResult> {
  return apiClient.post('/users/me/ai-key/test');
}

export async function fetchInterviewerTurns(sessionId: string): Promise<InterviewerTranscript> {
  return apiClient.get(`/v1/interviews/sessions/${sessionId}/interviewer/turns`);
}

export async function clearInterviewerTurns(sessionId: string): Promise<void> {
  return apiClient.delete(`/v1/interviews/sessions/${sessionId}/interviewer/turns`);
}

// ── Stats ─────────────────────────────────────────────────────────

export async function fetchMyStats(): Promise<Stats> {
  return apiClient.get<Stats>('/v1/stats/me');
}

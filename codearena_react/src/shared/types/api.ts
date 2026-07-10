export interface User {
  id: string;
  name: string;
  email: string;
  avatar_url: string;
  role: 'user' | 'admin';
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface PaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
  total: number | null;
}

// ── Problems ───────────────────────────────────────────────────────

export type Difficulty = 'easy' | 'medium' | 'hard';

export interface ProblemSummary {
  id: string;
  slug: string;
  title: string;
  difficulty: Difficulty;
  tags: string[];
}

export interface TestCaseSample {
  ordinal: number;
  stdin: string;
  expected_stdout: string;
}

export interface ProblemDetail extends ProblemSummary {
  statement_md: string;
  starter_code: Record<string, string>;
  judge_mode: 'stdio' | 'signature';
  time_limit_s: number;
  memory_kb: number;
  sample_testcases: TestCaseSample[];
}

// ── Submissions / judging ──────────────────────────────────────────

export type Verdict =
  | 'queued'
  | 'running'
  | 'accepted'
  | 'wrong_answer'
  | 'tle'
  | 'mle'
  | 'runtime_error'
  | 'compile_error'
  | 'internal_error';

export interface TestResult {
  ordinal: number;
  status: string;
  runtime_ms: number | null;
  memory_kb: number | null;
}

export interface Submission {
  id: string;
  user_id: string;
  problem_id: string;
  workspace_id: string | null;
  language: string;
  verdict: Verdict;
  runtime_ms: number | null;
  memory_kb: number | null;
  passed: number;
  total: number;
  test_results: TestResult[];
  created_at: string;
}

export interface JudgeEvent {
  kind: 'queued' | 'compiling' | 'case_started' | 'case_result' | 'verdict' | 'error';
  ordinal?: number;
  status?: string;
  runtime_ms?: number;
  memory_kb?: number;
  verdict?: string;
  message?: string;
  stdout?: string;
  passed?: number;
  total?: number;
}

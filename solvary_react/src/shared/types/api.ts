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
  judge_mode: 'stdio' | 'signature' | 'pytest';
  time_limit_s: number;
  memory_kb: number;
  sample_testcases: TestCaseSample[];
  /** pytest mode: the provided suite files (name → source) */
  harness_files?: Record<string, string> | null;
}

// ── Drills (quick idiom exercises) ─────────────────────────────────

export interface DrillSummary {
  id: string;
  slug: string;
  title: string;
  topic: string;
  order: number;
  solved: boolean;
  attempts: number;
}

export interface DrillTopic {
  slug: string;
  title: string;
  blurb: string;
  drills: DrillSummary[];
  solved: number;
  total: number;
}

export interface DrillList {
  topics: DrillTopic[];
  solved: number;
  total: number;
  next_slug: string | null;
}

export interface DrillDetail extends ProblemDetail {
  topic: string;
  topic_title: string;
  order: number;
  position: number;
  topic_total: number;
  editorial_md: string | null;
  solved: boolean;
  attempts: number;
  prev_slug: string | null;
  next_slug: string | null;
  next_unsolved_slug: string | null;
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
  interview_session_id?: string | null;
  language: string;
  verdict: Verdict;
  runtime_ms: number | null;
  memory_kb: number | null;
  passed: number;
  total: number;
  test_results: TestResult[];
  created_at: string;
}

/** `GET /v1/submissions/{id}`: the row plus the code that was judged. */
export interface SubmissionDetail extends Submission {
  code: string;
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

// ── Workspaces (M3) ────────────────────────────────────────────────

export type MemberRole = 'owner' | 'editor' | 'viewer';

export interface Workspace {
  id: string;
  name: string;
  owner_id: string;
  language: string;
  problem_id: string | null;
  problem_slug: string | null;
  problem_title: string | null;
  my_role: MemberRole;
  kind: 'standard' | 'interview';
  created_at: string;
}

export interface WorkspaceMember {
  id: string;
  user_id: string;
  name: string;
  email: string;
  avatar_url: string;
  role: MemberRole;
}

export interface WorkspaceFile {
  id: string;
  path: string;
  language: string | null;
}

// ── Mock interviews ───────────────────────────────────────────────

export type InterviewFormat = 'levels' | 'questions';
export type InterviewStatus = 'active' | 'finished' | 'expired' | 'abandoned';

export interface InterviewTemplateInfo {
  id: string;
  slug: string;
  title: string;
  format: InterviewFormat;
  duration_s: number;
  advance: 'free' | 'on_submit' | 'on_accept';
  pacing: 'coached' | 'strict';
}

export interface InterviewStageInfo {
  ordinal: number;
  title: string;
  budget_s: number | null;
}

export interface InterviewScore {
  passed: number;
  total: number;
  percent: number;
}

export interface InterviewSessionSummary {
  id: string;
  template: InterviewTemplateInfo;
  status: InterviewStatus;
  language: string;
  /** This run's clock; differs from template.duration_s when overridden at start. */
  duration_s: number;
  started_at: string;
  ends_at: string;
  finished_at: string | null;
  server_time: string;
  score: InterviewScore;
  time_used_s: number;
  stages_reached: number;
  stage_count: number;
  diagnosis: string | null;
}

export interface InterviewTemplateSummary extends InterviewTemplateInfo {
  stages: InterviewStageInfo[];
  last_result: InterviewSessionSummary | null;
}

export interface InterviewTemplateDetail extends InterviewTemplateSummary {
  description_md: string;
}

export interface InterviewStageResult {
  submissions: number;
  best_submission_id: string | null;
  best_verdict: string | null;
  best_passed: number;
  best_total: number;
  time_spent_s: number;
}

export interface InterviewStageView extends InterviewStageInfo {
  locked: boolean;
  file_id: string | null;
  deadline_at: string | null;
  problem: ProblemDetail | null;
  editorial_md: string | null;
  result: InterviewStageResult;
}

export interface InterviewSessionDetail extends InterviewSessionSummary {
  workspace_id: string | null;
  current_stage: number;
  unlocked_through: number;
  stages: InterviewStageView[];
  timeline: { stage: number; at: string }[];
}

export interface InterviewSessionReview extends InterviewSessionDetail {
  submissions: Submission[];
  /** Interviewer agent transcript, oldest first (empty when the agent was never used). */
  interviewer_turns: InterviewerTurn[];
}

// ── Interviewer agent (SOLVARY_INTERVIEWER_DESIGN.md) ─────────────

export type KeySource = 'user' | 'server' | 'none';

export interface AiKeyStatus {
  configured: boolean;
  last4: string | null;
  source: KeySource;
}

export interface AiKeyTestResult {
  ok: boolean;
  model: string;
  source: KeySource;
}

export type InterviewerTrigger = 'speech' | 'typed' | 'event' | 'opening';
export type MicMode = 'open' | 'push' | 'off';

export interface InterviewerTurn {
  id: string;
  ordinal: number;
  role: 'user' | 'assistant';
  trigger: InterviewerTrigger | null;
  /** utterance / "[event] …" lines, or the reply / "[silent]" / "[refused]" */
  content: string;
  digest: string;
  silent: boolean;
  model: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  cache_read_input_tokens: number | null;
  cache_creation_input_tokens: number | null;
  created_at: string;
}

export interface InterviewerTranscript {
  turns: InterviewerTurn[];
  /** fire the idle event after this many seconds without activity */
  idle_s: number;
  model: string;
  key_source: KeySource;
  active: boolean;
}

export interface JudgeFailure {
  name: string;
  detail: string;
}

export interface JudgeSnapshot {
  submission_id: string | null;
  verdict: string;
  passed: number;
  total: number;
  failures: JudgeFailure[];
  age_s: number;
}

export interface RunSnapshot {
  status: string | null;
  stdin: string;
  stdout: string;
  stderr: string;
  age_s: number;
}

/** The client half of the context package: what is on the candidate's screen. */
export interface ScreenContext {
  stage: number;
  code: string;
  code_changed_since_last_turn: boolean;
  judge: JudgeSnapshot | null;
  run: RunSnapshot | null;
  visible_pane: 'judge' | 'run' | 'none';
  seconds_since_last_edit: number;
  mic: MicMode;
}

export interface InterviewerTurnRequest {
  trigger: InterviewerTrigger;
  utterance?: string;
  events?: string[];
  screen: ScreenContext;
}

/** The terminal SSE frame of a turn. */
export interface InterviewerDoneFrame {
  done: true;
  spoke: boolean;
  refused?: boolean;
  truncated?: boolean;
  turn_id?: string;
  user_turn_id?: string;
  model?: string;
  usage?: Partial<
    Record<
      'input_tokens' | 'output_tokens' | 'cache_read_input_tokens' | 'cache_creation_input_tokens',
      number
    >
  >;
  error?: boolean;
  status?: number | null;
}

// ── Stats & accolades ─────────────────────────────────────────────

export interface TotalsStats {
  solved: number;
  total_problems: number;
  submissions: number;
  accepted_submissions: number;
  acceptance_rate: number;
  current_streak_days: number;
  longest_streak_days: number;
}

export interface DifficultyStat {
  difficulty: Difficulty;
  solved: number;
  total: number;
}

export interface LanguageStat {
  language: string;
  submissions: number;
  solved: number;
}

export interface HeatmapDay {
  day: string;
  count: number;
}

export interface StatsBadge {
  id: string;
  name: string;
  description: string;
  icon: string;
  earned: boolean;
}

export interface RecentSubmission {
  id: string;
  problem_slug: string;
  problem_title: string;
  difficulty: Difficulty;
  language: string;
  verdict: string;
  runtime_ms: number | null;
  created_at: string;
}

export interface Stats {
  totals: TotalsStats;
  by_difficulty: DifficultyStat[];
  by_language: LanguageStat[];
  heatmap: HeatmapDay[];
  badges: StatsBadge[];
  recent: RecentSubmission[];
}

// ── Python prelude (names available without an import) ───────────

export interface PythonPrelude {
  language: string;
  modules: string[];
  names: Record<string, string[]>;
}

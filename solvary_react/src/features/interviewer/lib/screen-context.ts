import { failureDetail } from '@/features/execution/lib/failure-detail';
import type { TestLabel } from '@/features/execution/lib/test-labels';
import type { RunState } from '@/features/execution/hooks/useRunStream';
import type { JudgeEvent, JudgeFailure, MicMode, ScreenContext } from '@/shared/types/api';

const MAX_FAILURES = 12;
const MAX_FAILURE_DETAIL = 800;
const MAX_RUN_OUTPUT = 2000;
const MAX_STDIN = 1000;

export interface ScreenInputs {
  /** The part the candidate is looking at. */
  stage: number;
  /** The whole editor buffer right now. */
  code: string;
  /** The code sent on the previous turn (null before the first turn). */
  lastCode: string | null;
  judge: {
    events: JudgeEvent[];
    verdict: JudgeEvent | null;
    submissionId: string | null;
    /** epoch ms the verdict arrived, null if none */
    at: number | null;
    labels: Record<number, TestLabel> | null;
  };
  run: {
    state: RunState;
    stdin: string;
    at: number | null;
  };
  pane: 'judge' | 'run' | 'none';
  /** epoch ms of the candidate's last local edit, null if none since load */
  lastEditAt: number | null;
  mic: MicMode;
  now?: number;
}

function ageS(at: number | null, now: number): number {
  return at == null ? 0 : Math.max(0, Math.floor((now - at) / 1000));
}

/** Failing tests by name (pytest ids when the problem has them) with their detail. */
export function judgeFailures(
  events: JudgeEvent[],
  labels: Record<number, TestLabel> | null,
): JudgeFailure[] {
  return events
    .filter((e) => e.kind === 'case_result' && e.status !== 'passed')
    .slice(0, MAX_FAILURES)
    .map((e) => {
      const ordinal = e.ordinal ?? 0;
      const label = labels?.[ordinal];
      const name = label ? (label.file ? `${label.file}::${label.name}` : label.name) : `Test ${ordinal}`;
      return { name, detail: failureDetail(e).slice(0, MAX_FAILURE_DETAIL) };
    });
}

/**
 * The client half of the interviewer's context package (design §4.1): what
 * the candidate sees. The server adds the truth (clock, budgets, results).
 */
export function buildScreenContext(input: ScreenInputs): ScreenContext {
  const now = input.now ?? Date.now();
  const { judge, run } = input;
  const verdict = judge.verdict;
  const showRun = run.state.status != null || run.state.error != null;
  return {
    stage: input.stage,
    code: input.code,
    code_changed_since_last_turn: input.lastCode === null || input.lastCode !== input.code,
    judge: verdict
      ? {
          submission_id: judge.submissionId,
          verdict: verdict.verdict ?? 'unknown',
          passed: verdict.passed ?? 0,
          total: verdict.total ?? 0,
          failures: judgeFailures(judge.events, judge.labels),
          age_s: ageS(judge.at, now),
        }
      : null,
    run: showRun
      ? {
          status: run.state.status ?? (run.state.error ? 'error' : null),
          stdin: run.stdin.slice(0, MAX_STDIN),
          stdout: run.state.stdout.slice(0, MAX_RUN_OUTPUT),
          stderr: (run.state.error ?? run.state.stderr).slice(0, MAX_RUN_OUTPUT),
          age_s: ageS(run.at, now),
        }
      : null,
    visible_pane: input.pane,
    seconds_since_last_edit: Math.min(86_400, ageS(input.lastEditAt, now)),
    mic: input.mic,
  };
}

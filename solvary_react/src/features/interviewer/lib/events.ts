import type { RunState } from '@/features/execution/hooks/useRunStream';
import type { TestLabel } from '@/features/execution/lib/test-labels';
import { fmtClock } from '@/features/interviews/lib/format';
import type { InterviewStageView, JudgeEvent } from '@/shared/types/api';

/** Event lines the page sends the interviewer (design §2.3). One line each, plain English. */

export const STARTED_EVENT = 'The interview has started.';
export const NUDGE_EVENT = 'The candidate asked for a check-in.';

export function verdictEvent(
  verdict: JudgeEvent,
  events: JudgeEvent[],
  labels: Record<number, TestLabel> | null,
): string {
  const failing = events.filter((e) => e.kind === 'case_result' && e.status !== 'passed');
  const names = failing.slice(0, 3).map((e) => {
    const label = labels?.[e.ordinal ?? 0];
    return label ? label.name : `Test ${e.ordinal}`;
  });
  const more = failing.length > 3 ? ` and ${failing.length - 3} more` : '';
  const tail = names.length ? ` Failing: ${names.join(', ')}${more}.` : '';
  return `Submission judged: ${verdict.verdict} ${verdict.passed ?? 0}/${verdict.total ?? 0}.${tail}`;
}

export function runEvent(state: RunState): string {
  if (state.error) return `Run failed: ${state.error.slice(0, 120)}`;
  return `Run finished with ${state.status ?? 'an error'}.`;
}

export function stageEvent(stage: InterviewStageView): string {
  const budget = stage.budget_s != null ? ` (budget ${fmtClock(stage.budget_s)})` : '';
  return `Moved to part ${stage.ordinal}: ${stage.title}${budget}.`;
}

export function budgetEvent(stage: InterviewStageView, elapsedS: number): string {
  return `Budget for part ${stage.ordinal} exceeded: ${fmtClock(elapsedS)} spent of ${fmtClock(stage.budget_s ?? 0)}.`;
}

export function idleEvent(idleS: number): string {
  return `No speech, typing or code changes for ${Math.max(1, Math.round(idleS / 60))} minutes.`;
}

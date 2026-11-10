import type { JudgeEvent } from '@/shared/types/api';

/** "wrong_answer on test 3 (2/4 passed)" — what the AI assistant gets told. */
export function summarizeVerdict(
  verdict: JudgeEvent | null,
  events: JudgeEvent[],
): string | null {
  if (!verdict?.verdict) return null;
  const firstFail = events.find((e) => e.kind === 'case_result' && e.status !== 'passed');
  const where = firstFail?.ordinal != null ? ` on test ${firstFail.ordinal}` : '';
  return `${verdict.verdict}${where} (${verdict.passed ?? 0}/${verdict.total ?? 0} passed)`;
}

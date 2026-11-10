import type { ProblemDetail } from '@/shared/types/api';

export interface TestLabel {
  file: string;
  name: string;
}

/**
 * pytest-mode problems store the test id (`file.py::test_name`) as each
 * sample case's stdin, so the judge panel can show names instead of numbers.
 * Returns null for ordinary stdio problems.
 */
export function testLabels(problem: ProblemDetail | null | undefined): Record<number, TestLabel> | null {
  if (!problem || problem.judge_mode !== 'pytest') return null;
  const out: Record<number, TestLabel> = {};
  for (const tc of problem.sample_testcases) {
    const id = tc.stdin.trim();
    const sep = id.indexOf('::');
    out[tc.ordinal] =
      sep === -1 ? { file: '', name: id } : { file: id.slice(0, sep), name: id.slice(sep + 2) };
  }
  return out;
}

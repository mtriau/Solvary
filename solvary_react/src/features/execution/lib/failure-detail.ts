import type { JudgeEvent } from '@/shared/types/api';

/** Strip the harness's PASS/FAIL prefix; what is left is the assertion/traceback. */
export function failureDetail(e: JudgeEvent): string {
  const out = (e.stdout ?? '').replace(/^(PASS|FAIL)\n?/, '').trimEnd();
  return out || e.message || (e.status === 'tle' ? 'timed out' : 'no output');
}

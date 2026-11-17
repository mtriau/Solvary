import type { InterviewPause } from '@/shared/types/api';

/**
 * Milliseconds of [fromMs, toMs] during which the clock stood still. A pause
 * in progress (no `end`) runs through `toMs`.
 */
export function pausedBetweenMs(pauses: InterviewPause[], fromMs: number, toMs: number): number {
  let total = 0;
  for (const p of pauses) {
    const lo = Math.max(fromMs, new Date(p.start).getTime());
    const hi = Math.min(toMs, p.end ? new Date(p.end).getTime() : toMs);
    if (hi > lo) total += hi - lo;
  }
  return total;
}

/** Running milliseconds between two wall-clock moments: pauses excluded. */
export function runningMsBetween(pauses: InterviewPause[], fromMs: number, toMs: number): number {
  return Math.max(0, toMs - fromMs - pausedBetweenMs(pauses, fromMs, toMs));
}

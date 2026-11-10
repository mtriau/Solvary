/** 5025 → "1:23:45", 731 → "12:11", 59 → "0:59" */
export function fmtClock(totalS: number): string {
  const s = Math.max(0, Math.floor(totalS));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const mm = h > 0 ? String(m).padStart(2, '0') : String(m);
  return `${h > 0 ? `${h}:` : ''}${mm}:${String(sec).padStart(2, '0')}`;
}

/** 5400 → "90 min", 3600 → "60 min", 90 → "2 min" */
export function fmtMinutes(totalS: number): string {
  return `${Math.max(1, Math.round(totalS / 60))} min`;
}

export const STATUS_LABELS: Record<string, string> = {
  active: 'In progress',
  finished: 'Finished',
  expired: 'Time ran out',
  abandoned: 'Abandoned',
};

export const FORMAT_LABELS: Record<string, string> = {
  levels: 'Levels · one evolving problem',
  questions: 'Questions · independent problems',
};

import type { InterviewSessionReview } from '@/shared/types/api';
import { fmtClock } from '../lib/format';

/**
 * Review page: planned budget vs actual time per stage, with each
 * submission as a tick (green = accepted). Bars share one scale so a part
 * that ate the interview is visibly wider than its budget marker.
 */
export function PaceTimeline({ review }: { review: InterviewSessionReview }) {
  const maxS = Math.max(
    1,
    ...review.stages.map((s) => Math.max(s.result.time_spent_s, s.budget_s ?? 0)),
  );
  const startMs = new Date(review.started_at).getTime();
  // Submission ticks are placed inside their stage's bar by the time they
  // happened relative to that stage's first activation
  const firstAt = (ordinal: number) => {
    const e = review.timeline.find((t) => t.stage === ordinal);
    return e ? new Date(e.at).getTime() : startMs;
  };
  const problemToStage = new Map(review.stages.map((s) => [s.problem?.id, s.ordinal]));

  return (
    <div className="space-y-2">
      {review.stages.map((s) => {
        const spent = s.result.time_spent_s;
        const budget = s.budget_s;
        const over = budget != null && spent > budget * 1.1;
        const ticks = review.submissions.filter((sub) => problemToStage.get(sub.problem_id) === s.ordinal);
        return (
          <div key={s.ordinal} className="grid grid-cols-[11rem_1fr_9rem] items-center gap-3 text-xs">
            <div className="truncate">
              <span className="font-medium text-gray-900">{s.title}</span>
              {s.locked && <span className="ml-1 text-gray-400">(never reached)</span>}
            </div>
            <div className="relative h-5 bg-gray-100 rounded">
              {budget != null && (
                <div
                  className="absolute top-0 bottom-0 border-r-2 border-dashed border-gray-400"
                  style={{ left: `${(budget / maxS) * 100}%` }}
                  title={`budget ${fmtClock(budget)}`}
                />
              )}
              <div
                className={`absolute top-0 bottom-0 left-0 rounded ${over ? 'bg-red-300' : 'bg-indigo-300'}`}
                style={{ width: `${(spent / maxS) * 100}%` }}
              />
              {ticks.map((sub) => {
                const offsetS = (new Date(sub.created_at).getTime() - firstAt(s.ordinal)) / 1000;
                const left = Math.min(100, Math.max(0, (offsetS / maxS) * 100));
                return (
                  <div
                    key={sub.id}
                    className={`absolute top-0.5 bottom-0.5 w-1 rounded ${sub.verdict === 'accepted' ? 'bg-green-600' : 'bg-red-600'}`}
                    style={{ left: `${left}%` }}
                    title={`${sub.verdict} · ${sub.passed}/${sub.total}`}
                  />
                );
              })}
            </div>
            <div className={`font-mono tabular-nums ${over ? 'text-red-600' : 'text-gray-600'}`}>
              {fmtClock(spent)}
              {budget != null && <span className="text-gray-400"> / {fmtClock(budget)}</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
}

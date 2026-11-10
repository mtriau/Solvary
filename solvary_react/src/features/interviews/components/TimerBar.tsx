import { CheckCircle2, Flag, Lock, Timer, XCircle } from 'lucide-react';
import type { InterviewSessionDetail } from '@/shared/types/api';
import type { Countdown } from '../hooks/useCountdown';
import { fmtClock } from '../lib/format';

interface Props {
  session: InterviewSessionDetail;
  countdown: Countdown;
  /** Seconds spent so far on the current stage (server-corrected). */
  stageElapsedS: number;
  onFinish: () => void;
  onAbandon: () => void;
  busy?: boolean;
}

const PHASE_STYLES: Record<string, string> = {
  ok: 'text-gray-900',
  warn: 'text-amber-600',
  critical: 'text-red-600 animate-pulse',
  over: 'text-red-600',
};

/**
 * Sticky header: the interview clock, overall progress, one chip per stage
 * (locked / current with budget / best score), finish & abandon.
 */
export function TimerBar({ session, countdown, stageElapsedS, onFinish, onAbandon, busy }: Props) {
  const total = session.duration_s;
  const usedPct = Math.min(100, ((total - countdown.remainingS) / total) * 100);
  const current = session.stages.find((s) => s.ordinal === session.current_stage);
  const budget = current?.budget_s ?? null;
  const budgetPct = budget ? stageElapsedS / budget : 0;
  const budgetTone =
    budgetPct >= 1.5 ? 'text-red-600' : budgetPct >= 1 ? 'text-amber-600' : 'text-gray-500';

  return (
    <div className="border-b border-gray-200 bg-white px-4 py-2 shrink-0">
      <div className="flex items-center gap-4">
        <div className={`flex items-center gap-1.5 font-mono text-2xl font-semibold tabular-nums ${PHASE_STYLES[countdown.phase]}`}>
          <Timer size={20} />
          {fmtClock(countdown.remainingS)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="h-1.5 rounded-full bg-gray-100 overflow-hidden">
            <div
              className={`h-full transition-[width] ${countdown.phase === 'ok' ? 'bg-indigo-500' : countdown.phase === 'warn' ? 'bg-amber-500' : 'bg-red-500'}`}
              style={{ width: `${usedPct}%` }}
            />
          </div>
          <div className="mt-1 flex items-center gap-1.5 flex-wrap text-[11px]">
            {session.stages.map((s) => {
              const isCurrent = s.ordinal === session.current_stage;
              const r = s.result;
              return (
                <span
                  key={s.ordinal}
                  className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded border ${
                    isCurrent
                      ? 'border-indigo-300 bg-indigo-50 text-indigo-800'
                      : s.locked
                        ? 'border-gray-200 text-gray-400'
                        : 'border-gray-200 text-gray-600'
                  }`}
                  title={s.budget_s ? `budget ${fmtClock(s.budget_s)}` : undefined}
                >
                  {s.locked ? (
                    <Lock size={10} />
                  ) : r.best_verdict === 'accepted' ? (
                    <CheckCircle2 size={10} className="text-green-600" />
                  ) : r.submissions > 0 ? (
                    <XCircle size={10} className="text-red-500" />
                  ) : null}
                  {s.title}
                  {!s.locked && r.submissions > 0 && (
                    <span className="opacity-70">
                      {r.best_passed}/{r.best_total}
                    </span>
                  )}
                  {isCurrent && budget != null && (
                    <span className={`ml-1 font-mono ${budgetTone}`}>
                      {fmtClock(stageElapsedS)} / {fmtClock(budget)}
                    </span>
                  )}
                </span>
              );
            })}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={onAbandon}
            disabled={busy}
            className="px-2.5 py-1.5 text-xs text-gray-500 hover:text-gray-800 disabled:opacity-50"
            title="End without a score"
          >
            Abandon
          </button>
          <button
            onClick={onFinish}
            disabled={busy}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            title="Stop the clock and go to the review"
          >
            <Flag size={12} /> Finish early
          </button>
        </div>
      </div>
    </div>
  );
}

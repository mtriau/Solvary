import { Link, useLocation } from 'react-router-dom';
import { Timer } from 'lucide-react';
import { useActiveInterview } from '../hooks/useActiveInterview';
import { useCountdown } from '../hooks/useCountdown';
import { fmtClock } from '../lib/format';

/** Top-bar reminder that the clock is running — leaving the page doesn't stop it. */
export function ActiveInterviewPill() {
  const { data: active } = useActiveInterview();
  const location = useLocation();
  const countdown = useCountdown(active?.ends_at, active?.server_time);
  if (!active || countdown.remainingS <= 0) return null;
  const href = `/interviews/sessions/${active.id}`;
  if (location.pathname === href) return null;
  const tone =
    countdown.phase === 'ok'
      ? 'bg-indigo-500/30 text-indigo-100'
      : countdown.phase === 'warn'
        ? 'bg-amber-500/30 text-amber-100'
        : 'bg-red-500/40 text-red-100';
  return (
    <Link
      to={href}
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium font-mono ${tone}`}
      title="Interview in progress — the clock keeps running"
    >
      <Timer size={11} />
      {fmtClock(countdown.remainingS)}
    </Link>
  );
}

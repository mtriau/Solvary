import { useEffect, useRef, useState } from 'react';

export type CountdownPhase = 'ok' | 'warn' | 'critical' | 'over';

export interface Countdown {
  /** Seconds left on the interview clock (never negative). */
  remainingS: number;
  phase: CountdownPhase;
  /** Server-corrected "now" in epoch ms — use it for every elapsed-time display. */
  nowMs: number;
}

/**
 * Renders a server-authoritative deadline. The server's `server_time` is
 * compared with the local clock once per response to derive an offset, so a
 * skewed client clock still counts down correctly; the tick itself is local.
 * `onExpire` fires exactly once when the clock hits zero.
 */
export function useCountdown(
  endsAt: string | undefined,
  serverTime: string | undefined,
  onExpire?: () => void,
): Countdown {
  const offsetRef = useRef(0);
  const firedRef = useRef(false);
  const onExpireRef = useRef(onExpire);
  onExpireRef.current = onExpire;
  const [nowMs, setNowMs] = useState(() => Date.now());

  useEffect(() => {
    if (serverTime) offsetRef.current = new Date(serverTime).getTime() - Date.now();
  }, [serverTime]);

  useEffect(() => {
    firedRef.current = false;
    if (!endsAt) return;
    const end = new Date(endsAt).getTime();
    const tick = () => {
      const now = Date.now() + offsetRef.current;
      setNowMs(now);
      if (now >= end && !firedRef.current) {
        firedRef.current = true;
        onExpireRef.current?.();
      }
    };
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, [endsAt]);

  const remainingS = endsAt
    ? Math.max(0, Math.ceil((new Date(endsAt).getTime() - nowMs) / 1000))
    : 0;
  const phase: CountdownPhase =
    remainingS <= 0 ? 'over' : remainingS <= 120 ? 'critical' : remainingS <= 600 ? 'warn' : 'ok';
  return { remainingS, phase, nowMs };
}

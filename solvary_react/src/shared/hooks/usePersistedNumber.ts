import { useCallback, useState } from 'react';

/**
 * A number kept in localStorage (panel sizes, slider positions). Values are
 * clamped to [min, max] on every write; `reset` restores the default.
 */
export function usePersistedNumber(key: string, initial: number, min: number, max: number) {
  const clamp = useCallback((v: number) => Math.min(max, Math.max(min, v)), [min, max]);
  const [value, setValue] = useState<number>(() => {
    const raw = localStorage.getItem(key);
    const parsed = raw === null ? NaN : Number(raw);
    return clamp(Number.isFinite(parsed) ? parsed : initial);
  });

  const set = useCallback(
    (next: number | ((prev: number) => number)) => {
      setValue((prev) => {
        const v = clamp(typeof next === 'function' ? next(prev) : next);
        localStorage.setItem(key, String(v));
        return v;
      });
    },
    [key, clamp],
  );
  const reset = useCallback(() => {
    localStorage.removeItem(key);
    setValue(clamp(initial));
  }, [key, initial, clamp]);

  return [value, set, reset] as const;
}

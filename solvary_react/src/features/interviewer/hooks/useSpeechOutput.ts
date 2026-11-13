import { useCallback, useEffect, useRef, useState } from 'react';

const STORAGE_KEY = 'interviewer.tts';
/** Recognition stays paused this long after the voice stops (room echo). */
const TAIL_MS = 400;

/**
 * Optional voice for the interviewer's replies via `speechSynthesis` (design
 * §7). One utterance per reply, spoken when the stream ends. `speaking` stays
 * true for a short tail after the voice stops so the mic never hears it.
 */
export function useSpeechOutput() {
  const supported = typeof window !== 'undefined' && 'speechSynthesis' in window;
  const [enabled, setEnabledState] = useState<boolean>(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === '1';
    } catch {
      return false;
    }
  });
  const [speaking, setSpeaking] = useState(false);
  const tailRef = useRef<number | null>(null);

  const setEnabled = useCallback((on: boolean) => {
    setEnabledState(on);
    try {
      localStorage.setItem(STORAGE_KEY, on ? '1' : '0');
    } catch {
      /* private mode */
    }
    if (!on && supported) window.speechSynthesis.cancel();
  }, [supported]);

  const stop = useCallback(() => {
    if (!supported) return;
    window.speechSynthesis.cancel();
    if (tailRef.current) window.clearTimeout(tailRef.current);
    setSpeaking(false);
  }, [supported]);

  const speak = useCallback(
    (text: string) => {
      if (!supported || !enabled || !text.trim()) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.05;
      const done = () => {
        if (tailRef.current) window.clearTimeout(tailRef.current);
        tailRef.current = window.setTimeout(() => setSpeaking(false), TAIL_MS);
      };
      utterance.onstart = () => {
        if (tailRef.current) window.clearTimeout(tailRef.current);
        setSpeaking(true);
      };
      utterance.onend = done;
      utterance.onerror = done;
      setSpeaking(true); // from the call, not onstart — Chrome fires onstart late
      window.speechSynthesis.speak(utterance);
    },
    [supported, enabled],
  );

  useEffect(() => () => stop(), [stop]);

  return { supported, enabled, setEnabled, speaking, speak, stop };
}

import { useCallback, useEffect, useRef, useState } from 'react';
import type { MicMode } from '@/shared/types/api';

const STORAGE_KEY = 'interviewer.mic';
const RESTART_MS = 250;
const PUSH_FLUSH_FALLBACK_MS = 1500;

interface Options {
  /** One finished utterance (design §3 decision 8: after the settle timer, or on push release). */
  onUtterance: (text: string) => void;
  /** Open mic: silence after a final result before the text is sent. */
  settleMs?: number;
  lang?: string;
}

function readStoredMode(): MicMode {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    return v === 'open' || v === 'push' ? v : 'off';
  } catch {
    return 'off';
  }
}

/**
 * Browser speech-to-text (Web Speech API) with endpointing that suits
 * someone narrating code:
 * - `open`: continuous recognition; each final phrase (re)starts a settle
 *   timer; when it fires the accumulated text is one utterance. Chrome ends
 *   recognition after ~60 s of silence or on network blips: it is restarted.
 * - `push`: start on press, stop on release, send what was heard.
 * `setPaused(true)` aborts recognition (used while the interviewer's voice
 * plays) and `setPaused(false)` restarts it in open mode.
 */
export function useSpeechInput({ onUtterance, settleMs = 1200, lang = 'en-US' }: Options) {
  const Ctor =
    typeof window !== 'undefined'
      ? (window.SpeechRecognition ?? window.webkitSpeechRecognition)
      : undefined;
  const supported = !!Ctor;

  const [mode, setModeState] = useState<MicMode>(() => (supported ? readStoredMode() : 'off'));
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState('');
  const [error, setError] = useState<string | null>(null);

  const recRef = useRef<SolvarySpeechRecognition | null>(null);
  const modeRef = useRef<MicMode>(mode);
  const pausedRef = useRef(false);
  const pushActiveRef = useRef(false);
  const flushOnEndRef = useRef(false);
  const pendingRef = useRef('');
  const settleRef = useRef<number | null>(null);
  const restartRef = useRef<number | null>(null);
  const fallbackRef = useRef<number | null>(null);
  const onUtteranceRef = useRef(onUtterance);
  onUtteranceRef.current = onUtterance;

  const clearTimer = (ref: { current: number | null }) => {
    if (ref.current != null) window.clearTimeout(ref.current);
    ref.current = null;
  };

  const flush = useCallback(() => {
    clearTimer(settleRef);
    clearTimer(fallbackRef);
    const text = pendingRef.current.replace(/\s+/g, ' ').trim();
    pendingRef.current = '';
    setInterim('');
    if (text) onUtteranceRef.current(text);
  }, []);

  const shouldRun = useCallback(
    () =>
      !pausedRef.current &&
      (modeRef.current === 'open' || (modeRef.current === 'push' && pushActiveRef.current)),
    [],
  );

  const start = useCallback(() => {
    if (!Ctor || !shouldRun()) return;
    clearTimer(restartRef);
    let rec = recRef.current;
    if (!rec) {
      rec = new Ctor();
      rec.lang = lang;
      rec.maxAlternatives = 1;
      rec.onstart = () => setListening(true);
      rec.onresult = (ev) => {
        let interimText = '';
        let gotFinal = false;
        for (let i = ev.resultIndex; i < ev.results.length; i++) {
          const result = ev.results[i];
          const transcript = result[0]?.transcript ?? '';
          if (result.isFinal) {
            pendingRef.current += (pendingRef.current ? ' ' : '') + transcript.trim();
            gotFinal = true;
          } else {
            interimText += transcript;
          }
        }
        setInterim((pendingRef.current + ' ' + interimText).trim());
        if (gotFinal && modeRef.current === 'open') {
          clearTimer(settleRef);
          settleRef.current = window.setTimeout(flush, settleMs);
        }
      };
      rec.onerror = (ev) => {
        if (ev.error === 'not-allowed' || ev.error === 'service-not-allowed') {
          setError('Microphone access was denied. Allow it in the browser and try again.');
          pausedRef.current = false;
          modeRef.current = 'off';
          setModeState('off');
        } else if (ev.error === 'audio-capture') {
          setError('No microphone was found.');
          modeRef.current = 'off';
          setModeState('off');
        }
        // "no-speech", "aborted", "network": onend follows and restarts
      };
      rec.onend = () => {
        setListening(false);
        if (flushOnEndRef.current) {
          flushOnEndRef.current = false;
          flush();
        }
        if (shouldRun()) {
          clearTimer(restartRef);
          restartRef.current = window.setTimeout(() => {
            if (shouldRun()) {
              try {
                recRef.current?.start();
              } catch {
                /* already started */
              }
            }
          }, RESTART_MS);
        }
      };
      recRef.current = rec;
    }
    rec.continuous = true;
    rec.interimResults = true;
    try {
      rec.start();
      setError(null);
    } catch {
      /* InvalidStateError: already running */
    }
  }, [Ctor, flush, lang, settleMs, shouldRun]);

  const halt = useCallback((discard: boolean) => {
    clearTimer(restartRef);
    clearTimer(settleRef);
    if (discard) {
      pendingRef.current = '';
      setInterim('');
    }
    try {
      recRef.current?.abort();
    } catch {
      /* not running */
    }
    setListening(false);
  }, []);

  const setMode = useCallback(
    (next: MicMode) => {
      if (!supported) return;
      modeRef.current = next;
      setModeState(next);
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch {
        /* private mode */
      }
      pushActiveRef.current = false;
      if (next === 'open') {
        pausedRef.current = false;
        start();
      } else {
        halt(true);
      }
    },
    [halt, start, supported],
  );

  /** Push-to-talk: hold. */
  const pressStart = useCallback(() => {
    if (modeRef.current !== 'push' || pushActiveRef.current) return;
    pushActiveRef.current = true;
    pendingRef.current = '';
    flushOnEndRef.current = false;
    start();
  }, [start]);

  /** Push-to-talk: release → send what was heard once the recognizer settles. */
  const pressEnd = useCallback(() => {
    if (modeRef.current !== 'push' || !pushActiveRef.current) return;
    pushActiveRef.current = false;
    flushOnEndRef.current = true;
    try {
      recRef.current?.stop(); // lets the last final result arrive before onend
    } catch {
      flushOnEndRef.current = false;
      flush();
      return;
    }
    clearTimer(fallbackRef);
    fallbackRef.current = window.setTimeout(() => {
      if (flushOnEndRef.current) {
        flushOnEndRef.current = false;
        flush();
      }
    }, PUSH_FLUSH_FALLBACK_MS);
  }, [flush]);

  /** Pause while the interviewer's voice plays (and resume afterwards). */
  const setPaused = useCallback(
    (paused: boolean) => {
      if (pausedRef.current === paused) return;
      pausedRef.current = paused;
      if (paused) halt(true);
      else if (modeRef.current === 'open') start();
    },
    [halt, start],
  );

  // Start on mount when the stored mode is open; stop on unmount
  useEffect(() => {
    if (modeRef.current === 'open') start();
    return () => {
      pausedRef.current = true;
      halt(true);
      recRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    supported,
    mode,
    setMode,
    listening,
    interim,
    error,
    pressStart,
    pressEnd,
    setPaused,
    flush,
  };
}

export type SpeechInput = ReturnType<typeof useSpeechInput>;

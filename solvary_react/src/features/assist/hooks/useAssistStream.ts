import { useCallback, useRef, useState } from 'react';
import { env } from '@/shared/lib/env';

export interface AssistRequest {
  question: string;
  problem_id?: string;
  code?: string;
  language?: string;
  verdict?: string;
  /** Review a finished mock interview — authorizes its private problems. */
  interview_session_id?: string;
}

interface AssistState {
  answer: string;
  isStreaming: boolean;
  error: string | null;
}

const INITIAL: AssistState = { answer: '', isStreaming: false, error: null };

/**
 * Streams `POST /v1/assist/explain` (SSE `{content}`* then `{done}`) into
 * a growing markdown answer. Same fetch-reader pattern as the judge stream.
 */
export function useAssistStream() {
  const [state, setState] = useState<AssistState>(INITIAL);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setState(INITIAL);
  }, []);

  const ask = useCallback(async (body: AssistRequest) => {
    abortRef.current?.abort();
    const abort = new AbortController();
    abortRef.current = abort;
    setState({ ...INITIAL, isStreaming: true });

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${env.apiBaseUrl}/v1/assist/explain`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
        signal: abort.signal,
      });
      if (!response.ok || !response.body) {
        const detail = await response
          .json()
          .then((j: { detail?: string }) => j.detail)
          .catch(() => undefined);
        throw new Error(detail ?? `Assistant request failed (${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const frames = buffer.split('\n\n');
        buffer = frames.pop() ?? '';
        for (const frame of frames) {
          const line = frame.trim();
          if (!line.startsWith('data: ')) continue;
          const payload = JSON.parse(line.slice(6)) as { content?: string; done?: boolean };
          if (payload.content) {
            setState((s) => ({ ...s, answer: s.answer + payload.content }));
          }
          if (payload.done) {
            setState((s) => ({ ...s, isStreaming: false }));
          }
        }
      }
      setState((s) => ({ ...s, isStreaming: false }));
    } catch (err) {
      if ((err as Error).name === 'AbortError') return;
      setState((s) => ({ ...s, isStreaming: false, error: (err as Error).message }));
    }
  }, []);

  return { ...state, ask, reset };
}

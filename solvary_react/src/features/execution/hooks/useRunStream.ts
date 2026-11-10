import { useCallback, useRef, useState } from 'react';
import type { JudgeEvent } from '@/shared/types/api';
import { runCode } from '@/shared/lib/api';
import { env } from '@/shared/lib/env';

export interface RunState {
  runId: string | null;
  isRunning: boolean;
  status: string | null; // finished | tle | mle | runtime_error | compile_error
  stdout: string;
  stderr: string;
  runtimeMs: number | null;
  error: string | null;
}

const INITIAL: RunState = {
  runId: null,
  isRunning: false,
  status: null,
  stdout: '',
  stderr: '',
  runtimeMs: null,
  error: null,
};

/**
 * Ad-hoc "Run" — execute the buffer against custom stdin, no judging, no
 * history (design §6.5: ephemeral, fire-and-watch). Same SSE reader as the
 * judge stream; the server replays `queued` so an early subscribe is safe.
 * With `problemId` on a pytest-mode problem the server runs the provided
 * suite instead (stdin = test ids, one per line; blank = all).
 */
export function useRunStream() {
  const [state, setState] = useState<RunState>(INITIAL);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setState(INITIAL);
  }, []);

  const run = useCallback(
    async (
      language: string,
      code: string,
      stdin: string,
      workspaceId?: string,
      problemId?: string,
    ) => {
      abortRef.current?.abort();
      const abort = new AbortController();
      abortRef.current = abort;
      setState({ ...INITIAL, isRunning: true });

      try {
        const { run_id } = await runCode({
          language,
          code,
          stdin,
          ...(workspaceId ? { workspace_id: workspaceId } : {}),
          ...(problemId ? { problem_id: problemId } : {}),
        });
        setState((s) => ({ ...s, runId: run_id }));

        const token = localStorage.getItem('auth_token');
        const response = await fetch(`${env.apiBaseUrl}/v1/execution/${run_id}/events`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          signal: abort.signal,
        });
        if (!response.ok || !response.body) {
          throw new Error(`Stream failed: ${response.status}`);
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
            const event: JudgeEvent = JSON.parse(line.slice(6));
            setState((s) => {
              if (event.kind === 'case_result') {
                return {
                  ...s,
                  status: event.status ?? null,
                  stdout: event.stdout ?? '',
                  stderr: event.message ?? '',
                  runtimeMs: event.runtime_ms ?? null,
                };
              }
              if (event.kind === 'error') {
                return {
                  ...s,
                  isRunning: false,
                  status: event.status ?? 'error',
                  stderr: event.message ?? '',
                  error: event.status === 'compile_error' ? null : (event.message ?? 'Run failed'),
                };
              }
              if (event.kind === 'verdict') {
                return { ...s, isRunning: false };
              }
              return s;
            });
          }
        }
        setState((s) => ({ ...s, isRunning: false }));
      } catch (err) {
        if ((err as Error).name === 'AbortError') return;
        setState((s) => ({ ...s, isRunning: false, error: (err as Error).message }));
      }
    },
    [],
  );

  return { ...state, run, reset };
}

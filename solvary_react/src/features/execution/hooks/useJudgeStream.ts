import { useCallback, useRef, useState } from 'react';
import type { JudgeEvent } from '@/shared/types/api';
import { createSubmission } from '@/shared/lib/api';
import { env } from '@/shared/lib/env';

interface JudgeState {
  submissionId: string | null;
  events: JudgeEvent[];
  verdict: JudgeEvent | null;
  isJudging: boolean;
  error: string | null;
}

const INITIAL: JudgeState = {
  submissionId: null,
  events: [],
  verdict: null,
  isJudging: false,
  error: null,
};

/**
 * Submit code and stream judge events over SSE (replay-then-follow —
 * the same fetch-reader pattern as MattChat's useStreamingMessage).
 *
 * `follow` streams an EXISTING submission — replay-then-follow on the
 * server means late subscribers still get the whole story. This is how
 * workspace peers watch each other's runs in a pair interview (M4).
 */
export function useJudgeStream() {
  const [state, setState] = useState<JudgeState>(INITIAL);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setState(INITIAL);
  }, []);

  const stream = useCallback(async (submissionId: string, abort: AbortController) => {
    const token = localStorage.getItem('auth_token');
    const response = await fetch(
      `${env.apiBaseUrl}/v1/submissions/${submissionId}/events`,
      {
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        signal: abort.signal,
      },
    );
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
        setState((s) => ({
          ...s,
          events: [...s.events, event],
          verdict: event.kind === 'verdict' ? event : s.verdict,
          isJudging: event.kind !== 'verdict' && event.kind !== 'error',
          error:
            event.kind === 'error' ? (event.message ?? 'Judge error') : s.error,
        }));
      }
    }
  }, []);

  const submit = useCallback(
    async (
      problemId: string,
      language: string,
      code: string,
      workspaceId?: string,
    ): Promise<string | null> => {
      abortRef.current?.abort();
      const abort = new AbortController();
      abortRef.current = abort;
      setState({ ...INITIAL, isJudging: true });

      try {
        const submission = await createSubmission({
          problem_id: problemId,
          language,
          code,
          ...(workspaceId ? { workspace_id: workspaceId } : {}),
        });
        setState((s) => ({ ...s, submissionId: submission.id }));
        await stream(submission.id, abort);
        return submission.id;
      } catch (err) {
        if ((err as Error).name === 'AbortError') return null;
        setState((s) => ({
          ...s,
          isJudging: false,
          error: (err as Error).message,
        }));
        return null;
      }
    },
    [stream],
  );

  const follow = useCallback(
    async (submissionId: string) => {
      abortRef.current?.abort();
      const abort = new AbortController();
      abortRef.current = abort;
      setState({ ...INITIAL, submissionId, isJudging: true });

      try {
        await stream(submissionId, abort);
      } catch (err) {
        if ((err as Error).name === 'AbortError') return;
        setState((s) => ({
          ...s,
          isJudging: false,
          error: (err as Error).message,
        }));
      }
    },
    [stream],
  );

  return { ...state, submit, follow, reset };
}

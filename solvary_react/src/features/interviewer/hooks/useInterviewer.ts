import { useCallback, useEffect, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchInterviewerTurns } from '@/shared/lib/api';
import { env } from '@/shared/lib/env';
import type {
  InterviewerDoneFrame,
  InterviewerTrigger,
  InterviewerTurnRequest,
  ScreenContext,
} from '@/shared/types/api';
import { INTERVIEWER_KEYS } from './useAiKey';

export interface QueuedTurn {
  trigger: InterviewerTrigger;
  utterance?: string;
  events?: string[];
}

export interface TurnUsage {
  input: number;
  output: number;
  cached: number;
}

interface Options {
  sessionId: string;
  /** Turns are only sent while this is true (active session, key configured, pane enabled). */
  enabled: boolean;
  /** Builds the client half of the context package right before a turn is sent. */
  buildScreen: (lastCode: string | null) => ScreenContext;
  /** Called with the spoken reply once the stream ends (for the optional voice). */
  onReply?: (text: string) => void;
}

const MAX_EVENTS = 8;

/** Pop the next turn: speech/typed first, absorbing every queued event; else one merged event turn. */
function takeNext(queue: QueuedTurn[]): QueuedTurn | null {
  if (queue.length === 0) return null;
  const idx = queue.findIndex((q) => q.trigger !== 'event');
  const item = idx >= 0 ? queue.splice(idx, 1)[0] : queue.shift()!;
  const events = [...(item.events ?? [])];
  for (let i = queue.length - 1; i >= 0; i--) {
    if (queue[i].trigger === 'event') {
      events.unshift(...(queue[i].events ?? []));
      queue.splice(i, 1);
    }
  }
  const unique = [...new Set(events)].slice(-MAX_EVENTS);
  return { ...item, events: unique };
}

async function streamTurn(
  sessionId: string,
  body: InterviewerTurnRequest,
  handlers: { onContent: (text: string) => void; onError: (message: string) => void },
  signal: AbortSignal,
): Promise<InterviewerDoneFrame | null> {
  const token = localStorage.getItem('auth_token');
  const response = await fetch(
    `${env.apiBaseUrl}/v1/interviews/sessions/${sessionId}/interviewer/turns`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
      signal,
    },
  );
  if (!response.ok || !response.body) {
    const payload = (await response.json().catch(() => ({}))) as {
      detail?: string;
      error_code?: string;
    };
    const err = new Error(payload.detail ?? `Interviewer request failed (${response.status})`);
    (err as Error & { status?: number; code?: string }).status = response.status;
    (err as Error & { status?: number; code?: string }).code = payload.error_code;
    throw err;
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let done: InterviewerDoneFrame | null = null;
  for (;;) {
    const { done: eof, value } = await reader.read();
    if (eof) break;
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split('\n\n');
    buffer = frames.pop() ?? '';
    for (const frame of frames) {
      const line = frame.trim();
      if (!line.startsWith('data: ')) continue;
      const payload = JSON.parse(line.slice(6)) as {
        content?: string;
        error?: string;
        done?: boolean;
      } & Partial<InterviewerDoneFrame>;
      if (payload.content) handlers.onContent(payload.content);
      if (payload.error && typeof payload.error === 'string') handlers.onError(payload.error);
      if (payload.done) done = payload as InterviewerDoneFrame;
    }
  }
  return done;
}

/**
 * The interviewer agent's client (design §7): the persisted transcript, a
 * FIFO turn queue (one in flight; events coalesce behind it; speech absorbs
 * pending events), and the streamed reply.
 */
export function useInterviewer({ sessionId, enabled, buildScreen, onReply }: Options) {
  const queryClient = useQueryClient();
  const transcript = useQuery({
    queryKey: INTERVIEWER_KEYS.turns(sessionId),
    queryFn: () => fetchInterviewerTurns(sessionId),
    enabled: !!sessionId,
  });

  const [streaming, setStreaming] = useState(false);
  const [partial, setPartial] = useState('');
  const [pending, setPending] = useState<QueuedTurn | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [noKey, setNoKey] = useState(false);
  const [usage, setUsage] = useState<TurnUsage>({ input: 0, output: 0, cached: 0 });
  const [lastUserTurnAt, setLastUserTurnAt] = useState<number | null>(null);

  const queueRef = useRef<QueuedTurn[]>([]);
  const busyRef = useRef(false);
  const abortRef = useRef<AbortController | null>(null);
  const lastCodeRef = useRef<string | null>(null);
  const enabledRef = useRef(enabled);
  enabledRef.current = enabled;
  const buildScreenRef = useRef(buildScreen);
  buildScreenRef.current = buildScreen;
  const onReplyRef = useRef(onReply);
  onReplyRef.current = onReply;

  const keySource = transcript.data?.key_source;
  useEffect(() => {
    if (keySource && keySource !== 'none') setNoKey(false);
  }, [keySource]);

  /** One turn: build the screen, stream the reply, refresh the transcript. */
  const runTurn = useCallback(
    async (item: QueuedTurn) => {
      const abort = new AbortController();
      abortRef.current = abort;
      setStreaming(true);
      setPartial('');
      setError(null);
      setPending(item);
      let reply = '';
      let streamError: string | null = null;
      try {
        const screen = buildScreenRef.current(lastCodeRef.current);
        lastCodeRef.current = screen.code;
        const done = await streamTurn(
          sessionId,
          { trigger: item.trigger, utterance: item.utterance, events: item.events, screen },
          {
            onContent: (text) => {
              reply += text;
              setPartial((p) => p + text);
            },
            onError: (message) => {
              streamError = message;
            },
          },
          abort.signal,
        );
        if (streamError) setError(streamError);
        if (done?.usage) {
          setUsage((u) => ({
            input: u.input + (done.usage?.input_tokens ?? 0),
            output: u.output + (done.usage?.output_tokens ?? 0),
            cached: u.cached + (done.usage?.cache_read_input_tokens ?? 0),
          }));
        }
        if (done && !done.error) {
          await queryClient.invalidateQueries({ queryKey: INTERVIEWER_KEYS.turns(sessionId) });
          if (done.spoke && reply.trim()) onReplyRef.current?.(reply.trim());
        }
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          const e = err as Error & { status?: number; code?: string };
          if (e.status === 402 || e.code === 'NO_API_KEY') {
            setNoKey(true);
            queueRef.current = [];
          }
          setError(e.message);
        }
      } finally {
        abortRef.current = null;
        setStreaming(false);
        setPartial('');
        setPending(null);
      }
    },
    [queryClient, sessionId],
  );

  /** Drain the queue, one turn at a time (events queued meanwhile coalesce). */
  const pump = useCallback(async () => {
    if (busyRef.current) return;
    busyRef.current = true;
    try {
      for (;;) {
        const item = takeNext(queueRef.current);
        if (!item) break;
        if (!enabledRef.current) {
          queueRef.current = [];
          break;
        }
        await runTurn(item);
      }
    } finally {
      busyRef.current = false;
    }
  }, [runTurn]);

  const enqueue = useCallback(
    (item: QueuedTurn) => {
      if (!enabledRef.current || noKey) return;
      if (item.trigger === 'speech' || item.trigger === 'typed') setLastUserTurnAt(Date.now());
      queueRef.current.push(item);
      void pump();
    },
    [noKey, pump],
  );

  useEffect(() => () => abortRef.current?.abort(), []);

  return {
    turns: transcript.data?.turns ?? [],
    transcript: transcript.data,
    isLoading: transcript.isLoading,
    streaming,
    partial,
    pending,
    error,
    noKey,
    usage,
    lastUserTurnAt,
    enqueue,
  };
}

export type Interviewer = ReturnType<typeof useInterviewer>;

import { useEffect, useRef } from 'react';
import { Mic } from 'lucide-react';
import type { InterviewerTurn } from '@/shared/types/api';
import type { QueuedTurn } from '../hooks/useInterviewer';

const SILENT = '[silent]';
const REFUSED = '[refused]';

interface Props {
  turns: InterviewerTurn[];
  /** The reply streaming in right now. */
  partial?: string;
  /** The user turn being answered (not yet persisted). */
  pending?: QueuedTurn | null;
  /** Live speech not yet sent. */
  interim?: string;
  streaming?: boolean;
  /** Review page: no auto-scroll, tighter spacing. */
  compact?: boolean;
}

function eventLines(content: string): string[] {
  return content
    .split('\n')
    .map((l) => l.replace(/^\[event\]\s*/, '').trim())
    .filter(Boolean);
}

function UserBubble({ text, speech }: { text: string; speech: boolean }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[88%] rounded-2xl rounded-br-sm bg-indigo-600 text-white px-3 py-1.5 text-[13px] leading-snug whitespace-pre-wrap break-words">
        {speech && <Mic size={10} className="inline mr-1 -mt-0.5 opacity-70" />}
        {text}
      </div>
    </div>
  );
}

function InterviewerBubble({ text, muted }: { text: string; muted?: boolean }) {
  return (
    <div className="flex justify-start">
      <div
        className={`max-w-[92%] rounded-2xl rounded-bl-sm px-3 py-1.5 text-[13px] leading-snug whitespace-pre-wrap break-words ${
          muted ? 'bg-gray-50 text-gray-400 italic border border-gray-100' : 'bg-gray-100 text-gray-900'
        }`}
      >
        {text}
      </div>
    </div>
  );
}

function SystemLines({ lines }: { lines: string[] }) {
  return (
    <div className="text-center space-y-0.5">
      {lines.map((l, i) => (
        <div key={i} className="text-[11px] text-gray-400">
          · {l}
        </div>
      ))}
    </div>
  );
}

/** The interviewer transcript: candidate right, interviewer left, events as grey system lines. */
export function TranscriptList({ turns, partial, pending, interim, streaming, compact }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!compact) bottomRef.current?.scrollIntoView({ block: 'end' });
  }, [turns.length, partial, pending, interim, compact]);

  return (
    <div className={compact ? 'space-y-1.5' : 'space-y-2'}>
      {turns.map((t) => {
        if (t.role === 'assistant') {
          if (t.silent || t.content === SILENT) return null;
          if (t.content === REFUSED) {
            return <InterviewerBubble key={t.id} text="The interviewer declined to answer that." muted />;
          }
          return <InterviewerBubble key={t.id} text={t.content} />;
        }
        if (t.trigger === 'event' || t.trigger === 'opening') {
          return <SystemLines key={t.id} lines={eventLines(t.content)} />;
        }
        return <UserBubble key={t.id} text={t.content} speech={t.trigger === 'speech'} />;
      })}
      {pending &&
        (pending.trigger === 'speech' || pending.trigger === 'typed' ? (
          <>
            {pending.events && pending.events.length > 0 && <SystemLines lines={pending.events} />}
            <UserBubble text={pending.utterance ?? ''} speech={pending.trigger === 'speech'} />
          </>
        ) : (
          <SystemLines lines={pending.events ?? []} />
        ))}
      {partial ? (
        <InterviewerBubble text={partial} />
      ) : streaming ? (
        <div className="text-[11px] text-gray-400 pl-1 animate-pulse">thinking…</div>
      ) : null}
      {interim && (
        <div className="flex justify-end">
          <div className="max-w-[88%] rounded-2xl rounded-br-sm border border-dashed border-gray-300 text-gray-400 px-3 py-1.5 text-[13px] leading-snug whitespace-pre-wrap break-words">
            <Mic size={10} className="inline mr-1 -mt-0.5" />
            {interim}
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}

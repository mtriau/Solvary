import { useState, type FormEvent, type KeyboardEvent } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  Hand,
  HelpCircle,
  KeyRound,
  Loader2,
  Mic,
  MicOff,
  PanelRightClose,
  Send,
  Volume2,
  VolumeX,
} from 'lucide-react';
import type { MicMode } from '@/shared/types/api';
import type { Interviewer } from '../hooks/useInterviewer';
import type { SpeechInput } from '../hooks/useSpeechInput';
import type { useSpeechOutput } from '../hooks/useSpeechOutput';
import { TranscriptList } from './TranscriptList';

interface Props {
  interviewer: Interviewer;
  speech: SpeechInput;
  tts: ReturnType<typeof useSpeechOutput>;
  /** The session still accepts turns. */
  active: boolean;
  onSend: (text: string) => void;
  onNudge: () => void;
  onCollapse: () => void;
}

const MIC_MODES: { value: MicMode; label: string; title: string }[] = [
  { value: 'off', label: 'Off', title: 'Microphone off' },
  { value: 'open', label: 'Open', title: 'Open mic: what you say is sent once you pause (Ctrl+Shift+M toggles)' },
  { value: 'push', label: 'Push', title: 'Push to talk: hold the button or Ctrl+Shift+Space' },
];

function shortModel(model: string | undefined): string {
  return (model ?? '').replace(/^claude-/, '') || 'claude';
}

function fmtK(n: number): string {
  return n >= 10_000 ? `${Math.round(n / 1000)}k` : n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n);
}

/**
 * The third column of the interview page (design §10): transcript, mic and
 * voice controls, composer. Hidden [silent] turns never render.
 */
export function InterviewerPane({ interviewer, speech, tts, active, onSend, onNudge, onCollapse }: Props) {
  const [draft, setDraft] = useState('');
  const keySource = interviewer.transcript?.key_source ?? 'none';
  const needsKey = interviewer.noKey || (!!interviewer.transcript && keySource === 'none');
  const canTalk = active && !needsKey;

  const send = () => {
    const text = draft.trim();
    if (!text || !canTalk) return;
    onSend(text);
    setDraft('');
  };
  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    send();
  };
  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const usage = interviewer.usage;
  const usageTitle = `Tokens this session — in: ${usage.input}, out: ${usage.output}, cached in: ${usage.cached}`;

  return (
    <div className="h-full flex flex-col min-h-0">
      {/* header */}
      <div className="h-10 px-3 flex items-center gap-2 border-b border-gray-200 shrink-0">
        <span className="text-sm font-semibold text-gray-900">Interviewer</span>
        <span
          className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 truncate"
          title={interviewer.transcript?.model}
        >
          {shortModel(interviewer.transcript?.model)}
        </span>
        {(usage.input > 0 || usage.output > 0) && (
          <span className="text-[10px] text-gray-400 font-mono" title={usageTitle}>
            Σ {fmtK(usage.input)}↑ {fmtK(usage.output)}↓
          </span>
        )}
        <div className="flex-1" />
        <button
          onClick={onCollapse}
          className="p-1 rounded text-gray-400 hover:text-gray-700 hover:bg-gray-100"
          title="Hide the interviewer pane"
        >
          <PanelRightClose size={15} />
        </button>
      </div>

      {/* mic + voice controls */}
      <div className="px-3 py-2 border-b border-gray-100 flex items-center gap-2 shrink-0">
        <div
          className="inline-flex rounded-lg border border-gray-200 overflow-hidden text-[11px] font-medium"
          role="radiogroup"
          aria-label="Microphone mode"
          title={speech.supported ? undefined : 'Speech recognition needs Chrome or Edge; typing still works.'}
        >
          {MIC_MODES.map((m) => (
            <button
              key={m.value}
              type="button"
              role="radio"
              aria-checked={speech.mode === m.value}
              disabled={!speech.supported || !canTalk}
              onClick={() => speech.setMode(m.value)}
              title={m.title}
              className={`px-2 py-1 disabled:opacity-40 ${
                speech.mode === m.value ? 'bg-gray-900 text-white' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              {m.value === 'off' ? <MicOff size={11} className="inline -mt-0.5 mr-1" /> : <Mic size={11} className="inline -mt-0.5 mr-1" />}
              {m.label}
            </button>
          ))}
        </div>
        {speech.mode === 'push' && (
          <button
            type="button"
            disabled={!canTalk}
            onPointerDown={(e) => {
              e.preventDefault();
              speech.pressStart();
            }}
            onPointerUp={speech.pressEnd}
            onPointerLeave={speech.pressEnd}
            onPointerCancel={speech.pressEnd}
            className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-medium border select-none disabled:opacity-40 ${
              speech.listening
                ? 'bg-red-600 border-red-600 text-white'
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
            title="Hold to talk (or hold Ctrl+Shift+Space)"
          >
            <Hand size={11} /> {speech.listening ? 'Listening…' : 'Hold to talk'}
          </button>
        )}
        {speech.mode === 'open' && (
          <span className="inline-flex items-center gap-1 text-[11px] text-gray-500">
            <span
              className={`inline-block w-2 h-2 rounded-full ${
                speech.listening ? 'bg-red-500 animate-pulse' : 'bg-gray-300'
              }`}
            />
            {speech.listening ? 'listening' : tts.speaking ? 'muted while speaking' : 'paused'}
          </span>
        )}
        <div className="flex-1" />
        <button
          type="button"
          disabled={!tts.supported}
          onClick={() => tts.setEnabled(!tts.enabled)}
          aria-pressed={tts.enabled}
          title={
            tts.supported
              ? tts.enabled
                ? 'Voice on: replies are read aloud (mic pauses while speaking)'
                : 'Voice off'
              : 'Speech synthesis is not available in this browser'
          }
          className={`p-1.5 rounded-lg border disabled:opacity-40 ${
            tts.enabled ? 'bg-indigo-50 border-indigo-200 text-indigo-700' : 'border-gray-200 text-gray-500 hover:bg-gray-50'
          }`}
        >
          {tts.enabled ? <Volume2 size={13} /> : <VolumeX size={13} />}
        </button>
      </div>

      {/* notices */}
      {needsKey && (
        <div className="mx-3 mt-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900 flex items-start gap-2">
          <KeyRound size={13} className="mt-0.5 shrink-0" />
          <span>
            No Anthropic API key yet. Add yours under{' '}
            <Link to="/interviews" className="font-medium underline">
              Interviews → Interviewer
            </Link>{' '}
            and the interviewer joins this session.
          </span>
        </div>
      )}
      {!active && (
        <div className="mx-3 mt-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-600">
          The interview is over; the transcript is read-only.
        </div>
      )}
      {(speech.error || interviewer.error) && (
        <div className="mx-3 mt-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800 flex items-start gap-2">
          <AlertTriangle size={13} className="mt-0.5 shrink-0" />
          <span>{speech.error ?? interviewer.error}</span>
        </div>
      )}

      {/* transcript */}
      <div className="flex-1 min-h-0 overflow-y-auto px-3 py-3">
        {interviewer.isLoading ? (
          <div className="flex justify-center py-6">
            <Loader2 size={18} className="animate-spin text-gray-300" />
          </div>
        ) : interviewer.turns.length === 0 && !interviewer.pending && !interviewer.streaming ? (
          <p className="text-xs text-gray-400 text-center py-6 px-4">
            {canTalk
              ? 'Talk through your plan, or type below. The interviewer speaks when an interviewer would.'
              : 'No interviewer transcript for this session.'}
          </p>
        ) : null}
        <TranscriptList
          turns={interviewer.turns}
          partial={interviewer.partial}
          pending={interviewer.pending}
          interim={speech.interim}
          streaming={interviewer.streaming}
        />
      </div>

      {/* composer */}
      {active && (
        <form onSubmit={onSubmit} className="border-t border-gray-200 p-2 shrink-0">
          <div className="flex items-end gap-1.5">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={onKeyDown}
              disabled={!canTalk}
              rows={2}
              maxLength={2000}
              placeholder={canTalk ? 'Say something to the interviewer… (Enter sends)' : 'Add an API key to talk to the interviewer'}
              className="flex-1 resize-none px-3 py-1.5 border border-gray-300 rounded-lg text-[13px] focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:bg-gray-50"
            />
            <div className="flex flex-col gap-1">
              <button
                type="submit"
                disabled={!canTalk || !draft.trim()}
                className="p-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40"
                title="Send"
              >
                <Send size={14} />
              </button>
              <button
                type="button"
                onClick={onNudge}
                disabled={!canTalk || interviewer.streaming}
                className="p-2 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 disabled:opacity-40"
                title="Ask the interviewer for a check-in"
              >
                <HelpCircle size={14} />
              </button>
            </div>
          </div>
        </form>
      )}
    </div>
  );
}

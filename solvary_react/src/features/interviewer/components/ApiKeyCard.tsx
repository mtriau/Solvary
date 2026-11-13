import { useState, type FormEvent } from 'react';
import { CheckCircle2, KeyRound, Loader2, Trash2 } from 'lucide-react';
import { ApiError } from '@/shared/lib/api-client';
import { useAiKey } from '../hooks/useAiKey';

function detailOf(err: unknown): string {
  if (err instanceof ApiError) {
    try {
      const body = JSON.parse(err.body) as { detail?: string; errors?: { message: string }[] };
      return body.errors?.[0]?.message ?? body.detail ?? err.message;
    } catch {
      return err.message;
    }
  }
  return (err as Error).message;
}

/**
 * "Interviewer" card on the interviews page: paste an Anthropic API key once;
 * it is stored encrypted server-side and never shown again (design §8).
 */
export function ApiKeyCard() {
  const { status, isLoading, save, remove, test } = useAiKey();
  const [draft, setDraft] = useState('');
  const [message, setMessage] = useState<{ tone: 'ok' | 'error'; text: string } | null>(null);

  const onSave = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    try {
      await save.mutateAsync(draft.trim());
      setDraft('');
      setMessage({ tone: 'ok', text: 'Key saved. The interviewer will use it in your next mock.' });
    } catch (err) {
      setMessage({ tone: 'error', text: detailOf(err) });
    }
  };
  const onTest = async () => {
    setMessage(null);
    try {
      const r = await test.mutateAsync();
      setMessage({ tone: 'ok', text: `Key works — ${r.model} answered.` });
    } catch (err) {
      setMessage({ tone: 'error', text: detailOf(err) });
    }
  };
  const onRemove = async () => {
    setMessage(null);
    try {
      await remove.mutateAsync();
      setMessage({ tone: 'ok', text: 'Key removed.' });
    } catch (err) {
      setMessage({ tone: 'error', text: detailOf(err) });
    }
  };

  const statusText = isLoading
    ? 'Checking…'
    : status?.source === 'user'
      ? `Your key ····${status.last4 ?? ''}`
      : status?.source === 'server'
        ? 'Using the server key'
        : 'Not configured';
  const busy = save.isPending || remove.isPending || test.isPending;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h2 className="font-semibold text-gray-900 flex items-center gap-2">
            <KeyRound size={16} className="text-indigo-600" /> Interviewer
          </h2>
          <p className="text-xs text-gray-500 mt-0.5">
            An AI interviewer sits in a pane during every mock: it sees your code, the tests and the
            clock, listens to your microphone and asks the questions a real screen would. It runs on
            your own Anthropic API key, stored encrypted and never shown again.
          </p>
        </div>
        <span
          className={`shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded border text-xs font-medium ${
            status?.configured
              ? 'bg-green-50 text-green-700 border-green-200'
              : 'bg-gray-50 text-gray-500 border-gray-200'
          }`}
        >
          {status?.configured && <CheckCircle2 size={12} />}
          {statusText}
        </span>
      </div>

      <form onSubmit={onSave} className="mt-3 flex items-center gap-2">
        <input
          type="password"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={status?.source === 'user' ? 'Paste a new key to replace yours' : 'sk-ant-…'}
          autoComplete="off"
          spellCheck={false}
          className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button
          type="submit"
          disabled={busy || draft.trim().length < 20}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
        >
          {save.isPending ? <Loader2 size={14} className="animate-spin" /> : null}
          Save
        </button>
        <button
          type="button"
          onClick={onTest}
          disabled={busy || !status?.configured}
          title="Send one tiny request on the configured key"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
        >
          {test.isPending ? <Loader2 size={14} className="animate-spin" /> : null}
          Test
        </button>
        {status?.source === 'user' && (
          <button
            type="button"
            onClick={onRemove}
            disabled={busy}
            title="Forget your key"
            className="p-1.5 text-gray-400 hover:text-red-600 disabled:opacity-50"
          >
            <Trash2 size={15} />
          </button>
        )}
      </form>
      {message && (
        <div
          className={`mt-2 text-xs rounded-lg px-3 py-1.5 border ${
            message.tone === 'ok'
              ? 'bg-green-50 text-green-800 border-green-200'
              : 'bg-red-50 text-red-700 border-red-200'
          }`}
        >
          {message.text}
        </div>
      )}
    </div>
  );
}

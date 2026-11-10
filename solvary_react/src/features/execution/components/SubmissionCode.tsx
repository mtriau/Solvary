import { useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';
import { Check, Copy, Loader2 } from 'lucide-react';
import { useSubmission } from '@/features/execution/hooks/useSubmission';

const LINE_PX = 19;
const MIN_PX = 140;
const MAX_PX = 520;

/**
 * Read-only view of the code a submission was judged with. Fetches lazily
 * (the list payloads carry no code) and sizes itself to the file, capped.
 * `onLoaded` hands the code back to the parent, e.g. to feed the AI panel.
 */
export function SubmissionCode({
  submissionId,
  onLoaded,
  action,
}: {
  submissionId: string;
  onLoaded?: (code: string) => void;
  /** Optional extra button rendered in the toolbar (e.g. "Load into editor"). */
  action?: { label: string; onClick: (code: string) => void };
}) {
  const { data, isLoading, error } = useSubmission(submissionId);
  const [copied, setCopied] = useState(false);
  const code = data?.code;
  useEffect(() => {
    if (code !== undefined) onLoaded?.(code);
  }, [code, onLoaded]);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-xs text-gray-400 py-3">
        <Loader2 size={14} className="animate-spin" /> Loading code…
      </div>
    );
  }
  if (!data) {
    return <p className="text-xs text-red-600 py-2">{error ? 'Could not load this submission.' : 'No code.'}</p>;
  }
  const lines = data.code.split('\n').length;
  const height = Math.min(MAX_PX, Math.max(MIN_PX, lines * LINE_PX + 24));

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(data.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable: nothing to do */
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
      <div className="flex items-center gap-3 px-3 py-1.5 border-b border-gray-100 bg-gray-50 text-[11px] text-gray-500">
        <span className="font-mono">{data.language}</span>
        <span>{lines} line{lines === 1 ? '' : 's'}</span>
        <span className="flex-1" />
        {action && (
          <button
            onClick={() => action.onClick(data.code)}
            className="font-medium text-indigo-700 hover:underline"
          >
            {action.label}
          </button>
        )}
        <button onClick={copy} className="inline-flex items-center gap-1 font-medium text-gray-600 hover:text-gray-900">
          {copied ? <Check size={12} /> : <Copy size={12} />} {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <Editor
        height={height}
        language={data.language}
        value={data.code}
        options={{
          readOnly: true,
          domReadOnly: true,
          minimap: { enabled: false },
          fontSize: 13,
          lineNumbersMinChars: 3,
          scrollBeyondLastLine: false,
          padding: { top: 8, bottom: 8 },
          renderLineHighlight: 'none',
          overviewRulerLanes: 0,
        }}
      />
    </div>
  );
}

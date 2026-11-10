import { useState } from 'react';
import { CheckCircle2, ChevronDown, ChevronRight, Circle, Loader2, XCircle } from 'lucide-react';
import type { JudgeEvent } from '@/shared/types/api';
import type { TestLabel } from '../lib/test-labels';

const VERDICT_LABELS: Record<string, string> = {
  accepted: 'Accepted',
  wrong_answer: 'Wrong Answer',
  tle: 'Time Limit Exceeded',
  mle: 'Memory Limit Exceeded',
  runtime_error: 'Runtime Error',
  compile_error: 'Compile Error',
  internal_error: 'Internal Error',
};

const STATUS_LABELS: Record<string, string> = {
  passed: 'passed',
  failed: 'failed',
  tle: 'timed out',
  mle: 'out of memory',
  runtime_error: 'crashed',
};

interface VerdictPanelProps {
  events: JudgeEvent[];
  verdict: JudgeEvent | null;
  isJudging: boolean;
  error: string | null;
  /** pytest mode: ordinal → test id; switches to a named, expandable list */
  labels?: Record<number, TestLabel> | null;
}

/** Strip the harness's PASS/FAIL prefix; what is left is the assertion/traceback. */
function failureDetail(e: JudgeEvent): string {
  const out = (e.stdout ?? '').replace(/^(PASS|FAIL)\n?/, '').trimEnd();
  return out || e.message || (e.status === 'tle' ? 'timed out' : 'no output');
}

function NamedResults({ results, labels }: { results: JudgeEvent[]; labels: Record<number, TestLabel> }) {
  const [open, setOpen] = useState<Record<number, boolean>>({});
  // A file header above the first test of each suite file
  const rows: { e: JudgeEvent; header: string | null }[] = [];
  for (const e of results) {
    const file = labels[e.ordinal ?? 0]?.file ?? '';
    const prev = rows.length ? (labels[rows[rows.length - 1].e.ordinal ?? 0]?.file ?? '') : '';
    rows.push({ e, header: file && file !== prev ? file : null });
  }
  return (
    <ul className="border border-gray-200 rounded-lg divide-y divide-gray-100 text-xs overflow-hidden">
      {rows.map(({ e, header }) => {
        const ordinal = e.ordinal ?? 0;
        const label = labels[ordinal] ?? { file: '', name: `Test ${ordinal}` };
        const passed = e.status === 'passed';
        const expanded = open[ordinal] ?? false;
        return (
          <li key={ordinal}>
            {header && (
              <div className="px-3 py-1 bg-gray-50 font-mono text-[10px] text-gray-400 border-b border-gray-100">
                {header}
              </div>
            )}
            <button
              type="button"
              onClick={() => !passed && setOpen((o) => ({ ...o, [ordinal]: !o[ordinal] }))}
              className={`w-full flex items-center gap-2 px-3 py-1.5 text-left ${passed ? 'cursor-default' : 'hover:bg-red-50/40'}`}
            >
              {passed ? (
                <CheckCircle2 size={13} className="text-green-600 shrink-0" />
              ) : (
                <XCircle size={13} className="text-red-500 shrink-0" />
              )}
              <span className={`font-mono truncate flex-1 ${passed ? 'text-gray-700' : 'text-red-700'}`}>
                {label.name}
              </span>
              <span className="text-gray-400 shrink-0">
                {STATUS_LABELS[e.status ?? ''] ?? e.status}
                {e.runtime_ms != null && ` · ${e.runtime_ms}ms`}
              </span>
              {!passed && (expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />)}
            </button>
            {!passed && expanded && (
              <pre className="mx-3 mb-2 bg-red-50 border border-red-100 rounded-md p-2 text-[11px] leading-4 text-red-900 whitespace-pre-wrap break-words max-h-64 overflow-y-auto">
                {failureDetail(e)}
              </pre>
            )}
          </li>
        );
      })}
    </ul>
  );
}

export function VerdictPanel({ events, verdict, isJudging, error, labels }: VerdictPanelProps) {
  const caseResults = events.filter((e) => e.kind === 'case_result');
  const compileError = events.find((e) => e.kind === 'error' && e.status === 'compile_error');

  if (!isJudging && !verdict && !error && caseResults.length === 0 && !compileError) {
    return (
      <div className="text-sm text-gray-400 py-3">
        {labels ? 'Submit to run the provided tests.' : 'Submit your solution to see judge results.'}
      </div>
    );
  }

  const failed = caseResults.filter((e) => e.status !== 'passed').length;

  return (
    <div className="py-3 space-y-3">
      {/* Final verdict banner */}
      {verdict && (
        <div
          className={`rounded-lg px-4 py-3 text-sm font-semibold ${
            verdict.verdict === 'accepted'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {labels && verdict.verdict === 'wrong_answer'
            ? `${failed} failing test${failed === 1 ? '' : 's'}`
            : (VERDICT_LABELS[verdict.verdict ?? ''] ?? verdict.verdict)}
          <span className="font-normal text-xs ml-2 opacity-75">
            {verdict.passed}/{verdict.total} tests
            {verdict.runtime_ms != null && ` · ${verdict.runtime_ms}ms`}
            {verdict.memory_kb != null && ` · ${Math.round(verdict.memory_kb / 1024)}MB`}
          </span>
        </div>
      )}

      {compileError?.message && (
        <pre className="rounded-lg px-4 py-3 text-xs bg-red-50 text-red-900 border border-red-200 whitespace-pre-wrap">
          {compileError.message}
        </pre>
      )}

      {labels ? (
        caseResults.length > 0 && <NamedResults results={caseResults} labels={labels} />
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {caseResults.map((e) => (
            <span
              key={e.ordinal}
              title={`${e.status} · ${e.runtime_ms ?? '–'}ms`}
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${
                e.status === 'passed'
                  ? 'bg-green-50 text-green-700 border border-green-200'
                  : 'bg-red-50 text-red-700 border border-red-200'
              }`}
            >
              {e.status === 'passed' ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
              Test {e.ordinal}
            </span>
          ))}
        </div>
      )}
      {isJudging && (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-gray-50 text-gray-500 border border-gray-200">
          <Loader2 size={12} className="animate-spin" />
          {labels ? 'running the suite…' : 'running…'}
        </span>
      )}

      {error && error !== compileError?.message && (
        <div className="rounded-lg px-4 py-3 text-sm bg-red-50 text-red-800 border border-red-200 flex items-center gap-2">
          <Circle size={8} className="fill-current" />
          {error}
        </div>
      )}
    </div>
  );
}

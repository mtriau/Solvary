import { CheckCircle2, Circle, Loader2, XCircle } from 'lucide-react';
import type { JudgeEvent } from '@/shared/types/api';

const VERDICT_LABELS: Record<string, string> = {
  accepted: 'Accepted',
  wrong_answer: 'Wrong Answer',
  tle: 'Time Limit Exceeded',
  mle: 'Memory Limit Exceeded',
  runtime_error: 'Runtime Error',
  compile_error: 'Compile Error',
  internal_error: 'Internal Error',
};

interface VerdictPanelProps {
  events: JudgeEvent[];
  verdict: JudgeEvent | null;
  isJudging: boolean;
  error: string | null;
}

export function VerdictPanel({ events, verdict, isJudging, error }: VerdictPanelProps) {
  const caseResults = events.filter((e) => e.kind === 'case_result');

  if (!isJudging && !verdict && !error && caseResults.length === 0) {
    return (
      <div className="text-sm text-gray-400 py-3">
        Submit your solution to see judge results.
      </div>
    );
  }

  return (
    <div className="py-3 space-y-3">
      {/* Per-case chips */}
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
        {isJudging && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-gray-50 text-gray-500 border border-gray-200">
            <Loader2 size={12} className="animate-spin" />
            running…
          </span>
        )}
      </div>

      {/* Final verdict banner */}
      {verdict && (
        <div
          className={`rounded-lg px-4 py-3 text-sm font-semibold ${
            verdict.verdict === 'accepted'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {VERDICT_LABELS[verdict.verdict ?? ''] ?? verdict.verdict}
          <span className="font-normal text-xs ml-2 opacity-75">
            {verdict.passed}/{verdict.total} tests
            {verdict.runtime_ms != null && ` · ${verdict.runtime_ms}ms`}
            {verdict.memory_kb != null && ` · ${Math.round(verdict.memory_kb / 1024)}MB`}
          </span>
        </div>
      )}

      {error && (
        <div className="rounded-lg px-4 py-3 text-sm bg-red-50 text-red-800 border border-red-200 flex items-center gap-2">
          <Circle size={8} className="fill-current" />
          {error}
        </div>
      )}
    </div>
  );
}

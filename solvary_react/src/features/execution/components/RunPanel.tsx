import { Loader2 } from 'lucide-react';
import type { RunState } from '../hooks/useRunStream';

const STATUS_LABELS: Record<string, string> = {
  finished: 'Finished',
  tle: 'Time limit exceeded',
  mle: 'Memory limit exceeded',
  runtime_error: 'Runtime error',
  compile_error: 'Compile error',
  internal_error: 'Internal error',
};

interface Props {
  stdin: string;
  onStdinChange: (value: string) => void;
  canEditStdin?: boolean;
  /** pytest-mode problem: stdin is a list of test ids, output is the test transcript */
  pytestMode?: boolean;
  state: RunState;
}

/** Custom-input runner: stdin on the left, program output on the right. */
export function RunPanel({
  stdin,
  onStdinChange,
  canEditStdin = true,
  pytestMode = false,
  state,
}: Props) {
  const ok = state.status === 'finished';
  return (
    <div className="py-3 grid grid-cols-2 gap-3 text-xs">
      <div className="flex flex-col min-h-0">
        <div className="text-gray-400 mb-1">
          {pytestMode ? 'Tests to run (one id per line; blank = whole suite)' : 'Input (stdin)'}
        </div>
        <textarea
          value={stdin}
          onChange={(e) => onStdinChange(e.target.value)}
          readOnly={!canEditStdin}
          spellCheck={false}
          className="flex-1 min-h-[6rem] font-mono bg-gray-50 border border-gray-200 rounded-lg p-2 resize-none focus:outline-none focus:ring-1 focus:ring-indigo-400"
        />
      </div>
      <div className="flex flex-col min-h-0">
        <div className="flex items-center justify-between mb-1">
          <span className="text-gray-400">
            {pytestMode ? 'Test results + printed output' : 'Output'}
          </span>
          {state.isRunning ? (
            <span className="inline-flex items-center gap-1 text-gray-500">
              <Loader2 size={11} className="animate-spin" /> running…
            </span>
          ) : state.status ? (
            <span className={ok ? 'text-green-700' : 'text-red-700'}>
              {STATUS_LABELS[state.status] ?? state.status}
              {state.runtimeMs != null && ` · ${state.runtimeMs}ms`}
            </span>
          ) : null}
        </div>
        <pre
          className={`flex-1 min-h-[6rem] font-mono whitespace-pre-wrap border rounded-lg p-2 overflow-auto ${
            state.status && !ok
              ? 'bg-red-50 border-red-200 text-red-900'
              : 'bg-gray-50 border-gray-200'
          }`}
        >
          {state.error
            ? state.error
            : state.stdout || state.stderr
              ? state.stdout + (state.stderr ? `\n[stderr]\n${state.stderr}` : '')
              : state.isRunning
                ? ''
                : pytestMode
                  ? 'Run executes the listed tests against your module and shows anything you print.'
                  : 'Run your code to see its output here.'}
        </pre>
      </div>
    </div>
  );
}

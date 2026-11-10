import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { ArrowRight, ChevronDown, ChevronRight, Loader2, Lock } from 'lucide-react';
import { ProvidedTests } from '@/features/execution/components/ProvidedTests';
import type { InterviewSessionDetail, InterviewStageView } from '@/shared/types/api';
import { fmtClock } from '../lib/format';

interface Props {
  session: InterviewSessionDetail;
  onAdvance: () => void;
  onSwitch: (stage: number) => void;
  busy?: boolean;
}

const PROSE =
  'prose prose-sm max-w-none text-gray-700 [&_pre]:bg-gray-50 [&_pre]:text-gray-800 [&_pre]:border [&_pre]:border-gray-200 [&_pre]:rounded-lg [&_pre]:p-3 [&_code]:text-[13px] [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:mt-4';

function SampleTests({ stage }: { stage: InterviewStageView }) {
  if (stage.problem?.harness_files) {
    // pytest mode: the suite is the spec; parts 1..N are all in here
    return <ProvidedTests files={stage.problem.harness_files} />;
  }
  const samples = stage.problem?.sample_testcases ?? [];
  if (samples.length === 0) return null;
  return (
    <div className="mt-4 space-y-2">
      <h4 className="text-xs font-semibold text-gray-900">Sample tests</h4>
      {samples.map((tc) => (
        <div key={tc.ordinal} className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <div className="text-gray-400 mb-1">Input</div>
            <pre className="bg-gray-50 border border-gray-200 rounded-lg p-2 whitespace-pre-wrap">
              {tc.stdin}
            </pre>
          </div>
          <div>
            <div className="text-gray-400 mb-1">Output</div>
            <pre className="bg-gray-50 border border-gray-200 rounded-lg p-2 whitespace-pre-wrap">
              {tc.expected_stdout}
            </pre>
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Left column of the interview. `levels`: the unlocked statements stacked
 * (earlier ones collapsed), locked ones shown as stubs, "Next part" at the
 * bottom. `questions`: tabs across the top, one statement at a time.
 */
export function StagePanel({ session, onAdvance, onSwitch, busy }: Props) {
  const isLevels = session.template.format === 'levels';
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});
  const [confirming, setConfirming] = useState(false);
  const current = session.stages.find((s) => s.ordinal === session.current_stage);
  const lastUnlocked = session.unlocked_through >= session.stages.length;
  const active = session.status === 'active';

  if (!isLevels) {
    return (
      <div className="flex flex-col min-h-0">
        <div className="flex items-center gap-1 px-4 pt-3 pb-2 border-b border-gray-100 shrink-0 overflow-x-auto">
          {session.stages.map((s) => (
            <button
              key={s.ordinal}
              onClick={() => onSwitch(s.ordinal)}
              disabled={busy || !active}
              className={`px-2.5 py-1 rounded text-xs font-medium whitespace-nowrap ${
                s.ordinal === session.current_stage
                  ? 'bg-gray-900 text-white'
                  : 'text-gray-500 hover:bg-gray-100'
              }`}
            >
              Q{s.ordinal}
              {s.result.best_verdict === 'accepted' && <span className="ml-1 text-green-400">✓</span>}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-y-auto px-5 py-4">
          {current?.problem && (
            <>
              <h2 className="text-base font-bold text-gray-900 mb-1">{current.title}</h2>
              <div className="text-[11px] text-gray-400 mb-3">
                {current.problem.title}
                {current.budget_s && ` · suggested ${fmtClock(current.budget_s)}`}
                {current.deadline_at && ' · hard deadline'}
              </div>
              <div className={PROSE}>
                <ReactMarkdown>{current.problem.statement_md}</ReactMarkdown>
              </div>
              <SampleTests stage={current} />
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-0">
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
        {session.stages.map((s) => {
          const isCurrent = s.ordinal === session.current_stage;
          const open = isCurrent || expanded[s.ordinal];
          if (s.locked) {
            return (
              <div
                key={s.ordinal}
                className="flex items-center gap-2 px-3 py-2 rounded-lg border border-dashed border-gray-200 text-gray-400 text-sm"
              >
                <Lock size={13} />
                {s.title}
                {s.budget_s && (
                  <span className="ml-auto text-[11px]">{fmtClock(s.budget_s)} budget</span>
                )}
              </div>
            );
          }
          return (
            <div
              key={s.ordinal}
              className={`rounded-lg border ${isCurrent ? 'border-indigo-200 bg-white' : 'border-gray-200 bg-gray-50/60'}`}
            >
              <button
                onClick={() => !isCurrent && setExpanded((e) => ({ ...e, [s.ordinal]: !e[s.ordinal] }))}
                className="w-full flex items-center gap-2 px-3 py-2 text-left"
              >
                {isCurrent ? null : open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                <span className={`text-sm font-semibold ${isCurrent ? 'text-gray-900' : 'text-gray-600'}`}>
                  {s.title}
                </span>
                {s.result.submissions > 0 && (
                  <span
                    className={`text-[11px] ${s.result.best_verdict === 'accepted' ? 'text-green-600' : 'text-red-500'}`}
                  >
                    {s.result.best_passed}/{s.result.best_total}
                  </span>
                )}
                {isCurrent && (
                  <span className="ml-auto text-[11px] text-indigo-600 font-medium">current</span>
                )}
              </button>
              {open && s.problem && (
                <div className="px-3 pb-3">
                  <div className={PROSE}>
                    <ReactMarkdown>{s.problem.statement_md}</ReactMarkdown>
                  </div>
                  {(isCurrent || !s.problem.harness_files) && <SampleTests stage={s} />}
                </div>
              )}
            </div>
          );
        })}
      </div>
      {active && !lastUnlocked && (
        <div className="border-t border-gray-200 px-4 py-3 shrink-0">
          {confirming ? (
            <div className="text-xs space-y-2">
              <p className="text-gray-700">
                {current?.result.best_verdict === 'accepted'
                  ? 'Reveal the next part?'
                  : 'This part is not accepted yet. Moving on is allowed — and often the right call. Reveal the next part?'}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setConfirming(false);
                    onAdvance();
                  }}
                  disabled={busy}
                  className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50"
                >
                  Yes, next part
                </button>
                <button
                  onClick={() => setConfirming(false)}
                  className="px-3 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Stay
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setConfirming(true)}
              disabled={busy}
              className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              {busy ? <Loader2 size={14} className="animate-spin" /> : <ArrowRight size={14} />}
              Next part
            </button>
          )}
        </div>
      )}
    </div>
  );
}

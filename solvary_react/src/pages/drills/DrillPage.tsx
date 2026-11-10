import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import Editor, { type OnMount } from '@monaco-editor/react';
import PreludeHint from '@/features/execution/components/PreludeHint';
import ReactMarkdown from 'react-markdown';
import { useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Check,
  Eye,
  Loader2,
  Play,
  RotateCcw,
  Send,
} from 'lucide-react';
import { DRILL_KEYS, useDrill, useDrills } from '@/features/drills/hooks/useDrills';
import { useJudgeStream } from '@/features/execution/hooks/useJudgeStream';
import { useRunStream } from '@/features/execution/hooks/useRunStream';
import { VerdictPanel } from '@/features/execution/components/VerdictPanel';
import { RunPanel } from '@/features/execution/components/RunPanel';
import { ProvidedTests } from '@/features/execution/components/ProvidedTests';
import { testLabels } from '@/features/execution/lib/test-labels';
import { AssistPanel } from '@/features/assist/components/AssistPanel';
import { summarizeVerdict } from '@/features/execution/lib/verdict-summary';

const PROSE =
  'prose prose-sm max-w-none text-gray-700 [&_pre]:bg-gray-50 [&_pre]:text-gray-800 [&_pre]:border [&_pre]:border-gray-200 [&_pre]:rounded-lg [&_pre]:p-3 [&_code]:text-[13px] [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:mt-4';

type BottomTab = 'judge' | 'run' | 'assist';

const TABS: { id: BottomTab; label: string }[] = [
  { id: 'judge', label: 'Tests' },
  { id: 'run', label: 'Run' },
  { id: 'assist', label: 'Ask AI' },
];

export default function DrillPage() {
  const { slug = '' } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: drill, isLoading } = useDrill(slug);
  const { data: all } = useDrills();
  const [code, setCode] = useState('');
  const [stdin, setStdin] = useState('');
  const [tab, setTab] = useState<BottomTab>('judge');
  const [revealed, setRevealed] = useState(false);
  const { submit, events, verdict, isJudging, error, reset } = useJudgeStream();
  const runState = useRunStream();
  const submitRef = useRef<() => void>(() => {});

  // A new drill: fresh editor, hidden solution, clean panels.
  useEffect(() => {
    if (drill) {
      setCode(drill.starter_code.python ?? '');
      setRevealed(false);
      setTab('judge');
      setStdin('');
      reset();
      runState.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [drill?.id]);

  // A verdict changes progress everywhere; an accept opens the solution.
  useEffect(() => {
    if (!verdict) return;
    queryClient.invalidateQueries({ queryKey: DRILL_KEYS.all });
    queryClient.invalidateQueries({ queryKey: DRILL_KEYS.one(slug) });
    if (verdict.verdict === 'accepted') setRevealed(true);
  }, [verdict, queryClient, slug]);

  const onSubmit = () => {
    if (!drill || isJudging || !code.trim()) return;
    setTab('judge');
    void submit(drill.id, 'python', code);
  };
  submitRef.current = onSubmit;

  const onRun = () => {
    if (!drill) return;
    setTab('run');
    void runState.run('python', code, stdin, undefined, drill.id);
  };

  const onMount: OnMount = (editor, monaco) => {
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => submitRef.current());
    editor.focus();
  };

  if (isLoading || !drill) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="animate-spin text-gray-400" size={28} />
      </div>
    );
  }

  const accepted = verdict?.verdict === 'accepted';
  const solved = drill.solved || accepted;
  const nextSlug = drill.next_unsolved_slug ?? drill.next_slug;
  const topicDrills = all?.topics.find((t) => t.slug === drill.topic)?.drills ?? [];
  const showSolution = revealed || drill.solved;

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Top strip: context + navigation */}
      <div className="h-11 border-b border-gray-200 flex items-center gap-4 px-4 shrink-0 bg-white">
        <Link
          to="/drills"
          className="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600"
        >
          <ArrowLeft size={12} /> All drills
        </Link>
        <span className="text-xs text-gray-500">
          {drill.topic_title} · {drill.position} of {drill.topic_total}
        </span>
        {topicDrills.length > 0 && (
          <div className="flex items-center gap-1" title="This topic's drills">
            {topicDrills.map((d) => (
              <Link
                key={d.id}
                to={`/drills/${d.slug}`}
                title={d.title}
                className={`h-2.5 w-2.5 rounded-full border ${
                  d.slug === drill.slug
                    ? 'border-gray-900 ring-2 ring-gray-900/20'
                    : 'border-transparent'
                } ${d.solved ? 'bg-green-500' : 'bg-gray-200'}`}
              />
            ))}
          </div>
        )}
        <span className="flex-1" />
        {drill.prev_slug && (
          <Link
            to={`/drills/${drill.prev_slug}`}
            className="text-xs text-gray-500 hover:text-gray-900"
          >
            Previous
          </Link>
        )}
        {nextSlug ? (
          <Link
            to={`/drills/${nextSlug}`}
            className={`inline-flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-medium ${
              solved
                ? 'bg-green-600 text-white hover:bg-green-700'
                : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            Next drill <ArrowRight size={12} />
          </Link>
        ) : (
          <span className="text-xs text-gray-400">Last drill</span>
        )}
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Left: statement, tests, solution */}
        <div className="w-[42%] border-r border-gray-200 overflow-y-auto">
          <div className="px-6 py-5 space-y-5">
            <div className="flex items-start justify-between gap-3">
              <h1 className="text-xl font-bold text-gray-900">{drill.title}</h1>
              {solved && (
                <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 border border-green-200 rounded-full px-2 py-0.5 shrink-0">
                  <Check size={12} /> Solved
                </span>
              )}
            </div>

            <div className={PROSE}>
              <ReactMarkdown>{drill.statement_md}</ReactMarkdown>
            </div>

            {accepted && (
              <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-900">
                <div className="font-semibold">Tests green.</div>
                <div className="text-green-800 mt-0.5">
                  Now compare with the idiomatic solution below. If yours is longer, work out which
                  idiom you skipped.
                </div>
                {nextSlug && (
                  <button
                    onClick={() => navigate(`/drills/${nextSlug}`)}
                    className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-green-800 hover:underline"
                  >
                    Next drill <ArrowRight size={12} />
                  </button>
                )}
              </div>
            )}

            {drill.editorial_md && (
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-800">
                    <BookOpen size={13} /> Idiomatic solution
                  </div>
                  {!showSolution && (
                    <button
                      onClick={() => setRevealed(true)}
                      className="inline-flex items-center gap-1 text-xs font-medium text-emerald-800 hover:underline"
                    >
                      <Eye size={12} /> Reveal
                    </button>
                  )}
                </div>
                {showSolution ? (
                  <div className={`${PROSE} text-emerald-900 mt-2`}>
                    <ReactMarkdown>{drill.editorial_md}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-xs text-emerald-700 mt-1">
                    Hidden until your tests pass. Reveal it if you are stuck, then still write it
                    yourself.
                  </p>
                )}
              </div>
            )}

            {drill.harness_files && <ProvidedTests files={drill.harness_files} />}
          </div>
        </div>

        {/* Right: editor + panels */}
        <div className="flex-1 flex flex-col min-w-0">
          <div className="h-11 flex items-center justify-between px-4 border-b border-gray-200 shrink-0">
            <span className="text-xs text-gray-400 font-mono">
              {drill.harness_files ? Object.keys(drill.harness_files)[0]?.replace(/^test_/, '') : 'python'}
              <span className="text-gray-300"> · Ctrl+Enter submits</span>
            </span>
            <div className="flex items-center gap-2">
              <PreludeHint />
              <button
                onClick={() => setCode(drill.starter_code.python ?? '')}
                title="Back to the starter code"
                className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-gray-500 rounded-lg text-xs font-medium hover:bg-gray-100"
              >
                <RotateCcw size={13} /> Reset
              </button>
              <button
                onClick={onRun}
                disabled={runState.isRunning || !code.trim()}
                title="Run the provided tests and show printed output"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-gray-700 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
              >
                {runState.isRunning ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Play size={14} />
                )}
                Run
              </button>
              <button
                onClick={onSubmit}
                disabled={isJudging || !code.trim()}
                title="Judge against the provided tests (Ctrl+Enter)"
                className="inline-flex items-center gap-1.5 px-4 py-1.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
              >
                {isJudging ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                {isJudging ? 'Judging…' : 'Submit'}
              </button>
            </div>
          </div>

          <div className="flex-1 min-h-0">
            <Editor
              language="python"
              value={code}
              onChange={(v) => setCode(v ?? '')}
              onMount={onMount}
              options={{
                minimap: { enabled: false },
                fontSize: 13,
                scrollBeyondLastLine: false,
                padding: { top: 12 },
              }}
            />
          </div>

          <div className="border-t border-gray-200 shrink-0 flex flex-col max-h-80">
            <div className="flex items-center gap-1 px-4 pt-2 shrink-0">
              {TABS.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                    tab === t.id ? 'bg-gray-900 text-white' : 'text-gray-500 hover:bg-gray-100'
                  }`}
                >
                  {t.label}
                  {t.id === 'judge' && isJudging && (
                    <Loader2 size={10} className="inline ml-1 animate-spin" />
                  )}
                </button>
              ))}
            </div>
            <div className="px-4 overflow-y-auto">
              {tab === 'judge' && (
                <VerdictPanel
                  events={events}
                  verdict={verdict}
                  isJudging={isJudging}
                  error={error}
                  labels={testLabels(drill)}
                />
              )}
              {tab === 'run' && (
                <RunPanel stdin={stdin} onStdinChange={setStdin} pytestMode state={runState} />
              )}
              {tab === 'assist' && (
                <AssistPanel
                  problemId={drill.id}
                  code={code}
                  language="python"
                  verdictSummary={summarizeVerdict(verdict, events)}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

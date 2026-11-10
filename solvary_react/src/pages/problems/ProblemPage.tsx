import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import ReactMarkdown from 'react-markdown';
import { useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, ChevronDown, ChevronRight, Loader2, Play, Send, Users } from 'lucide-react';
import { SubmissionCode } from '@/features/execution/components/SubmissionCode';
import { useMySubmissions, useProblem } from '@/features/problems/hooks/useProblems';
import { useJudgeStream } from '@/features/execution/hooks/useJudgeStream';
import { useRunStream } from '@/features/execution/hooks/useRunStream';
import { VerdictPanel } from '@/features/execution/components/VerdictPanel';
import { RunPanel } from '@/features/execution/components/RunPanel';
import { ProvidedTests } from '@/features/execution/components/ProvidedTests';
import { testLabels } from '@/features/execution/lib/test-labels';
import { AssistPanel } from '@/features/assist/components/AssistPanel';
import { summarizeVerdict } from '@/features/execution/lib/verdict-summary';
import { createWorkspace } from '@/shared/lib/api';

const LANGUAGES = ['python', 'javascript'] as const;

const VERDICT_COLORS: Record<string, string> = {
  accepted: 'text-green-600',
  queued: 'text-gray-400',
  running: 'text-gray-400',
};

type BottomTab = 'judge' | 'run' | 'assist';

const TABS: { id: BottomTab; label: string }[] = [
  { id: 'judge', label: 'Judge' },
  { id: 'run', label: 'Run' },
  { id: 'assist', label: 'Ask AI' },
];

export default function ProblemPage() {
  const { slug = '' } = useParams();
  const { data: problem, isLoading } = useProblem(slug);
  const [language, setLanguage] = useState<string>('python');
  const [code, setCode] = useState('');
  const [stdin, setStdin] = useState('');
  const [tab, setTab] = useState<BottomTab>('judge');
  const { submit, events, verdict, isJudging, error, submissionId } = useJudgeStream();
  const runState = useRunStream();
  const submissions = useMySubmissions(problem?.id);
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [creatingWs, setCreatingWs] = useState(false);
  const [openSubmission, setOpenSubmission] = useState<string | null>(null);
  // Code to put in the editor instead of the starter when a language switch
  // is caused by "Load into editor" on a past submission.
  const pendingCode = useRef<string | null>(null);

  const solveCollaboratively = async () => {
    if (!problem) return;
    setCreatingWs(true);
    try {
      const ws = await createWorkspace({ problem_id: problem.id, language });
      navigate(`/workspaces/${ws.id}`);
    } finally {
      setCreatingWs(false);
    }
  };

  // Load starter code when the problem (or language) changes — but never
  // clobber user edits mid-session
  useEffect(() => {
    if (problem) {
      const restored = pendingCode.current;
      pendingCode.current = null;
      setCode(restored ?? problem.starter_code[language] ?? '');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [problem?.id, language]);

  // Default the Run input to the first sample's stdin
  useEffect(() => {
    if (problem) setStdin(problem.sample_testcases[0]?.stdin ?? '');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [problem?.id]);

  // Refresh the submissions list once a verdict lands
  useEffect(() => {
    if (verdict) {
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
    }
  }, [verdict, queryClient]);

  if (isLoading || !problem) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="animate-spin text-gray-400" size={28} />
      </div>
    );
  }

  const onRun = () => {
    setTab('run');
    void runState.run(
      language,
      code,
      stdin,
      undefined,
      problem.judge_mode === 'pytest' ? problem.id : undefined,
    );
  };
  const onSubmit = () => {
    setTab('judge');
    void submit(problem.id, language, code);
  };

  return (
    <div className="h-full flex overflow-hidden">
      {/* Left: statement + submissions */}
      <div className="w-[45%] border-r border-gray-200 overflow-y-auto">
        <div className="px-6 py-5">
          <Link
            to="/problems"
            className="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 mb-3"
          >
            <ArrowLeft size={12} />
            All problems
          </Link>
          <h1 className="text-xl font-bold text-gray-900 mb-4">{problem.title}</h1>

          <div className="prose prose-sm max-w-none text-gray-700 [&_pre]:bg-gray-50 [&_pre]:text-gray-800 [&_pre]:border [&_pre]:border-gray-200 [&_pre]:rounded-lg [&_pre]:p-3 [&_code]:text-[13px] [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:mt-4">
            <ReactMarkdown>{problem.statement_md}</ReactMarkdown>
          </div>

          {problem.harness_files && <ProvidedTests files={problem.harness_files} />}

          {!problem.harness_files && problem.sample_testcases.length > 0 && (
            <div className="mt-6 space-y-3">
              <h3 className="text-sm font-semibold text-gray-900">Sample tests</h3>
              {problem.sample_testcases.map((tc) => (
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
          )}

          {/* My submissions */}
          <div className="mt-8">
            <h3 className="text-sm font-semibold text-gray-900 mb-2">My submissions</h3>
            {submissions.data?.items.length ? (
              <ul className="divide-y divide-gray-100 border border-gray-200 rounded-lg text-xs">
                {submissions.data.items.slice(0, 10).map((s) => {
                  const isOpen = openSubmission === s.id;
                  return (
                    <li key={s.id}>
                      <button
                        onClick={() => setOpenSubmission(isOpen ? null : s.id)}
                        title={isOpen ? 'Hide code' : 'View the code of this submission'}
                        className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-gray-50"
                      >
                        {isOpen ? (
                          <ChevronDown size={12} className="text-gray-400 shrink-0" />
                        ) : (
                          <ChevronRight size={12} className="text-gray-400 shrink-0" />
                        )}
                        <span
                          className={`font-medium capitalize flex-1 ${VERDICT_COLORS[s.verdict] ?? 'text-red-600'}`}
                        >
                          {s.verdict.replace('_', ' ')}
                        </span>
                        <span className="text-gray-400">
                          {s.passed}/{s.total} · {s.language} ·{' '}
                          {new Date(s.created_at).toLocaleTimeString()}
                        </span>
                      </button>
                      {isOpen && (
                        <div className="px-3 pb-3">
                          <SubmissionCode
                            submissionId={s.id}
                            action={{
                              label: 'Load into editor',
                              onClick: (code) => {
                                if (s.language !== language) pendingCode.current = code;
                                setLanguage(s.language);
                                setCode(code);
                              },
                            }}
                          />
                        </div>
                      )}
                    </li>
                  );
                })}
              </ul>
            ) : (
              <p className="text-xs text-gray-400">No submissions yet.</p>
            )}
          </div>
        </div>
      </div>

      {/* Right: editor + bottom panel (judge / run / ask AI) */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="h-11 flex items-center justify-between px-4 border-b border-gray-200 shrink-0">
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-2 py-1 bg-white focus:outline-none"
          >
            {LANGUAGES.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
          <div className="flex items-center gap-2">
            <button
              onClick={solveCollaboratively}
              disabled={creatingWs}
              title="Create a shared workspace bound to this problem — invite others and solve together"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-gray-700 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              {creatingWs ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Users size={14} />
              )}
              Solve together
            </button>
            <button
              onClick={onRun}
              disabled={runState.isRunning || !code.trim()}
              title="Run against the input below — no judging, nothing recorded"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-gray-700 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50 transition-colors"
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
              title="Judge against all test cases"
              className="inline-flex items-center gap-1.5 px-4 py-1.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {isJudging ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Send size={14} />
              )}
              {isJudging ? 'Judging…' : 'Submit'}
            </button>
          </div>
        </div>

        <div className="flex-1 min-h-0">
          <Editor
            language={language}
            value={code}
            onChange={(v) => setCode(v ?? '')}
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
                  tab === t.id
                    ? 'bg-gray-900 text-white'
                    : 'text-gray-500 hover:bg-gray-100'
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
              <>
                <VerdictPanel
                  events={events}
                  verdict={verdict}
                  isJudging={isJudging}
                  error={error}
                  labels={testLabels(problem)}
                />
                {submissionId && (
                  <p className="text-[10px] text-gray-300 pb-2">{submissionId}</p>
                )}
              </>
            )}
            {tab === 'run' && (
              <RunPanel
                stdin={stdin}
                onStdinChange={setStdin}
                pytestMode={problem.judge_mode === 'pytest'}
                state={runState}
              />
            )}
            {tab === 'assist' && (
              <AssistPanel
                problemId={problem.id}
                code={code}
                language={language}
                verdictSummary={summarizeVerdict(verdict, events)}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

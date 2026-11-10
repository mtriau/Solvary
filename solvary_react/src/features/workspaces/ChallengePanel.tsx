/**
 * The M4 payoff: a workspace bound to a Problem gets a statement panel, an
 * ad-hoc runner and a shared judge. When any editor submits, the submission
 * id is broadcast via Yjs awareness ("judging" field) and every member —
 * viewers included — follows the same SSE verdict stream (the server
 * authorizes workspace members on workspace-tagged submissions).
 */

import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import { Loader2, Play, Send } from 'lucide-react';
import { useJudgeStream } from '@/features/execution/hooks/useJudgeStream';
import { useRunStream } from '@/features/execution/hooks/useRunStream';
import { VerdictPanel } from '@/features/execution/components/VerdictPanel';
import { RunPanel } from '@/features/execution/components/RunPanel';
import { testLabels } from '@/features/execution/lib/test-labels';
import type { CollabState } from '@/features/collaboration/useCollab';
import { fetchProblem } from '@/shared/lib/api';
import type { Workspace } from '@/shared/types/api';
import type * as Y from 'yjs';

interface Props {
  workspace: Workspace;
  collab: CollabState | null;
  activeFileId: string | null;
}

type Pane = 'judge' | 'run';

export default function ChallengePanel({ workspace, collab, activeFileId }: Props) {
  const { submit, follow, events, verdict, isJudging, error } = useJudgeStream();
  const runState = useRunStream();
  const [stdin, setStdin] = useState('');
  const [pane, setPane] = useState<Pane>('judge');
  const lastHandledRef = useRef<string | null>(null);

  const { data: problem } = useQuery({
    queryKey: ['problem', workspace.problem_slug],
    queryFn: () => fetchProblem(workspace.problem_slug!),
    enabled: !!workspace.problem_slug,
  });

  useEffect(() => {
    if (problem) setStdin(problem.sample_testcases[0]?.stdin ?? '');
  }, [problem]);

  const isViewer = workspace.my_role === 'viewer';

  // Follow peers' submissions: awareness carries {judging: {submissionId, at}}
  useEffect(() => {
    if (!collab) return;
    const awareness = collab.provider.awareness;

    const onChange = () => {
      let latest: { submissionId: string; at: number } | null = null;
      let fromSelf = false;
      awareness.getStates().forEach((state, clientId) => {
        const judging = state.judging as { submissionId: string; at: number } | undefined;
        if (judging && (!latest || judging.at > latest.at)) {
          latest = judging;
          fromSelf = clientId === awareness.clientID;
        }
      });
      if (!latest) return;
      const { submissionId } = latest;
      if (submissionId === lastHandledRef.current) return;
      lastHandledRef.current = submissionId;
      if (!fromSelf) {
        setPane('judge');
        follow(submissionId); // submitter already streams
      }
    };

    awareness.on('change', onChange);
    onChange(); // catch a judging state that predates this mount
    return () => awareness.off('change', onChange);
  }, [collab, follow]);

  const currentCode = (): string | null => {
    if (!collab || !activeFileId) return null;
    const code = collab.doc.getMap<Y.Text>('files').get(activeFileId)?.toString() ?? '';
    return code.trim() ? code : null;
  };

  const onRun = () => {
    const code = currentCode();
    if (!code) return;
    setPane('run');
    void runState.run(
      workspace.language,
      code,
      stdin,
      workspace.id,
      problem?.judge_mode === 'pytest' ? problem.id : undefined,
    );
  };

  const onSubmit = async () => {
    const code = currentCode();
    if (!code || !collab || !workspace.problem_id) return;
    setPane('judge');

    // CRDT convergence: any member's buffer is what everyone sees — send it
    const submissionId = await submit(
      workspace.problem_id,
      workspace.language,
      code,
      workspace.id,
    );
    if (submissionId) {
      lastHandledRef.current = submissionId;
      collab.provider.awareness.setLocalStateField('judging', {
        submissionId,
        at: Date.now(),
      });
    }
  };

  const showResults =
    pane === 'run'
      ? runState.isRunning || runState.status || runState.error
      : events.length > 0 || isJudging || error;

  return (
    <div className="w-[26rem] border-l border-gray-200 flex flex-col min-h-0 bg-white">
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 shrink-0 gap-2">
        <span className="text-sm font-semibold text-gray-900 truncate">
          {workspace.problem_title ?? 'Challenge'}
        </span>
        <div className="flex items-center gap-1.5 shrink-0">
          <button
            onClick={onRun}
            disabled={runState.isRunning || isViewer || !activeFileId}
            title={isViewer ? 'Viewers cannot run code' : 'Run the current buffer on custom input'}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-gray-700 border border-gray-300 rounded-lg text-xs font-medium hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            {runState.isRunning ? (
              <Loader2 size={13} className="animate-spin" />
            ) : (
              <Play size={13} />
            )}
            Run
          </button>
          <button
            onClick={onSubmit}
            disabled={isJudging || isViewer || !activeFileId}
            title={isViewer ? 'Viewers cannot submit' : 'Judge the current buffer'}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {isJudging ? (
              <Loader2 size={13} className="animate-spin" />
            ) : (
              <Send size={13} />
            )}
            {isJudging ? 'Judging…' : 'Submit'}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 prose prose-sm max-w-none">
        {problem ? (
          <ReactMarkdown>{problem.statement_md}</ReactMarkdown>
        ) : (
          <p className="text-gray-400 text-sm">Loading statement…</p>
        )}
      </div>

      {showResults && (
        <div className="border-t border-gray-200 max-h-80 overflow-y-auto shrink-0 px-4">
          <div className="flex items-center gap-1 pt-2">
            {(['judge', 'run'] as Pane[]).map((p) => (
              <button
                key={p}
                onClick={() => setPane(p)}
                className={`px-2 py-0.5 rounded text-[11px] font-medium ${
                  pane === p ? 'bg-gray-900 text-white' : 'text-gray-500 hover:bg-gray-100'
                }`}
              >
                {p === 'judge' ? 'Judge' : 'Run'}
              </button>
            ))}
          </div>
          {pane === 'judge' ? (
            <VerdictPanel
              events={events}
              verdict={verdict}
              isJudging={isJudging}
              error={error}
              labels={testLabels(problem)}
            />
          ) : (
            <RunPanel
              stdin={stdin}
              onStdinChange={setStdin}
              canEditStdin={!isViewer}
              pytestMode={problem?.judge_mode === 'pytest'}
              state={runState}
            />
          )}
        </div>
      )}
    </div>
  );
}

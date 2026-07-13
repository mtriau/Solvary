/**
 * The M4 payoff: a workspace bound to a Problem gets a statement panel and
 * a shared judge. When any editor submits, the submission id is broadcast
 * via Yjs awareness ("judging" field) and every member — viewers included —
 * follows the same SSE verdict stream (the server authorizes workspace
 * members on workspace-tagged submissions).
 */

import { useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import { Loader2, Play } from 'lucide-react';
import { useJudgeStream } from '@/features/execution/hooks/useJudgeStream';
import { VerdictPanel } from '@/features/execution/components/VerdictPanel';
import type { CollabState } from '@/features/collaboration/useCollab';
import { fetchProblem } from '@/shared/lib/api';
import type { Workspace } from '@/shared/types/api';
import type * as Y from 'yjs';

interface Props {
  workspace: Workspace;
  collab: CollabState | null;
  activeFileId: string | null;
}

export default function ChallengePanel({ workspace, collab, activeFileId }: Props) {
  const { submit, follow, events, verdict, isJudging, error } = useJudgeStream();
  const lastHandledRef = useRef<string | null>(null);

  const { data: problem } = useQuery({
    queryKey: ['problem', workspace.problem_slug],
    queryFn: () => fetchProblem(workspace.problem_slug!),
    enabled: !!workspace.problem_slug,
  });

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
      if (!fromSelf) follow(submissionId); // submitter already streams
    };

    awareness.on('change', onChange);
    onChange(); // catch a judging state that predates this mount
    return () => awareness.off('change', onChange);
  }, [collab, follow]);

  const onSubmit = async () => {
    if (!collab || !activeFileId || !workspace.problem_id) return;
    const files = collab.doc.getMap<Y.Text>('files');
    const code = files.get(activeFileId)?.toString() ?? '';
    if (!code.trim()) return;

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

  return (
    <div className="w-[26rem] border-l border-gray-200 flex flex-col min-h-0 bg-white">
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 shrink-0">
        <span className="text-sm font-semibold text-gray-900 truncate">
          {workspace.problem_title ?? 'Challenge'}
        </span>
        <button
          onClick={onSubmit}
          disabled={isJudging || isViewer || !activeFileId}
          title={isViewer ? 'Viewers cannot submit' : 'Judge the current buffer'}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {isJudging ? (
            <Loader2 size={13} className="animate-spin" />
          ) : (
            <Play size={13} />
          )}
          {isJudging ? 'Judging…' : 'Submit'}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 prose prose-sm max-w-none">
        {problem ? (
          <ReactMarkdown>{problem.statement_md}</ReactMarkdown>
        ) : (
          <p className="text-gray-400 text-sm">Loading statement…</p>
        )}
      </div>

      {(events.length > 0 || isJudging || error) && (
        <div className="border-t border-gray-200 max-h-72 overflow-y-auto shrink-0">
          <VerdictPanel
            events={events}
            verdict={verdict}
            isJudging={isJudging}
            error={error}
          />
        </div>
      )}
    </div>
  );
}

import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, ArrowRight, Loader2, Play, Send, X } from 'lucide-react';
import type * as Y from 'yjs';
import { useAuth } from '@/app/providers/AuthProvider';
import CollabEditor from '@/features/collaboration/CollabEditor';
import PreludeHint from '@/features/execution/components/PreludeHint';
import { useCollab } from '@/features/collaboration/useCollab';
import { VerdictPanel } from '@/features/execution/components/VerdictPanel';
import { RunPanel } from '@/features/execution/components/RunPanel';
import { useJudgeStream } from '@/features/execution/hooks/useJudgeStream';
import { useRunStream } from '@/features/execution/hooks/useRunStream';
import { testLabels } from '@/features/execution/lib/test-labels';
import { StagePanel } from '@/features/interviews/components/StagePanel';
import { TimerBar } from '@/features/interviews/components/TimerBar';
import { useCountdown } from '@/features/interviews/hooks/useCountdown';
import {
  INTERVIEW_KEYS,
  useInterviewSession,
} from '@/features/interviews/hooks/useInterviewSession';
import { fmtClock } from '@/features/interviews/lib/format';
import { ResizeHandle } from '@/shared/components/ResizeHandle';
import { usePersistedNumber } from '@/shared/hooks/usePersistedNumber';
import { ApiError } from '@/shared/lib/api-client';
import { fetchFiles } from '@/shared/lib/api';
import type { InterviewSessionDetail } from '@/shared/types/api';

type Pane = 'judge' | 'run';

function detailOf(err: unknown): string {
  if (err instanceof ApiError) {
    try {
      return (JSON.parse(err.body) as { detail?: string }).detail ?? err.message;
    } catch {
      return err.message;
    }
  }
  return (err as Error).message;
}

/** Mounted once the session is loaded — the collab socket needs the workspace id. */
function Workbench({ session }: { session: InterviewSessionDetail }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { advance, switchStage, finish, abandon, refetch } = useInterviewSession(session.id);
  const countdown = useCountdown(session.ends_at, session.server_time, () => {
    void refetch(); // the server finalizes lazily; the refetch flips status → review
  });

  const { collab, synced, connected } = useCollab(
    session.workspace_id ?? '',
    user ?? { id: 'anon', name: 'anon' },
    () => {},
  );
  const { data: files = [] } = useQuery({
    queryKey: ['ws-files', session.workspace_id],
    queryFn: () => fetchFiles(session.workspace_id!),
    enabled: !!session.workspace_id,
  });

  const { submit, events, verdict, isJudging, error } = useJudgeStream();
  const runState = useRunStream();
  const [pane, setPane] = useState<Pane>('judge');
  const [stdin, setStdin] = useState('');
  const [actionError, setActionError] = useState<string | null>(null);
  const [dismissedNudge, setDismissedNudge] = useState<number | null>(null);
  // Draggable splitters (remembered across sessions)
  const [leftWidth, setLeftWidth, resetLeftWidth] = usePersistedNumber(
    'interview.leftWidth',
    Math.round(window.innerWidth * 0.42),
    260,
    Math.max(400, window.innerWidth - 420),
  );
  const [consoleHeight, setConsoleHeight, resetConsoleHeight] = usePersistedNumber(
    'interview.consoleHeight',
    288,
    120,
    Math.max(240, window.innerHeight - 260),
  );

  const isLevels = session.template.format === 'levels';
  const active = session.status === 'active';
  const stage = session.stages.find((s) => s.ordinal === session.current_stage);
  const fileId = stage?.file_id ?? null;
  const labels = useMemo(() => testLabels(stage?.problem), [stage?.problem]);
  const filePath = files.find((f) => f.id === fileId)?.path ?? (isLevels ? 'main' : `q${session.current_stage}`);

  // Stage elapsed from the server timeline, on the server-corrected clock
  const stageElapsedS = useMemo(() => {
    const last = session.timeline[session.timeline.length - 1];
    if (!last) return 0;
    return Math.max(0, Math.floor((countdown.nowMs - new Date(last.at).getTime()) / 1000));
  }, [session.timeline, countdown.nowMs]);

  useEffect(() => {
    if (stage?.problem) setStdin(stage.problem.sample_testcases[0]?.stdin ?? '');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage?.problem?.id]);

  // A verdict changes the derived results → refresh the payload
  useEffect(() => {
    if (verdict) queryClient.invalidateQueries({ queryKey: INTERVIEW_KEYS.session(session.id) });
  }, [verdict, queryClient, session.id]);

  useEffect(() => {
    if (!active) navigate(`/interviews/sessions/${session.id}/review`, { replace: true });
  }, [active, navigate, session.id]);

  const currentCode = (): string | null => {
    if (!collab || !fileId) return null;
    const code = collab.doc.getMap<Y.Text>('files').get(fileId)?.toString() ?? '';
    return code.trim() ? code : null;
  };

  const onRun = () => {
    const code = currentCode();
    if (!code) return;
    setPane('run');
    void runState.run(
      session.language,
      code,
      stdin,
      session.workspace_id ?? undefined,
      stage?.problem?.judge_mode === 'pytest' ? stage.problem.id : undefined,
    );
  };
  const onSubmit = () => {
    const code = currentCode();
    if (!code || !stage?.problem) return;
    setPane('judge');
    void submit(stage.problem.id, session.language, code, session.workspace_id ?? undefined, session.id);
  };
  const act = async (fn: () => Promise<unknown>) => {
    setActionError(null);
    try {
      await fn();
    } catch (err) {
      setActionError(detailOf(err));
      void refetch();
    }
  };
  const busy = advance.isPending || switchStage.isPending || finish.isPending || abandon.isPending;

  // ── pacing nudges ──
  const budget = stage?.budget_s ?? null;
  const overBudget = budget != null && stageElapsedS > budget;
  const lockedBudgetS = session.stages
    .filter((s) => s.ordinal > session.current_stage)
    .reduce((acc, s) => acc + (s.budget_s ?? 0), 0);
  const pointOfNoReturn = lockedBudgetS > 0 && countdown.remainingS < lockedBudgetS;
  const partsLeft = session.stages.length - session.current_stage;
  const showNudge =
    active && overBudget && partsLeft > 0 && (pointOfNoReturn || dismissedNudge !== session.current_stage);

  const showResults =
    pane === 'run'
      ? runState.isRunning || runState.status || runState.error
      : events.length > 0 || isJudging || error;

  return (
    <div className="h-full flex flex-col">
      <TimerBar
        session={session}
        countdown={countdown}
        stageElapsedS={stageElapsedS}
        busy={busy}
        onFinish={() => {
          if (window.confirm('Stop the clock and finish the interview now?')) {
            void act(() => finish.mutateAsync());
          }
        }}
        onAbandon={() => {
          if (window.confirm('Abandon this interview? It will not be scored.')) {
            void act(() => abandon.mutateAsync());
          }
        }}
      />
      {(actionError || showNudge) && (
        <div
          className={`px-4 py-2 text-xs flex items-center gap-2 border-b ${
            actionError
              ? 'bg-red-50 border-red-200 text-red-800'
              : pointOfNoReturn
                ? 'bg-red-50 border-red-200 text-red-800'
                : 'bg-amber-50 border-amber-200 text-amber-800'
          }`}
        >
          <AlertTriangle size={13} />
          {actionError ? (
            <span className="flex-1">{actionError}</span>
          ) : (
            <span className="flex-1">
              {pointOfNoReturn
                ? `Less time left (${fmtClock(countdown.remainingS)}) than the remaining parts' budgets (${fmtClock(lockedBudgetS)}). `
                : `Budget for ${stage?.title} is up (${fmtClock(stageElapsedS)} / ${fmtClock(budget ?? 0)}). `}
              {partsLeft} part{partsLeft === 1 ? '' : 's'} and {fmtClock(countdown.remainingS)} left.
              {isLevels ? ' Move on?' : ' Consider switching questions.'}
            </span>
          )}
          {!actionError && isLevels && (
            <button
              onClick={() => void act(() => advance.mutateAsync())}
              disabled={busy}
              className="inline-flex items-center gap-1 px-2 py-1 rounded bg-white border border-current font-medium hover:bg-amber-100 disabled:opacity-50"
            >
              Next part <ArrowRight size={11} />
            </button>
          )}
          <button
            onClick={() => (actionError ? setActionError(null) : setDismissedNudge(session.current_stage))}
            className="p-1 rounded hover:bg-black/5"
            title="Dismiss"
          >
            <X size={12} />
          </button>
        </div>
      )}

      <div className="flex-1 flex min-h-0">
        <div
          className="bg-white flex flex-col min-h-0 shrink-0"
          style={{ width: leftWidth }}
        >
          <StagePanel
            session={session}
            busy={busy}
            onAdvance={() => void act(() => advance.mutateAsync())}
            onSwitch={(n) => void act(() => switchStage.mutateAsync(n))}
          />
        </div>
        <ResizeHandle
          direction="col"
          onDrag={(dx) => setLeftWidth((w) => w + dx)}
          onDoubleClick={resetLeftWidth}
        />

        <div className="flex-1 flex flex-col min-w-0">
          <div className="h-10 flex items-center justify-between px-4 border-b border-gray-200 shrink-0">
            <span className="text-xs text-gray-500 font-mono">{filePath}</span>
            <div className="flex items-center gap-2">
              <PreludeHint compact />
              <button
                onClick={onRun}
                disabled={runState.isRunning || !active || !synced}
                title="Run against the input below — no judging"
                className="inline-flex items-center gap-1.5 px-3 py-1 text-gray-700 border border-gray-300 rounded-lg text-xs font-medium hover:bg-gray-50 disabled:opacity-50"
              >
                {runState.isRunning ? <Loader2 size={13} className="animate-spin" /> : <Play size={13} />}
                Run
              </button>
              <button
                onClick={onSubmit}
                disabled={isJudging || !active || !synced}
                title="Judge this part against all its tests"
                className="inline-flex items-center gap-1.5 px-3.5 py-1 bg-indigo-600 text-white rounded-lg text-xs font-medium hover:bg-indigo-700 disabled:opacity-50"
              >
                {isJudging ? <Loader2 size={13} className="animate-spin" /> : <Send size={13} />}
                {isJudging ? 'Judging…' : 'Submit'}
              </button>
            </div>
          </div>

          <div className="flex-1 min-h-0">
            {collab && synced && fileId ? (
              <CollabEditor
                key={fileId}
                collab={collab}
                fileId={fileId}
                path={filePath}
                readOnly={!active}
              />
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400 text-sm">
                {connected ? 'Syncing document…' : 'Connecting…'}
              </div>
            )}
          </div>

          {showResults && (
            <>
              <ResizeHandle
                direction="row"
                onDrag={(dy) => setConsoleHeight((h) => h - dy)}
                onDoubleClick={resetConsoleHeight}
              />
              <div className="shrink-0 flex flex-col" style={{ height: consoleHeight }}>
              <div className="flex items-center gap-1 px-4 pt-2 shrink-0">
                {(['judge', 'run'] as Pane[]).map((p) => (
                  <button
                    key={p}
                    onClick={() => setPane(p)}
                    className={`px-2.5 py-1 rounded text-xs font-medium ${
                      pane === p ? 'bg-gray-900 text-white' : 'text-gray-500 hover:bg-gray-100'
                    }`}
                  >
                    {p === 'judge' ? 'Judge' : 'Run'}
                  </button>
                ))}
              </div>
              <div className="px-4 overflow-y-auto flex-1 min-h-0">
                {pane === 'judge' ? (
                  <VerdictPanel
                    events={events}
                    verdict={verdict}
                    isJudging={isJudging}
                    error={error}
                    labels={labels}
                  />
                ) : (
                  <RunPanel
                    stdin={stdin}
                    onStdinChange={setStdin}
                    pytestMode={stage?.problem?.judge_mode === 'pytest'}
                    state={runState}
                  />
                )}
              </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function InterviewSessionPage() {
  const { sessionId = '' } = useParams();
  const { session, isLoading, error } = useInterviewSession(sessionId);

  if (isLoading || (!session && !error)) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="animate-spin text-gray-400" size={28} />
      </div>
    );
  }
  if (!session) {
    return (
      <div className="h-full flex items-center justify-center text-sm text-red-600">
        Couldn't load this interview{error ? `: ${detailOf(error)}` : ''}.
      </div>
    );
  }
  return <Workbench session={session} />;
}

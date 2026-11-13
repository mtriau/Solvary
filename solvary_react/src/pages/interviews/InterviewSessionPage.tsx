import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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
import { InterviewerPane } from '@/features/interviewer/components/InterviewerPane';
import { useInterviewer } from '@/features/interviewer/hooks/useInterviewer';
import { useSpeechInput } from '@/features/interviewer/hooks/useSpeechInput';
import { useSpeechOutput } from '@/features/interviewer/hooks/useSpeechOutput';
import {
  NUDGE_EVENT,
  STARTED_EVENT,
  budgetEvent,
  idleEvent,
  runEvent,
  stageEvent,
  verdictEvent,
} from '@/features/interviewer/lib/events';
import { buildScreenContext, type ScreenInputs } from '@/features/interviewer/lib/screen-context';
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
import type { InterviewSessionDetail, MicMode } from '@/shared/types/api';

type Pane = 'judge' | 'run';

const INTERVIEWER_OPEN_KEY = 'interview.interviewerOpen';
const IDLE_CHECK_MS = 15_000;
const IDLE_REPEAT_MS = 5 * 60_000;

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

  const { submit, events, verdict, isJudging, error, submissionId } = useJudgeStream();
  const runState = useRunStream();
  const [pane, setPane] = useState<Pane>('judge');
  const [stdin, setStdin] = useState('');
  const [actionError, setActionError] = useState<string | null>(null);
  const [dismissedNudge, setDismissedNudge] = useState<number | null>(null);
  const [interviewerOpen, setInterviewerOpenState] = useState<boolean>(() => {
    try {
      return localStorage.getItem(INTERVIEWER_OPEN_KEY) !== '0';
    } catch {
      return true;
    }
  });
  const setInterviewerOpen = (open: boolean) => {
    setInterviewerOpenState(open);
    try {
      localStorage.setItem(INTERVIEWER_OPEN_KEY, open ? '1' : '0');
    } catch {
      /* private mode */
    }
  };
  // Draggable splitters (remembered across sessions)
  const [rightWidth, setRightWidth, resetRightWidth] = usePersistedNumber(
    'interview.interviewerWidth',
    360,
    280,
    Math.max(320, window.innerWidth - 760),
  );
  const [leftWidth, setLeftWidth, resetLeftWidth] = usePersistedNumber(
    'interview.leftWidth',
    Math.round(window.innerWidth * 0.42),
    260,
    Math.max(400, window.innerWidth - 420 - (interviewerOpen ? rightWidth : 0)),
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

  useEffect(() => {
    if (!active) navigate(`/interviews/sessions/${session.id}/review`, { replace: true });
  }, [active, navigate, session.id]);

  const currentCode = (): string | null => {
    if (!collab || !fileId) return null;
    const code = collab.doc.getMap<Y.Text>('files').get(fileId)?.toString() ?? '';
    return code.trim() ? code : null;
  };

  const showResults =
    pane === 'run'
      ? runState.isRunning || runState.status || runState.error
      : events.length > 0 || isJudging || error;

  // ── interviewer agent: what it can see, and when it is told ──
  const lastEditAtRef = useRef<number | null>(null);
  const lastActivityRef = useRef<number | null>(null); // null until mounted (set below)
  const judgeAtRef = useRef<number | null>(null);
  const runAtRef = useRef<number | null>(null);
  const micModeRef = useRef<MicMode>('off');

  useEffect(() => {
    lastActivityRef.current ??= Date.now(); // the idle clock starts at mount, not at load time
  }, []);
  // Local edits only (remote sync transactions don't count as activity)
  useEffect(() => {
    if (!collab) return;
    const filesMap = collab.doc.getMap<Y.Text>('files');
    const onDeep = (_events: Y.YEvent<Y.Text>[], transaction: Y.Transaction) => {
      if (transaction.local) {
        const now = Date.now();
        lastEditAtRef.current = now;
        lastActivityRef.current = now;
      }
    };
    filesMap.observeDeep(onDeep);
    return () => filesMap.unobserveDeep(onDeep);
  }, [collab]);
  useEffect(() => {
    if (verdict) judgeAtRef.current = Date.now();
  }, [verdict]);
  useEffect(() => {
    if (!runState.isRunning && (runState.status || runState.error)) runAtRef.current = Date.now();
  }, [runState.isRunning, runState.status, runState.error]);

  // The screen, read at the moment a turn is sent (never stale, never a dependency)
  const screenRef = useRef<() => Omit<ScreenInputs, 'lastCode'>>(() => ({
    stage: 1,
    code: '',
    judge: { events: [], verdict: null, submissionId: null, at: null, labels: null },
    run: { state: runState, stdin: '', at: null },
    pane: 'none',
    lastEditAt: null,
    mic: 'off',
  }));
  screenRef.current = () => ({
    stage: session.current_stage,
    code: currentCode() ?? '',
    judge: { events, verdict, submissionId, at: judgeAtRef.current, labels },
    run: { state: runState, stdin, at: runAtRef.current },
    pane: showResults ? pane : 'none',
    lastEditAt: lastEditAtRef.current,
    mic: micModeRef.current,
  });
  const buildScreen = useCallback(
    (lastCode: string | null) => buildScreenContext({ ...screenRef.current(), lastCode }),
    [],
  );

  const tts = useSpeechOutput();
  const interviewer = useInterviewer({
    sessionId: session.id,
    enabled: active,
    buildScreen,
    onReply: (text) => tts.speak(text),
  });
  const { enqueue } = interviewer;
  const speech = useSpeechInput({
    onUtterance: (text) => {
      lastActivityRef.current = Date.now();
      enqueue({ trigger: 'speech', utterance: text });
    },
  });
  micModeRef.current = speech.mode;

  const keySource = interviewer.transcript?.key_source ?? 'none';
  const agentEnabled = active && keySource !== 'none' && !interviewer.noKey;
  const agentEnabledRef = useRef(agentEnabled);
  agentEnabledRef.current = agentEnabled;
  const eventsRef = useRef(events);
  eventsRef.current = events;
  const labelsRef = useRef(labels);
  labelsRef.current = labels;
  const streamingRef = useRef(interviewer.streaming);
  streamingRef.current = interviewer.streaming;

  // The mic never hears the interviewer: paused while the voice plays, and
  // while a reply streams if the voice is on
  const micPaused = tts.speaking || (interviewer.streaming && tts.enabled);
  const { setPaused } = speech;
  useEffect(() => {
    setPaused(micPaused);
  }, [micPaused, setPaused]);

  // Opening line, once, on a fresh session
  const transcriptLoaded = !!interviewer.transcript;
  const turnCount = interviewer.turns.length;
  const openingRef = useRef(false);
  useEffect(() => {
    if (!agentEnabled || !transcriptLoaded || openingRef.current) return;
    openingRef.current = true;
    if (turnCount === 0) enqueue({ trigger: 'opening', events: [STARTED_EVENT] });
  }, [agentEnabled, transcriptLoaded, turnCount, enqueue]);

  // A verdict changes the derived results → refresh the payload; tell the interviewer
  useEffect(() => {
    if (!verdict) return;
    queryClient.invalidateQueries({ queryKey: INTERVIEW_KEYS.session(session.id) });
    if (agentEnabledRef.current) {
      enqueue({ trigger: 'event', events: [verdictEvent(verdict, eventsRef.current, labelsRef.current)] });
    }
  }, [verdict, queryClient, session.id, enqueue]);

  // A Run that crashed or timed out
  const runEventRef = useRef<string | null>(null);
  useEffect(() => {
    if (runState.isRunning || !runState.runId || runEventRef.current === runState.runId) return;
    if ((runState.status && runState.status !== 'finished') || runState.error) {
      runEventRef.current = runState.runId;
      if (agentEnabledRef.current) enqueue({ trigger: 'event', events: [runEvent(runState)] });
    }
  }, [runState, enqueue]);

  // Stage advanced or switched
  const prevStageRef = useRef(session.current_stage);
  useEffect(() => {
    if (prevStageRef.current === session.current_stage) return;
    prevStageRef.current = session.current_stage;
    if (stage && agentEnabledRef.current) enqueue({ trigger: 'event', events: [stageEvent(stage)] });
  }, [session.current_stage, stage, enqueue]);

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

  // Budget exceeded: once per stage
  const budgetFiredRef = useRef<number | null>(null);
  useEffect(() => {
    if (!overBudget || !stage || budgetFiredRef.current === session.current_stage) return;
    budgetFiredRef.current = session.current_stage;
    if (agentEnabledRef.current) {
      enqueue({ trigger: 'event', events: [budgetEvent(stage, stageElapsedS)] });
    }
  }, [overBudget, stage, session.current_stage, stageElapsedS, enqueue]);

  // Idle: no speech, typing or code change for idle_s (at most once per 5 min)
  const idleS = interviewer.transcript?.idle_s ?? 180;
  useEffect(() => {
    if (!agentEnabled) return;
    let lastIdleEvent = 0;
    const id = window.setInterval(() => {
      const now = Date.now();
      const lastActivity = lastActivityRef.current ?? now;
      if (
        !streamingRef.current &&
        now - lastActivity >= idleS * 1000 &&
        now - lastIdleEvent >= IDLE_REPEAT_MS
      ) {
        lastIdleEvent = now;
        enqueue({ trigger: 'event', events: [idleEvent(idleS)] });
      }
    }, IDLE_CHECK_MS);
    return () => window.clearInterval(id);
  }, [agentEnabled, idleS, enqueue]);

  // Keyboard: Ctrl+Shift+M toggles the mic, Ctrl+Shift+Space is push-to-talk.
  // Skipped when the editor already handled the chord (defaultPrevented).
  const lastMicModeRef = useRef<MicMode>('open');
  useEffect(() => {
    if (speech.mode !== 'off') lastMicModeRef.current = speech.mode;
  }, [speech.mode]);
  const { mode: micMode, setMode: setMicMode, pressStart, pressEnd, supported: micSupported } = speech;
  useEffect(() => {
    if (!micSupported) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.defaultPrevented || !e.ctrlKey || !e.shiftKey || e.altKey || e.metaKey) return;
      if (e.code === 'KeyM') {
        e.preventDefault();
        setMicMode(micMode === 'off' ? lastMicModeRef.current : 'off');
      } else if (e.code === 'Space' && micMode === 'push' && !e.repeat) {
        e.preventDefault();
        pressStart();
      }
    };
    const onKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space' && micMode === 'push') pressEnd();
    };
    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('keyup', onKeyUp);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('keyup', onKeyUp);
    };
  }, [micSupported, micMode, setMicMode, pressStart, pressEnd]);

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

  return (
    <div className="h-full flex flex-col">
      <TimerBar
        session={session}
        countdown={countdown}
        stageElapsedS={stageElapsedS}
        busy={busy}
        interviewerOpen={interviewerOpen}
        onToggleInterviewer={() => setInterviewerOpen(!interviewerOpen)}
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

        {interviewerOpen && (
          <>
            <ResizeHandle
              direction="col"
              onDrag={(dx) => setRightWidth((w) => w - dx)}
              onDoubleClick={resetRightWidth}
            />
            <div className="bg-white flex flex-col min-h-0 shrink-0" style={{ width: rightWidth }}>
              <InterviewerPane
                interviewer={interviewer}
                speech={speech}
                tts={tts}
                active={active}
                onSend={(text) => {
                  lastActivityRef.current = Date.now();
                  enqueue({ trigger: 'typed', utterance: text });
                }}
                onNudge={() => enqueue({ trigger: 'event', events: [NUDGE_EVENT] })}
                onCollapse={() => setInterviewerOpen(false)}
              />
            </div>
          </>
        )}
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

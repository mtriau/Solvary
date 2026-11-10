import { useCallback, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { ArrowLeft, BookOpen, Code2, ExternalLink, Loader2, RotateCcw, Sparkles } from 'lucide-react';
import { AssistPanel } from '@/features/assist/components/AssistPanel';
import { SubmissionCode } from '@/features/execution/components/SubmissionCode';
import { PaceTimeline } from '@/features/interviews/components/PaceTimeline';
import {
  useInterviewReview,
  useStartInterview,
} from '@/features/interviews/hooks/useInterviewSession';
import { STATUS_LABELS, fmtClock, fmtMinutes } from '@/features/interviews/lib/format';
import { ApiError } from '@/shared/lib/api-client';

const PROSE =
  'prose prose-sm max-w-none text-gray-700 [&_pre]:bg-gray-50 [&_pre]:text-gray-800 [&_pre]:border [&_pre]:border-gray-200 [&_pre]:rounded-lg [&_pre]:p-3 [&_code]:text-[13px]';

/** The attempt to show by default: the latest accepted one, else the latest. */
function pickDefault(subs: { id: string; verdict: string }[]): string | null {
  if (!subs.length) return null;
  const accepted = [...subs].reverse().find((s) => s.verdict === 'accepted');
  return (accepted ?? subs[subs.length - 1]).id;
}

export default function InterviewReviewPage() {
  const { sessionId = '' } = useParams();
  const navigate = useNavigate();
  const { data: review, isLoading, error } = useInterviewReview(sessionId);
  const start = useStartInterview();
  const [open, setOpen] = useState<number | null>(null);
  const [aiStage, setAiStage] = useState<number | null>(null);
  // Which attempt's code is shown per part (keyed by ordinal); unset = default pick.
  const [chosen, setChosen] = useState<Record<number, string>>({});
  // Code of the attempt on screen, handed to the AI panel of that part.
  const [shownCode, setShownCode] = useState<Record<number, string>>({});
  const codeLoaded = useCallback(
    (ordinal: number, code: string) =>
      setShownCode((prev) => (prev[ordinal] === code ? prev : { ...prev, [ordinal]: code })),
    [],
  );

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="animate-spin text-gray-400" size={28} />
      </div>
    );
  }
  if (!review) {
    const stillActive = error instanceof ApiError && error.status === 409;
    return (
      <div className="h-full flex flex-col items-center justify-center gap-3 text-sm text-gray-600">
        {stillActive ? 'This interview is still in progress.' : 'Could not load this review.'}
        {stillActive && (
          <Link to={`/interviews/sessions/${sessionId}`} className="text-indigo-600 hover:underline">
            Back to the interview
          </Link>
        )}
      </div>
    );
  }

  const tiles = [
    { label: 'Score', value: `${review.score.percent}%`, context: `${review.score.passed} of ${review.score.total} tests` },
    { label: 'Time used', value: fmtClock(review.time_used_s), context: `of ${fmtMinutes(review.duration_s)}` },
    { label: 'Parts reached', value: `${review.stages_reached}/${review.stage_count}`, context: STATUS_LABELS[review.status] },
    {
      label: 'Accepted parts',
      value: review.stages.filter((s) => s.result.best_verdict === 'accepted').length,
      context: `${review.submissions.length} submission${review.submissions.length === 1 ? '' : 's'}`,
    },
  ];

  const retry = async () => {
    const s = await start.mutateAsync({
      template_id: review.template.id,
      language: review.language,
      duration_s: review.duration_s,
    });
    navigate(`/interviews/sessions/${s.id}`);
  };

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
        <div>
          <Link to="/interviews" className="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 mb-2">
            <ArrowLeft size={12} /> All interviews
          </Link>
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{review.template.title}</h1>
              <p className="text-xs text-gray-500 mt-1">
                {new Date(review.started_at).toLocaleString()} · {STATUS_LABELS[review.status]}
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {review.workspace_id && (
                <Link
                  to={`/workspaces/${review.workspace_id}`}
                  title="Open the editor as you left it at the end of the interview"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-medium hover:bg-white"
                >
                  <ExternalLink size={14} /> Final code
                </Link>
              )}
              <button
                onClick={retry}
                disabled={start.isPending}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-medium hover:bg-white disabled:opacity-50"
              >
                <RotateCcw size={14} /> Run it again
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {tiles.map((t) => (
            <div key={t.label} className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="text-xs text-gray-500">{t.label}</div>
              <div className="mt-1 text-3xl font-semibold text-gray-900">{t.value}</div>
              <div className="mt-0.5 text-xs text-gray-400">{t.context}</div>
            </div>
          ))}
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
          <div>
            <h2 className="text-sm font-semibold text-gray-900">Pacing</h2>
            {review.diagnosis && <p className="text-sm text-gray-700 mt-1">{review.diagnosis}</p>}
          </div>
          <PaceTimeline review={review} />
          <p className="text-[11px] text-gray-400">
            Bar = time on the part, dashed line = its budget, ticks = submissions (green accepted).
          </p>
        </div>

        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-gray-900">Parts</h2>
          {review.stages.map((s) => {
            const r = s.result;
            const isOpen = open === s.ordinal;
            const verdictSummary = r.submissions
              ? `${r.best_verdict} (${r.best_passed}/${r.best_total} passed), ${fmtClock(r.time_spent_s)} spent${s.budget_s ? ` of a ${fmtClock(s.budget_s)} budget` : ''}`
              : `no submission; ${fmtClock(r.time_spent_s)} spent`;
            const attempts = s.problem
              ? review.submissions.filter((sub) => sub.problem_id === s.problem?.id)
              : [];
            const shownId = chosen[s.ordinal] ?? pickDefault(attempts);
            return (
              <div key={s.ordinal} id={`stage-${s.ordinal}`} className="bg-white border border-gray-200 rounded-xl scroll-mt-4">
                <button
                  onClick={() => setOpen(isOpen ? null : s.ordinal)}
                  className="w-full flex items-center gap-3 px-5 py-3 text-left"
                >
                  <span className="font-semibold text-gray-900 flex-1">{s.title}</span>
                  {s.ordinal > review.stages_reached ? (
                    <span className="text-xs text-gray-400">never reached</span>
                  ) : (
                    <span
                      className={`text-xs font-medium ${r.best_verdict === 'accepted' ? 'text-green-600' : r.submissions ? 'text-red-600' : 'text-gray-400'}`}
                    >
                      {r.submissions ? `${r.best_verdict?.replace('_', ' ')} · ${r.best_passed}/${r.best_total}` : 'no submission'}
                    </span>
                  )}
                  <span className="text-xs text-gray-400 font-mono">{fmtClock(r.time_spent_s)}</span>
                </button>
                {isOpen && s.problem && (
                  <div className="px-5 pb-5 space-y-4 border-t border-gray-100 pt-4">
                    <div className={PROSE}>
                      <ReactMarkdown>{s.problem.statement_md}</ReactMarkdown>
                    </div>
                    {s.editorial_md && (
                      <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3">
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-800 mb-1">
                          <BookOpen size={13} /> Editorial
                        </div>
                        <div className={`${PROSE} text-emerald-900`}>
                          <ReactMarkdown>{s.editorial_md}</ReactMarkdown>
                        </div>
                      </div>
                    )}
                    {attempts.length > 0 && shownId && (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-gray-900">
                            <Code2 size={13} /> Your code
                          </span>
                          <select
                            value={shownId}
                            onChange={(e) => setChosen((prev) => ({ ...prev, [s.ordinal]: e.target.value }))}
                            className="text-xs border border-gray-300 rounded-md px-2 py-1 bg-white text-gray-700"
                          >
                            {attempts.map((sub, i) => (
                              <option key={sub.id} value={sub.id}>
                                Attempt {i + 1} · +
                                {fmtClock((new Date(sub.created_at).getTime() - new Date(review.started_at).getTime()) / 1000)}
                                {' · '}
                                {sub.verdict.replace('_', ' ')} {sub.passed}/{sub.total}
                              </option>
                            ))}
                          </select>
                          <span className="text-[11px] text-gray-400">
                            {attempts.length} attempt{attempts.length === 1 ? '' : 's'} on this part
                          </span>
                        </div>
                        <SubmissionCode
                          key={shownId}
                          submissionId={shownId}
                          onLoaded={(code) => codeLoaded(s.ordinal, code)}
                        />
                      </div>
                    )}
                    <div>
                      <button
                        onClick={() => setAiStage(aiStage === s.ordinal ? null : s.ordinal)}
                        className="inline-flex items-center gap-1.5 text-xs font-medium text-indigo-700 hover:underline"
                      >
                        <Sparkles size={13} /> {aiStage === s.ordinal ? 'Hide AI review' : 'Ask AI about this part'}
                      </button>
                      {aiStage === s.ordinal && (
                        <AssistPanel
                          problemId={s.problem.id}
                          code={shownCode[s.ordinal] ?? ''}
                          language={review.language}
                          verdictSummary={verdictSummary}
                          interviewSessionId={review.id}
                        />
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {review.submissions.length > 0 && (
          <div>
            <h2 className="text-sm font-semibold text-gray-900 mb-2">Submissions</h2>
            <ul className="divide-y divide-gray-100 border border-gray-200 rounded-xl bg-white text-xs">
              {review.submissions.map((sub) => {
                const stage = review.stages.find((s) => s.problem?.id === sub.problem_id);
                const showCode = () => {
                  if (!stage) return;
                  setChosen((prev) => ({ ...prev, [stage.ordinal]: sub.id }));
                  setOpen(stage.ordinal);
                  document.getElementById(`stage-${stage.ordinal}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                };
                return (
                  <li key={sub.id}>
                    <button
                      onClick={showCode}
                      disabled={!stage}
                      title={stage ? 'View the code of this attempt' : undefined}
                      className="w-full flex items-center gap-3 px-4 py-2 text-left hover:bg-gray-50 disabled:cursor-default disabled:hover:bg-white"
                    >
                      <span className="text-gray-400 font-mono w-14">
                        +{fmtClock((new Date(sub.created_at).getTime() - new Date(review.started_at).getTime()) / 1000)}
                      </span>
                      <span className="flex-1 text-gray-700">{stage?.title ?? sub.problem_id}</span>
                      <span className={`font-medium capitalize ${sub.verdict === 'accepted' ? 'text-green-600' : 'text-red-600'}`}>
                        {sub.verdict.replace('_', ' ')}
                      </span>
                      <span className="text-gray-400">
                        {sub.passed}/{sub.total}
                      </span>
                      {stage && <Code2 size={13} className="text-gray-300" />}
                    </button>
                  </li>
                );
              })}
            </ul>
            <p className="text-[11px] text-gray-400 mt-1">Click an attempt to see its code under the part above.</p>
          </div>
        )}
      </div>
    </div>
  );
}

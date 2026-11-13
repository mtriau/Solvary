import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Loader2, Play, Timer } from 'lucide-react';
import {
  useInterviewSessions,
  useInterviewTemplates,
  useStartInterview,
} from '@/features/interviews/hooks/useInterviewSession';
import { ApiKeyCard } from '@/features/interviewer/components/ApiKeyCard';
import { useActiveInterview } from '@/features/interviews/hooks/useActiveInterview';
import { useCountdown } from '@/features/interviews/hooks/useCountdown';
import { FORMAT_LABELS, STATUS_LABELS, fmtClock, fmtMinutes } from '@/features/interviews/lib/format';
import { ApiError } from '@/shared/lib/api-client';
import type { InterviewSessionSummary, InterviewTemplateSummary } from '@/shared/types/api';

const LANGUAGES = ['python', 'javascript'] as const;
const DURATION_PRESETS_MIN = [30, 45, 60, 90, 120];
const MIN_DURATION_MIN = 15;
const MAX_DURATION_MIN = 180;

/** Pick this run's clock. Stage budgets scale with it on the server. */
function DurationPicker({
  template,
  minutes,
  onChange,
}: {
  template: InterviewTemplateSummary;
  minutes: number;
  onChange: (m: number) => void;
}) {
  const ratio = (minutes * 60) / template.duration_s;
  const isDefault = minutes * 60 === template.duration_s;
  return (
    <div className="mt-3 rounded-lg border border-gray-100 bg-gray-50 px-3 py-2">
      <div className="flex items-center gap-3">
        <span className="text-xs text-gray-500 shrink-0">Clock</span>
        <input
          type="range"
          min={MIN_DURATION_MIN}
          max={MAX_DURATION_MIN}
          step={5}
          value={minutes}
          onChange={(e) => onChange(Number(e.target.value))}
          className="flex-1 accent-indigo-600"
          aria-label="Interview duration in minutes"
        />
        <span className="font-mono text-sm font-semibold text-gray-900 w-16 text-right tabular-nums">
          {minutes} min
        </span>
      </div>
      <div className="mt-1.5 flex items-center gap-1 flex-wrap">
        {[...new Set([...DURATION_PRESETS_MIN, template.duration_s / 60])]
          .sort((a, b) => a - b)
          .map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => onChange(m)}
              className={`px-2 py-0.5 rounded text-[11px] font-medium border ${
                m === minutes
                  ? 'bg-gray-900 text-white border-gray-900'
                  : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-100'
              }`}
            >
              {m}
              {m * 60 === template.duration_s && ' (default)'}
            </button>
          ))}
        {!isDefault && (
          <span className="ml-auto text-[11px] text-gray-400">
            part budgets scale ×{ratio.toFixed(2)}
          </span>
        )}
      </div>
    </div>
  );
}

function ActiveBanner({ active }: { active: InterviewSessionSummary }) {
  const countdown = useCountdown(active.ends_at, active.server_time);
  return (
    <Link
      to={`/interviews/sessions/${active.id}`}
      className="flex items-center gap-3 px-4 py-3 rounded-xl border border-indigo-200 bg-indigo-50 hover:bg-indigo-100 transition-colors"
    >
      <Timer size={18} className="text-indigo-600" />
      <div className="flex-1 text-sm">
        <span className="font-semibold text-indigo-900">{active.template.title}</span>
        <span className="text-indigo-700"> is in progress — the clock is running.</span>
      </div>
      <span className="font-mono text-lg font-semibold text-indigo-900 tabular-nums">
        {fmtClock(countdown.remainingS)}
      </span>
    </Link>
  );
}

function ScoreChip({ s }: { s: InterviewSessionSummary }) {
  const tone =
    s.status === 'abandoned'
      ? 'bg-gray-100 text-gray-500'
      : s.score.percent === 100
        ? 'bg-green-50 text-green-700 border-green-200'
        : 'bg-gray-50 text-gray-700 border-gray-200';
  return (
    <span className={`px-2 py-0.5 rounded border text-xs font-medium ${tone}`}>
      {s.status === 'abandoned' ? 'no score' : `${s.score.percent}% · ${s.score.passed}/${s.score.total}`}
    </span>
  );
}

export default function InterviewsPage() {
  const navigate = useNavigate();
  const templates = useInterviewTemplates();
  const sessions = useInterviewSessions();
  const { data: active } = useActiveInterview();
  const start = useStartInterview();
  const [language, setLanguage] = useState<string>('python');
  const [error, setError] = useState<string | null>(null);
  const [durations, setDurations] = useState<Record<string, number>>({});
  const minutesFor = (t: InterviewTemplateSummary) => durations[t.id] ?? t.duration_s / 60;

  const onStart = async (t: InterviewTemplateSummary) => {
    setError(null);
    try {
      const session = await start.mutateAsync({
        template_id: t.id,
        language,
        duration_s: minutesFor(t) * 60,
      });
      navigate(`/interviews/sessions/${session.id}`);
    } catch (err) {
      const detail =
        err instanceof ApiError
          ? (JSON.parse(err.body || '{}') as { detail?: string }).detail
          : undefined;
      setError(detail ?? (err as Error).message);
    }
  };

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">
        <div className="flex items-end justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Mock interviews</h1>
            <p className="text-sm text-gray-500 mt-1">
              A running clock, parts revealed one at a time, tests released with each part.
              The point is pacing: know when to move on.
            </p>
          </div>
          <label className="text-xs text-gray-500 flex items-center gap-2">
            Language
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="text-sm border border-gray-200 rounded-lg px-2 py-1 bg-white"
            >
              {LANGUAGES.map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </select>
          </label>
        </div>

        {active && <ActiveBanner active={active} />}
        <ApiKeyCard />
        {error && (
          <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-4 py-2">
            {error}
          </div>
        )}

        {templates.isLoading && (
          <div className="flex justify-center py-10">
            <Loader2 className="animate-spin text-gray-400" size={26} />
          </div>
        )}

        <div className="space-y-3">
          {templates.data?.map((t) => (
            <div key={t.id} className="bg-white border border-gray-200 rounded-xl p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <h2 className="font-semibold text-gray-900">{t.title}</h2>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {FORMAT_LABELS[t.format]} · {fmtMinutes(t.duration_s)} · {t.stages.length} parts
                    {t.pacing === 'strict' && ' · strict pacing'}
                  </div>
                  <ol className="mt-3 flex flex-wrap gap-1.5">
                    {t.stages.map((s) => (
                      <li
                        key={s.ordinal}
                        className="text-[11px] px-2 py-0.5 rounded bg-gray-50 border border-gray-200 text-gray-600"
                      >
                        {s.title}
                        {s.budget_s != null && (
                          <span className="text-gray-400">
                            {' · '}
                            {fmtMinutes((s.budget_s * minutesFor(t) * 60) / t.duration_s)}
                          </span>
                        )}
                      </li>
                    ))}
                  </ol>
                  <DurationPicker
                    template={t}
                    minutes={minutesFor(t)}
                    onChange={(m) => setDurations((d) => ({ ...d, [t.id]: m }))}
                  />
                  {t.last_result && (
                    <div className="mt-3 text-xs text-gray-500 flex items-center gap-2">
                      Last run: <ScoreChip s={t.last_result} />
                      <span>{fmtClock(t.last_result.time_used_s)} used</span>
                      <Link
                        to={`/interviews/sessions/${t.last_result.id}/review`}
                        className="text-indigo-600 hover:underline"
                      >
                        review
                      </Link>
                    </div>
                  )}
                </div>
                <button
                  onClick={() => onStart(t)}
                  disabled={start.isPending || !!active}
                  title={active ? 'Finish or abandon the interview in progress first' : undefined}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 shrink-0"
                >
                  {start.isPending ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : (
                    <Play size={14} />
                  )}
                  Start
                </button>
              </div>
            </div>
          ))}
          {templates.data && templates.data.length === 0 && (
            <div className="text-sm text-gray-400 text-center py-8">
              No interview templates yet. Run <code>python -m scripts.seed_interviews</code>.
            </div>
          )}
        </div>

        {sessions.data && sessions.data.items.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-2">History</h3>
            <ul className="divide-y divide-gray-100 border border-gray-200 rounded-xl bg-white text-xs">
              {sessions.data.items.map((s) => (
                <li key={s.id} className="flex items-center gap-3 px-4 py-2.5">
                  <span className="font-medium text-gray-900 truncate flex-1">
                    {s.template.title}
                  </span>
                  <span className="text-gray-400">{STATUS_LABELS[s.status]}</span>
                  <ScoreChip s={s} />
                  <span className="text-gray-400 font-mono">{fmtClock(s.time_used_s)}</span>
                  <span className="text-gray-400">
                    {new Date(s.started_at).toLocaleDateString()}
                  </span>
                  {s.status === 'active' ? (
                    <Link to={`/interviews/sessions/${s.id}`} className="text-indigo-600 hover:underline">
                      resume
                    </Link>
                  ) : (
                    <Link
                      to={`/interviews/sessions/${s.id}/review`}
                      className="text-indigo-600 hover:underline"
                    >
                      review
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

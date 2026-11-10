import { Link } from 'react-router-dom';
import { Check, Circle, Loader2, Play, Zap } from 'lucide-react';
import { useDrills } from '@/features/drills/hooks/useDrills';

export default function DrillsPage() {
  const { data, isLoading, error } = useDrills();

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="animate-spin text-gray-400" size={28} />
      </div>
    );
  }
  if (error || !data) {
    return (
      <div className="h-full flex items-center justify-center text-sm text-red-600">
        Could not load the drills.
      </div>
    );
  }

  const pct = data.total ? Math.round((100 * data.solved) / data.total) : 0;
  const allDone = data.total > 0 && data.solved === data.total;

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
        <div className="bg-white border border-gray-200 rounded-xl p-6 flex items-start justify-between gap-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 inline-flex items-center gap-2">
              <Zap size={22} className="text-amber-500" /> Drills
            </h1>
            <p className="text-sm text-gray-600 mt-1 max-w-xl">
              Two-minute Python exercises, one idiom each. Solve it, then compare your code with the
              idiomatic version and read why it is written that way. The habits come from the
              comparison, so always look at the solution after yours passes.
            </p>
            <div className="mt-4 flex items-center gap-3">
              <div className="h-2 w-56 bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full bg-amber-500" style={{ width: `${pct}%` }} />
              </div>
              <span className="text-xs text-gray-500">
                {data.solved} of {data.total} solved
              </span>
            </div>
          </div>
          {data.next_slug ? (
            <Link
              to={`/drills/${data.next_slug}`}
              className="shrink-0 inline-flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800"
            >
              <Play size={14} /> {data.solved ? 'Continue' : 'Start'}
            </Link>
          ) : allDone ? (
            <span className="shrink-0 text-sm text-green-700 font-medium">All drills solved</span>
          ) : null}
        </div>

        {data.topics.map((topic) => {
          const topicPct = topic.total ? Math.round((100 * topic.solved) / topic.total) : 0;
          return (
            <section key={topic.slug} className="bg-white border border-gray-200 rounded-xl">
              <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-4">
                <div className="flex-1 min-w-0">
                  <h2 className="font-semibold text-gray-900">{topic.title}</h2>
                  <p className="text-xs text-gray-500 mt-0.5">{topic.blurb}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <div className="h-1.5 w-24 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-green-500" style={{ width: `${topicPct}%` }} />
                  </div>
                  <span className="text-xs text-gray-500 font-mono w-8 text-right">
                    {topic.solved}/{topic.total}
                  </span>
                </div>
              </div>
              <ul className="divide-y divide-gray-100">
                {topic.drills.map((drill) => (
                  <li key={drill.id}>
                    <Link
                      to={`/drills/${drill.slug}`}
                      className="flex items-center gap-3 px-5 py-2.5 hover:bg-gray-50"
                    >
                      {drill.solved ? (
                        <Check size={15} className="text-green-600 shrink-0" />
                      ) : (
                        <Circle size={15} className="text-gray-300 shrink-0" />
                      )}
                      <span
                        className={`flex-1 text-sm ${drill.solved ? 'text-gray-500' : 'text-gray-900'}`}
                      >
                        {drill.title}
                      </span>
                      {drill.attempts > 0 && (
                        <span className="text-[11px] text-gray-400">
                          {drill.attempts} attempt{drill.attempts === 1 ? '' : 's'}
                        </span>
                      )}
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          );
        })}
      </div>
    </div>
  );
}

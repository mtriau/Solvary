import type { DifficultyStat, LanguageStat } from '@/shared/types/api';

/**
 * Meters: the unfilled track is a lighter step of the SAME ramp as the
 * fill, so state reads across the whole bar. Difficulty hue is semantic
 * and always paired with its text label.
 */
const RAMP: Record<string, { fill: string; track: string }> = {
  easy: { fill: 'bg-teal-500', track: 'bg-teal-100' },
  medium: { fill: 'bg-amber-500', track: 'bg-amber-100' },
  hard: { fill: 'bg-rose-500', track: 'bg-rose-100' },
};

export function DifficultyMeters({
  byDifficulty,
  byLanguage,
}: {
  byDifficulty: DifficultyStat[];
  byLanguage: LanguageStat[];
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <h2 className="text-sm font-semibold text-gray-900">Progress</h2>
      <div className="mt-3 space-y-3">
        {byDifficulty.map((d) => {
          const pct = d.total ? Math.round((d.solved / d.total) * 100) : 0;
          const ramp = RAMP[d.difficulty];
          return (
            <div key={d.difficulty}>
              <div className="flex items-baseline justify-between text-xs">
                <span className="capitalize text-gray-700">{d.difficulty}</span>
                <span className="text-gray-500 tabular-nums">
                  {d.solved} / {d.total}
                </span>
              </div>
              <div className={`mt-1 h-2 rounded-full ${ramp.track}`}>
                <div
                  className={`h-2 rounded-full ${ramp.fill} transition-all`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {byLanguage.length > 0 && (
        <>
          <h3 className="mt-4 text-xs font-medium text-gray-500">Languages</h3>
          <div className="mt-2 flex flex-wrap gap-2">
            {byLanguage.map((lang) => (
              <span
                key={lang.language}
                className="px-2 py-1 rounded bg-gray-100 text-xs text-gray-700"
              >
                {lang.language} · {lang.solved} solved · {lang.submissions} subs
              </span>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

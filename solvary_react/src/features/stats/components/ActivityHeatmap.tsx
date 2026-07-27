import type { HeatmapDay } from '@/shared/types/api';

/**
 * Contribution-style heatmap. Sequential encoding: one hue (the app's
 * indigo accent), more-is-darker, monotonic steps; zero is the neutral
 * surface step. Per-cell hover carries the exact value (native tooltip).
 */
const LEVELS = [
  'bg-gray-100',
  'bg-indigo-200',
  'bg-indigo-400',
  'bg-indigo-600',
  'bg-indigo-800',
] as const;

function level(count: number): number {
  if (count === 0) return 0;
  if (count === 1) return 1;
  if (count <= 3) return 2;
  if (count <= 6) return 3;
  return 4;
}

export function ActivityHeatmap({ heatmap }: { heatmap: HeatmapDay[] }) {
  // Pad so the grid starts on a Sunday column like the data ends today
  const firstDay = heatmap.length ? new Date(`${heatmap[0].day}T00:00:00Z`) : null;
  const padding = firstDay ? firstDay.getUTCDay() : 0;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <h2 className="text-sm font-semibold text-gray-900">Activity</h2>
      <div className="mt-3 overflow-x-auto">
        <div className="grid grid-flow-col grid-rows-7 gap-[3px] w-max">
          {Array.from({ length: padding }).map((_, i) => (
            <div key={`pad-${i}`} className="w-[11px] h-[11px]" />
          ))}
          {heatmap.map((d) => (
            <div
              key={d.day}
              className={`w-[11px] h-[11px] rounded-[2px] ${LEVELS[level(d.count)]}`}
              title={`${d.count} submission${d.count === 1 ? '' : 's'} on ${d.day}`}
            />
          ))}
        </div>
      </div>
      <div className="mt-2 flex items-center gap-1 text-[10px] text-gray-400">
        Less
        {LEVELS.map((cls) => (
          <span key={cls} className={`inline-block w-[11px] h-[11px] rounded-[2px] ${cls}`} />
        ))}
        More
      </div>
    </div>
  );
}

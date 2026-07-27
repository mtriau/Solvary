import type { TotalsStats } from '@/shared/types/api';

/**
 * KPI row — stat-tile contract: sentence-case label, semibold value in
 * text tokens (never a data color), secondary context inline.
 */
export function StatTiles({ totals }: { totals: TotalsStats }) {
  const rate = Math.round(totals.acceptance_rate * 100);
  const tiles = [
    {
      label: 'Problems solved',
      value: totals.solved,
      context: `of ${totals.total_problems}`,
    },
    {
      label: 'Acceptance rate',
      value: totals.submissions ? `${rate}%` : '—',
      context: `${totals.accepted_submissions} of ${totals.submissions} submissions`,
    },
    {
      label: 'Current streak',
      value: totals.current_streak_days,
      context:
        totals.current_streak_days === 1
          ? 'day — keep it going'
          : totals.current_streak_days > 1
            ? 'days 🔥'
            : 'days',
    },
    {
      label: 'Longest streak',
      value: totals.longest_streak_days,
      context: totals.longest_streak_days === 1 ? 'day' : 'days',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {tiles.map((tile) => (
        <div key={tile.label} className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-xs text-gray-500">{tile.label}</div>
          <div className="mt-1 text-3xl font-semibold text-gray-900">{tile.value}</div>
          <div className="mt-0.5 text-xs text-gray-400">{tile.context}</div>
        </div>
      ))}
    </div>
  );
}

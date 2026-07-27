import type { StatsBadge } from '@/shared/types/api';

export function BadgeGrid({ badges }: { badges: StatsBadge[] }) {
  const earned = badges.filter((b) => b.earned).length;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-baseline justify-between">
        <h2 className="text-sm font-semibold text-gray-900">Accolades</h2>
        <span className="text-xs text-gray-500 tabular-nums">
          {earned} / {badges.length} earned
        </span>
      </div>
      <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-2">
        {badges.map((badge) => (
          <div
            key={badge.id}
            className={`rounded-lg border p-3 ${
              badge.earned
                ? 'border-indigo-200 bg-indigo-50/50'
                : 'border-gray-100 bg-gray-50 opacity-50 grayscale'
            }`}
            title={badge.earned ? undefined : 'Not earned yet'}
          >
            <div className="text-xl leading-none">{badge.icon}</div>
            <div className="mt-1.5 text-xs font-semibold text-gray-900">{badge.name}</div>
            <div className="mt-0.5 text-[11px] leading-tight text-gray-500">
              {badge.description}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

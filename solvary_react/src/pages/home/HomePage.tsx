import { useAuth } from '@/app/providers/AuthProvider';
import { Avatar } from '@/shared/components/Avatar';
import { useMyStats } from '@/features/stats/hooks/useMyStats';
import { StatTiles } from '@/features/stats/components/StatTiles';
import { DifficultyMeters } from '@/features/stats/components/DifficultyMeters';
import { ActivityHeatmap } from '@/features/stats/components/ActivityHeatmap';
import { BadgeGrid } from '@/features/stats/components/BadgeGrid';
import { RecentActivity } from '@/features/stats/components/RecentActivity';

export default function HomePage() {
  const { user } = useAuth();
  const { data: stats, isLoading, error } = useMyStats();

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-6">
        {/* Profile header */}
        <div className="flex items-center gap-3">
          {user && <Avatar src={user.avatar_url} name={user.name} size="md" />}
          <div>
            <h1 className="text-lg font-bold text-gray-900">{user?.name}</h1>
            <p className="text-xs text-gray-500">{user?.email}</p>
          </div>
        </div>

        {isLoading && (
          <div className="mt-10 text-center text-sm text-gray-400">Loading your stats…</div>
        )}
        {error != null && (
          <div className="mt-10 text-center text-sm text-rose-600">
            Couldn't load stats — try refreshing.
          </div>
        )}

        {stats && (
          <div className="mt-5 space-y-4">
            <StatTiles totals={stats.totals} />

            <ActivityHeatmap heatmap={stats.heatmap} />

            <div className="grid lg:grid-cols-2 gap-4 items-start">
              <div className="space-y-4">
                <DifficultyMeters
                  byDifficulty={stats.by_difficulty}
                  byLanguage={stats.by_language}
                />
                <RecentActivity recent={stats.recent} />
              </div>
              <BadgeGrid badges={stats.badges} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

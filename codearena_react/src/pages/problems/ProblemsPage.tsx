import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useProblems } from '@/features/problems/hooks/useProblems';
import type { Difficulty } from '@/shared/types/api';

const DIFFICULTY_STYLES: Record<Difficulty, string> = {
  easy: 'text-green-600 bg-green-50 border-green-200',
  medium: 'text-amber-600 bg-amber-50 border-amber-200',
  hard: 'text-red-600 bg-red-50 border-red-200',
};

const FILTERS = ['all', 'easy', 'medium', 'hard'] as const;

export default function ProblemsPage() {
  const [difficulty, setDifficulty] = useState<string>('all');
  const { data, isLoading, error } = useProblems(
    difficulty === 'all' ? undefined : difficulty,
  );

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-3xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Problems</h1>
          <div className="flex gap-1">
            {FILTERS.map((f) => (
              <button
                key={f}
                onClick={() => setDifficulty(f)}
                className={`px-3 py-1 rounded-full text-xs font-medium capitalize transition-colors ${
                  difficulty === f
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {isLoading && (
          <div className="flex justify-center py-16">
            <Loader2 className="animate-spin text-gray-400" size={28} />
          </div>
        )}
        {error && (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
            Failed to load problems.
          </div>
        )}

        <ul className="divide-y divide-gray-100 border border-gray-200 rounded-xl overflow-hidden">
          {data?.items.map((p) => (
            <li key={p.id}>
              <Link
                to={`/problems/${p.slug}`}
                className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="font-medium text-gray-900 truncate">{p.title}</span>
                  <span className="hidden sm:flex gap-1">
                    {p.tags.map((t) => (
                      <span
                        key={t}
                        className="px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 text-[10px]"
                      >
                        {t}
                      </span>
                    ))}
                  </span>
                </div>
                <span
                  className={`px-2 py-0.5 rounded-full border text-xs font-medium capitalize shrink-0 ${DIFFICULTY_STYLES[p.difficulty]}`}
                >
                  {p.difficulty}
                </span>
              </Link>
            </li>
          ))}
          {data && data.items.length === 0 && (
            <li className="px-4 py-8 text-center text-sm text-gray-400">
              No problems match this filter.
            </li>
          )}
        </ul>
      </div>
    </div>
  );
}

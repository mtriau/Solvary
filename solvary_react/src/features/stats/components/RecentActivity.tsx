import { Link } from 'react-router-dom';
import type { RecentSubmission } from '@/shared/types/api';

const VERDICT_STYLE: Record<string, string> = {
  accepted: 'bg-emerald-50 text-emerald-700',
  wrong_answer: 'bg-rose-50 text-rose-700',
  tle: 'bg-amber-50 text-amber-700',
  mle: 'bg-amber-50 text-amber-700',
  runtime_error: 'bg-orange-50 text-orange-700',
  compile_error: 'bg-orange-50 text-orange-700',
  internal_error: 'bg-gray-100 text-gray-600',
};

const VERDICT_LABEL: Record<string, string> = {
  accepted: 'Accepted',
  wrong_answer: 'Wrong Answer',
  tle: 'Time Limit',
  mle: 'Memory Limit',
  runtime_error: 'Runtime Error',
  compile_error: 'Compile Error',
  internal_error: 'Judge Error',
  queued: 'Queued',
  running: 'Running',
};

function relativeTime(iso: string): string {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function RecentActivity({ recent }: { recent: RecentSubmission[] }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <h2 className="text-sm font-semibold text-gray-900">Recent activity</h2>
      {recent.length === 0 ? (
        <p className="mt-3 text-xs text-gray-500">
          No submissions yet —{' '}
          <Link to="/problems" className="text-indigo-600 hover:underline">
            pick a problem
          </Link>{' '}
          to get started.
        </p>
      ) : (
        <ul className="mt-2 divide-y divide-gray-100">
          {recent.map((s) => (
            <li key={s.id} className="py-2 flex items-center gap-3 text-xs">
              <span
                className={`px-1.5 py-0.5 rounded font-medium whitespace-nowrap ${
                  VERDICT_STYLE[s.verdict] ?? 'bg-gray-100 text-gray-600'
                }`}
              >
                {VERDICT_LABEL[s.verdict] ?? s.verdict}
              </span>
              <Link
                to={`/problems/${s.problem_slug}`}
                className="flex-1 truncate text-gray-800 hover:text-indigo-600 font-medium"
              >
                {s.problem_title}
              </Link>
              <span className="text-gray-400 whitespace-nowrap">
                {s.language}
                {s.runtime_ms != null && s.verdict === 'accepted'
                  ? ` · ${s.runtime_ms}ms`
                  : ''}
                {' · '}
                {relativeTime(s.created_at)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

import { Swords } from 'lucide-react';

/**
 * Placeholder — M1 replaces this with the real problem list
 * (difficulty filters, tags, cursor pagination via TanStack Query).
 */
export default function ProblemsPage() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center px-4">
      <Swords size={40} className="text-gray-300 mb-4" />
      <h2 className="text-xl font-semibold text-gray-900 mb-2">Problems</h2>
      <p className="text-gray-500 max-w-sm">
        The challenge catalog lands in M1 — problems, difficulty filters, and
        streamed judge verdicts.
      </p>
    </div>
  );
}

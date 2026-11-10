import { useQuery } from '@tanstack/react-query';
import { fetchDrill, fetchDrills } from '@/shared/lib/api';

export const DRILL_KEYS = {
  all: ['drills'] as const,
  one: (slug: string) => ['drill', slug] as const,
};

/** Every drill grouped by topic with the user's progress. */
export function useDrills() {
  return useQuery({ queryKey: DRILL_KEYS.all, queryFn: fetchDrills });
}

/** One drill: statement, starter, provided tests, editorial, navigation. */
export function useDrill(slug: string) {
  return useQuery({
    queryKey: DRILL_KEYS.one(slug),
    queryFn: () => fetchDrill(slug),
    enabled: !!slug,
  });
}

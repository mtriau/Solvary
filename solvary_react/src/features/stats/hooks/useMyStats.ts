import { useQuery } from '@tanstack/react-query';
import { fetchMyStats } from '@/shared/lib/api';

export function useMyStats() {
  return useQuery({
    queryKey: ['stats', 'me'],
    queryFn: fetchMyStats,
    staleTime: 30_000,
  });
}

import { useQuery } from '@tanstack/react-query';
import { fetchSubmission } from '@/shared/lib/api';

/** One submission with its code; disabled until an id is chosen. Code never changes, so cache it for good. */
export function useSubmission(id: string | null | undefined) {
  return useQuery({
    queryKey: ['submission', id],
    queryFn: () => fetchSubmission(id as string),
    enabled: !!id,
    staleTime: Infinity,
  });
}

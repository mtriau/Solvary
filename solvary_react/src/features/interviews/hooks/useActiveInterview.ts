import { useQuery } from '@tanstack/react-query';
import { fetchActiveInterview } from '@/shared/lib/api';
import { INTERVIEW_KEYS } from './useInterviewSession';

/** The user's in-progress interview, if any — drives the top-bar pill. */
export function useActiveInterview(enabled = true) {
  return useQuery({
    queryKey: INTERVIEW_KEYS.active,
    queryFn: fetchActiveInterview,
    enabled,
    refetchInterval: 60_000,
  });
}

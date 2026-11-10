import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  abandonInterview,
  advanceInterview,
  fetchInterviewReview,
  fetchInterviewSession,
  fetchInterviewSessions,
  fetchInterviewTemplates,
  finishInterview,
  startInterview,
  switchInterviewStage,
} from '@/shared/lib/api';
import type { InterviewSessionDetail } from '@/shared/types/api';

export const INTERVIEW_KEYS = {
  templates: ['interview-templates'] as const,
  sessions: ['interview-sessions'] as const,
  active: ['interview-active'] as const,
  session: (id: string) => ['interview', id] as const,
  review: (id: string) => ['interview-review', id] as const,
};

export function useInterviewTemplates() {
  return useQuery({ queryKey: INTERVIEW_KEYS.templates, queryFn: fetchInterviewTemplates });
}

export function useInterviewSessions() {
  return useQuery({ queryKey: INTERVIEW_KEYS.sessions, queryFn: () => fetchInterviewSessions() });
}

export function useInterviewReview(id: string) {
  return useQuery({
    queryKey: INTERVIEW_KEYS.review(id),
    queryFn: () => fetchInterviewReview(id),
    enabled: !!id,
  });
}

/**
 * Session payload + the mutations that move it. The clock is re-synced on
 * every refetch (60 s) via `server_time`; mutations return the new payload
 * and replace the cache directly (no extra round trip).
 */
export function useInterviewSession(id: string) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: INTERVIEW_KEYS.session(id),
    queryFn: () => fetchInterviewSession(id),
    enabled: !!id,
    refetchInterval: 60_000,
  });

  const settle = (session: InterviewSessionDetail) => {
    queryClient.setQueryData(INTERVIEW_KEYS.session(id), session);
    queryClient.invalidateQueries({ queryKey: INTERVIEW_KEYS.active });
    queryClient.invalidateQueries({ queryKey: INTERVIEW_KEYS.sessions });
  };

  const advance = useMutation({ mutationFn: () => advanceInterview(id), onSuccess: settle });
  const switchStage = useMutation({
    mutationFn: (stage: number) => switchInterviewStage(id, stage),
    onSuccess: settle,
  });
  const finish = useMutation({ mutationFn: () => finishInterview(id), onSuccess: settle });
  const abandon = useMutation({ mutationFn: () => abandonInterview(id), onSuccess: settle });

  return { ...query, session: query.data, advance, switchStage, finish, abandon };
}

export function useStartInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { template_id: string; language?: string; duration_s?: number }) =>
      startInterview(vars),
    onSuccess: (session) => {
      queryClient.setQueryData(INTERVIEW_KEYS.session(session.id), session);
      queryClient.invalidateQueries({ queryKey: INTERVIEW_KEYS.active });
      queryClient.invalidateQueries({ queryKey: INTERVIEW_KEYS.sessions });
    },
  });
}

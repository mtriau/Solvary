import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { clearAiKey, fetchAiKey, setAiKey, testAiKey } from '@/shared/lib/api';
import type { AiKeyStatus } from '@/shared/types/api';

export const AI_KEY_QUERY = ['ai-key'] as const;
export const INTERVIEWER_KEYS = {
  all: ['interviewer'] as const,
  turns: (sessionId: string) => ['interviewer', sessionId] as const,
};

/** The user's Anthropic key status + save / test / remove (design §8). */
export function useAiKey() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: AI_KEY_QUERY, queryFn: fetchAiKey });

  const settle = (status: AiKeyStatus) => {
    queryClient.setQueryData(AI_KEY_QUERY, status);
    // the transcript payload carries key_source; refresh any open pane
    queryClient.invalidateQueries({ queryKey: INTERVIEWER_KEYS.all });
  };
  const save = useMutation({ mutationFn: (key: string) => setAiKey(key), onSuccess: settle });
  const remove = useMutation({ mutationFn: clearAiKey, onSuccess: settle });
  const test = useMutation({ mutationFn: testAiKey });

  return { status: query.data, isLoading: query.isLoading, save, remove, test };
}

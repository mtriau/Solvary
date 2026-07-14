import { useQuery } from '@tanstack/react-query';
import { fetchProblem, fetchProblems, fetchSubmissions } from '@/shared/lib/api';

export function useProblems(difficulty?: string) {
  return useQuery({
    queryKey: ['problems', difficulty ?? 'all'],
    queryFn: () => fetchProblems(difficulty ? { difficulty } : undefined),
  });
}

export function useProblem(slug: string) {
  return useQuery({
    queryKey: ['problem', slug],
    queryFn: () => fetchProblem(slug),
    enabled: !!slug,
  });
}

export function useMySubmissions(problemId?: string) {
  return useQuery({
    queryKey: ['submissions', problemId ?? 'all'],
    queryFn: () => fetchSubmissions(problemId),
    enabled: problemId !== undefined ? !!problemId : true,
  });
}

import { useQuery } from '@tanstack/react-query';
import { fetchPythonPrelude } from '@/shared/lib/api';

/** Stdlib modules and names every Python run/submission gets without an import. Static. */
export function usePythonPrelude() {
  return useQuery({
    queryKey: ['execution', 'prelude'],
    queryFn: fetchPythonPrelude,
    staleTime: Infinity,
  });
}

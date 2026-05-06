import { useQuery } from '@tanstack/react-query';
import { fetchStatsWithDistribution } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';

const STALE_MS = 300 * 1000;

/**
 * Portfolio stats; only fetches when signed in unless `enabled` is overridden.
 * @param {{ enabled?: boolean }} [options]
 */
export function useStats(options = {}) {
  const { isLoaded, isSignedIn } = useAuth();
  const enabled =
    options.enabled !== undefined ? options.enabled : Boolean(isLoaded && isSignedIn);

  return useQuery({
    queryKey: ['stats'],
    queryFn: fetchStatsWithDistribution,
    enabled,
    staleTime: STALE_MS,
  });
}

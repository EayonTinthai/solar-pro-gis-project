import { useQuery } from '@tanstack/react-query';
import { fetchBuildingsBbox } from '@/lib/api';

const STALE_MS = 60 * 1000;

/**
 * Buildings in current map bbox with filters.
 * @param {{ minLat: number, maxLat: number, minLon: number, maxLon: number } | null} bbox
 * @param {{ limit?: number, minConfidence?: number, enabled?: boolean }} options
 */
export function useBuildings(bbox, options = {}) {
  const {
    limit = 1000,
    minConfidence = 0.7,
    enabled = true,
  } = options;

  return useQuery({
    queryKey: ['buildings', 'bbox', bbox, limit, minConfidence],
    queryFn: () => fetchBuildingsBbox(bbox, { limit, minConfidence }),
    enabled: Boolean(enabled && bbox),
    staleTime: STALE_MS,
  });
}

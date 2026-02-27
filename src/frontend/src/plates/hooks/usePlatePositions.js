import { useQuery } from '@tanstack/react-query';
import { client, config } from '../config';
import usePlateStore from '../store';

/**
 * Fetch all positions for the current plate and sync them into Zustand.
 */
export function usePlatePositions() {
  const plateId = usePlateStore((s) => s.plateId);
  const setPositions = usePlateStore((s) => s.setPositions);

  return useQuery({
    queryKey: ['plate-positions', plateId],
    queryFn: async () => {
      const { data } = await client.get('/api/plate-positions/', {
        params: { plate: plateId },
      });
      // DRF may return paginated or flat list
      const results = Array.isArray(data) ? data : data.results ?? [];
      setPositions(results);
      return results;
    },
    enabled: !!plateId,
  });
}

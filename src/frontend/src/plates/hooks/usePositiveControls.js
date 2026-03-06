import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { client } from '../config';
import usePlateStore from '../store';

/**
 * Fetch all positive control options.
 */
export function usePositiveControls() {
  return useQuery({
    queryKey: ['positive-controls'],
    queryFn: async () => {
      const { data } = await client.get('/staff/api/positive-controls/');
      return data.results ?? data;
    },
    staleTime: 60_000, // Cache for 1 minute
  });
}

/**
 * Hook to set positive control on a plate position.
 */
export function useSetPositiveControl() {
  const queryClient = useQueryClient();
  const plateId = usePlateStore((s) => s.plateId);
  const updatePosition = usePlateStore((s) => s.updatePosition);

  return useMutation({
    mutationFn: async ({ positionId, positiveControlId }) => {
      const { data } = await client.post(
        `/api/plate-positions/${positionId}/set_positive_control/`,
        { positive_control_id: positiveControlId },
      );
      return data.position;
    },
    onSuccess: (position) => {
      updatePosition(position);
      queryClient.invalidateQueries({ queryKey: ['plate-positions', plateId] });
    },
  });
}

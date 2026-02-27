import { useMutation, useQueryClient } from '@tanstack/react-query';
import { client } from '../config';
import usePlateStore from '../store';

/**
 * Generic mutation helper that calls a PlatePosition action endpoint
 * and updates the Zustand store + React Query cache on success.
 */
export function usePositionAction() {
  const queryClient = useQueryClient();
  const plateId = usePlateStore((s) => s.plateId);
  const updatePosition = usePlateStore((s) => s.updatePosition);

  return useMutation({
    mutationFn: async ({ positionId, action, payload = {} }) => {
      const { data } = await client.post(
        `/api/plate-positions/${positionId}/${action}/`,
        payload,
      );
      return data.position;
    },
    onSuccess: (position) => {
      updatePosition(position);
      queryClient.invalidateQueries({ queryKey: ['plate-positions', plateId] });
    },
  });
}

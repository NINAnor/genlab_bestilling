import { useMutation, useQueryClient } from '@tanstack/react-query';
import { client } from '../config';
import usePlateStore from '../store';

/**
 * Mutation helper for plate-level actions (row/column operations).
 * Invalidates the plate-positions query on success to refresh the grid.
 */
export function usePlateAction() {
  const queryClient = useQueryClient();
  const plateId = usePlateStore((s) => s.plateId);
  const plateType = usePlateStore((s) => s.plateType);

  return useMutation({
    mutationFn: async ({ action, payload = {} }) => {
      const basePath = plateType === 'extraction'
        ? '/staff/api/extraction-plates'
        : '/staff/api/analysis-plates';
      const { data } = await client.post(
        `${basePath}/${plateId}/${action}/`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plate-positions', plateId] });
    },
  });
}

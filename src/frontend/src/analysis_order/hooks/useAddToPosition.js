import { useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { client } from '../config';
import useOrderStore from '../store';

/**
 * Mutation hook to add a single sample marker to a specific position.
 * Uses the plate-positions API endpoint.
 */
export function useAddToPosition() {
  const queryClient = useQueryClient();
  const clearSelectedPositionForAdd = useOrderStore((s) => s.clearSelectedPositionForAdd);

  return useMutation({
    mutationFn: async ({ positionId, sampleMarkerId }) => {
      const { data } = await client.post(`/api/plate-positions/${positionId}/add_sample_marker/`, {
        sample_marker_id: sampleMarkerId,
      });
      return data;
    },
    onSuccess: (data) => {
      toast.success(data.message || 'Sample marker added to position');
      clearSelectedPositionForAdd();
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['sample-markers'] });
      queryClient.invalidateQueries({ queryKey: ['analysis-plates-search'] });
      queryClient.invalidateQueries({ queryKey: ['analysisPlatePositions'] });
    },
    onError: (error) => {
      const message = error.response?.data?.error || 'Failed to add sample marker';
      toast.error(message);
    },
  });
}

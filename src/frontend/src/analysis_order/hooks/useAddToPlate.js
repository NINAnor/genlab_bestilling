import { useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { client } from '../config';
import useOrderStore from '../store';

/**
 * Mutation hook to add selected sample markers to an analysis plate.
 * @param {Object} params
 * @param {number} params.plateId - The plate ID to add markers to
 * @param {number[]} params.sampleMarkerIds - Array of unique sample marker IDs to add
 * @param {number} [params.replicates=1] - Number of replicates (1-12). When > 1, samples are placed horizontally
 */
export function useAddToPlate() {
  const queryClient = useQueryClient();
  const clearSelection = useOrderStore((s) => s.clearSelection);

  return useMutation({
    mutationFn: async ({ plateId, sampleMarkerIds, replicates = 1 }) => {
      const { data } = await client.post(
        `/staff/api/analysis-plates/${plateId}/add-sample-markers/`,
        { sample_marker_ids: sampleMarkerIds, replicates },
      );
      return data;
    },
    onSuccess: (data) => {
      toast.success(data.message || 'Sample markers added to plate');
      clearSelection();
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['sample-markers'] });
      queryClient.invalidateQueries({ queryKey: ['analysis-plates-search'] });
      queryClient.invalidateQueries({ queryKey: ['analysisPlatePositions'] });
    },
    onError: (error) => {
      const message = error.response?.data?.error || 'Failed to add sample markers';
      toast.error(message);
    },
  });
}

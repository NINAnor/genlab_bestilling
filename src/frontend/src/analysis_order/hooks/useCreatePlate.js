import { useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { client } from '../config';

/**
 * Mutation hook to create a new analysis plate.
 */
export function useCreatePlate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ name } = {}) => {
      const { data } = await client.post('/staff/api/analysis-plates/', { name });
      return data;
    },
    onSuccess: (data) => {
      toast.success(`Created plate ${data.label}`);
      // Invalidate plate queries to refresh the list
      queryClient.invalidateQueries({ queryKey: ['analysis-plates-search'] });
    },
    onError: (error) => {
      const message = error.response?.data?.error || 'Failed to create plate';
      toast.error(message);
    },
  });
}

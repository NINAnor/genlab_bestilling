import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { client } from '../config';

/**
 * Mutation hook to mark an analysis order as in progress.
 * @param {Object} options
 * @param {Function} options.onSuccess - Callback when order is successfully updated
 */
export function useSetOrderInProgress({ onSuccess } = {}) {
  return useMutation({
    mutationFn: async (orderId) => {
      const { data } = await client.post(
        `/staff/api/analysis-orders/${orderId}/in-progress/`,
      );
      return data;
    },
    onSuccess: (data) => {
      toast.success(data.message || 'Order marked as in progress');
      onSuccess?.();
    },
    onError: (error) => {
      const message = error.response?.data?.error || 'Failed to set order in progress';
      toast.error(message);
    },
  });
}

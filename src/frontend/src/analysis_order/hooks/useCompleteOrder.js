import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { client } from '../config';

/**
 * Mutation hook to mark an analysis order as completed.
 * @param {Object} options
 * @param {Function} options.onSuccess - Callback when order is successfully completed
 */
export function useCompleteOrder({ onSuccess } = {}) {
  return useMutation({
    mutationFn: async (orderId) => {
      const { data } = await client.post(`/staff/api/analysis-orders/${orderId}/complete/`);
      return data;
    },
    onSuccess: (data) => {
      toast.success(data.message || 'Order marked as completed');
      onSuccess?.();
    },
    onError: (error) => {
      const message = error.response?.data?.error || 'Failed to complete order';
      toast.error(message);
    },
  });
}

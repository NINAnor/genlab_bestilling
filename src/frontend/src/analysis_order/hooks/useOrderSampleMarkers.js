import { useQuery } from '@tanstack/react-query';
import { client } from '../config';
import useOrderStore from '../store';

/**
 * Build query params object from filters, excluding empty values.
 */
function buildFilterParams(filters) {
  const params = {};
  for (const [key, value] of Object.entries(filters || {})) {
    if (value !== '' && value != null) {
      params[key] = value;
    }
  }
  return params;
}

/**
 * Fetch all sample markers for the current analysis order with optional filters.
 * Syncs results into Zustand store.
 *
 * @param {Object} filters - Filter parameters (marker, species, sample_type, isolation_method, genlab_id)
 */
export function useOrderSampleMarkers(filters = {}) {
  const orderId = useOrderStore((s) => s.orderId);
  const setSampleMarkers = useOrderStore((s) => s.setSampleMarkers);

  const filterParams = buildFilterParams(filters);

  return useQuery({
    queryKey: ['order-sample-markers', orderId, filterParams],
    queryFn: async () => {
      const { data } = await client.get(`/staff/api/analysis-orders/${orderId}/sample-markers/`, {
        params: filterParams,
      });
      const results = Array.isArray(data) ? data : data.results ?? [];
      setSampleMarkers(results);
      return results;
    },
    enabled: !!orderId,
  });
}

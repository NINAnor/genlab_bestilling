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
 * Fetch all sample markers with optional filters including order.
 * Syncs results into Zustand store.
 *
 * @param {Object} filters - Filter parameters (order, marker, species, sample_type, isolation_method, genlab_id)
 */
export function useOrderSampleMarkers(filters = {}) {
  const orderId = useOrderStore((s) => s.orderId);
  const setSampleMarkers = useOrderStore((s) => s.setSampleMarkers);

  // Include orderId in filters if set
  const allFilters = { ...filters };
  if (orderId) {
    allFilters.order = orderId;
  }

  const filterParams = buildFilterParams(allFilters);

  return useQuery({
    queryKey: ['sample-markers', filterParams],
    queryFn: async () => {
      const { data } = await client.get('/staff/api/sample-markers/', {
        params: filterParams,
      });
      const results = Array.isArray(data) ? data : data.results ?? [];
      setSampleMarkers(results);
      return results;
    },
  });
}

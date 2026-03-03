import { useQuery } from '@tanstack/react-query';
import { client } from '../config';
import useOrderStore from '../store';

/**
 * Fetch analysis orders for filter dropdown.
 */
export function useAnalysisOrderFilterOptions() {
  return useQuery({
    queryKey: ['filter-analysis-orders'],
    queryFn: async () => {
      const { data } = await client.get('/staff/api/analysis-orders/', {
        params: { limit: 100 },
      });
      return data.results ?? data;
    },
    staleTime: 60_000,
  });
}

/**
 * Fetch markers allowed for this analysis order (or all if no order selected).
 */
export function useMarkerFilterOptions() {
  const orderId = useOrderStore((s) => s.orderId);
  return useQuery({
    queryKey: ['filter-markers', orderId],
    queryFn: async () => {
      const params = {};
      if (orderId) {
        params.analysis_order = orderId;
      }
      const { data } = await client.get('/api/markers/', { params });
      return data.results ?? data;
    },
    staleTime: 60_000,
  });
}

/**
 * Fetch species available in this analysis order (or all if no order selected).
 */
export function useSpeciesFilterOptions() {
  const orderId = useOrderStore((s) => s.orderId);
  return useQuery({
    queryKey: ['filter-species', orderId],
    queryFn: async () => {
      const params = {};
      if (orderId) {
        params.analysis_order = orderId;
      }
      const { data } = await client.get('/api/species/', { params });
      return data.results ?? data;
    },
    staleTime: 60_000,
  });
}

/**
 * Fetch all sample types for filter dropdown.
 */
export function useSampleTypeFilterOptions() {
  return useQuery({
    queryKey: ['filter-sample-types'],
    queryFn: async () => {
      const { data } = await client.get('/api/sample-types/');
      return data.results ?? data;
    },
    staleTime: 60_000,
  });
}

/**
 * Fetch all isolation methods for filter dropdown.
 */
export function useIsolationMethodFilterOptions() {
  return useQuery({
    queryKey: ['filter-isolation-methods'],
    queryFn: async () => {
      const { data } = await client.get('/api/isolation-methods/');
      return data.results ?? data;
    },
    staleTime: 60_000,
  });
}

/**
 * Search analysis plates by name with optional filters.
 * @param {string} searchTerm - Search term for plate name
 * @param {object} filters - Optional filters: { status, minAvailablePositions }
 */
export function useAnalysisPlateSearch(searchTerm, filters = {}) {
  return useQuery({
    queryKey: ['analysis-plates-search', searchTerm, filters],
    queryFn: async () => {
      const params = {};
      if (searchTerm) {
        params.search = searchTerm;
      }
      if (filters.status) {
        params.status = filters.status;
      }
      if (filters.minAvailablePositions) {
        params.min_available_positions = filters.minAvailablePositions;
      }
      // Only limit results when no filters are active
      const hasFilters = searchTerm || filters.status || filters.minAvailablePositions;
      if (!hasFilters) {
        params.limit = 10;
      }
      const { data } = await client.get('/staff/api/analysis-plates/', {
        params,
      });
      return data.results ?? data;
    },
    staleTime: 30_000,
    placeholderData: (prev) => prev,
  });
}

/**
 * Fetch positions for a specific plate.
 */
export function usePlatePositions(plateId) {
  return useQuery({
    queryKey: ['analysisPlatePositions', plateId],
    queryFn: async () => {
      const { data } = await client.get('/api/plate-positions/', {
        params: { plate: plateId },
      });
      return data.results ?? data;
    },
    enabled: !!plateId,
    staleTime: 30_000,
  });
}

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

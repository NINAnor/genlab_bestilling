import { useQuery } from '@tanstack/react-query';
import { client } from '../config';
import useOrderStore from '../store';

/**
 * Fetch analysis orders for filter dropdown with optional search.
 */
export function useAnalysisOrderFilterOptions(searchTerm = '') {
  return useQuery({
    queryKey: ['filter-analysis-orders', searchTerm],
    queryFn: async () => {
      const params = { limit: 50 };
      if (searchTerm) {
        params.search = searchTerm;
      }
      const { data } = await client.get('/staff/api/analysis-orders/', { params });
      return data.results ?? data;
    },
    staleTime: 60_000,
  });
}

/**
 * Search analysis orders (for async select).
 */
export async function searchAnalysisOrders(searchTerm = '') {
  const params = { limit: 50 };
  if (searchTerm) {
    params.search = searchTerm;
  }
  const { data } = await client.get('/staff/api/analysis-orders/', { params });
  const results = data.results ?? data;
  return results.map((o) => ({
    value: o.id,
    label: o.label,
  }));
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
 * Fetch all markers (for plate filtering).
 */
export function useAllMarkers() {
  return useQuery({
    queryKey: ['all-markers'],
    queryFn: async () => {
      const { data } = await client.get('/api/markers/');
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
 * @param {object} filters - Optional filters: { status, minAvailablePositions, analysisType, marker }
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
      if (filters.analysisType) {
        params.analysis_type = filters.analysisType;
      }
      if (filters.marker) {
        params.marker = filters.marker;
      }
      // Only limit results when no filters are active
      const hasFilters =
        searchTerm ||
        filters.status ||
        filters.minAvailablePositions ||
        filters.analysisType ||
        filters.marker;
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

/**
 * Fetch all analysis types for plate creation.
 */
export function useAnalysisTypes() {
  return useQuery({
    queryKey: ['analysis-types'],
    queryFn: async () => {
      const { data } = await client.get('/api/analysis-types/');
      return data.results ?? data;
    },
    staleTime: 60_000,
  });
}

/**
 * Fetch markers filtered by analysis type.
 * @param {number|null} analysisTypeId - Filter by analysis type, or null for all
 */
export function useMarkersForAnalysisType(analysisTypeId) {
  return useQuery({
    queryKey: ['markers-for-analysis-type', analysisTypeId],
    queryFn: async () => {
      const params = {};
      if (analysisTypeId) {
        params.analysis_type = analysisTypeId;
      }
      const { data } = await client.get('/api/markers/', { params });
      return data.results ?? data;
    },
    staleTime: 60_000,
    enabled: !!analysisTypeId,
  });
}

import { useInfiniteQuery } from '@tanstack/react-query';
import { useCallback, useEffect } from 'react';
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
 * Extract cursor from URL (handles both full URL and query string).
 */
function extractCursor(url) {
  if (!url) return null;
  try {
    const urlObj = new URL(url, window.location.origin);
    return urlObj.searchParams.get('cursor');
  } catch {
    return null;
  }
}

/**
 * Fetch all sample markers with optional filters including order.
 * Uses cursor-based pagination with infinite loading.
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

  const query = useInfiniteQuery({
    queryKey: ['sample-markers', filterParams],
    queryFn: async ({ pageParam }) => {
      const params = { ...filterParams };
      if (pageParam) {
        params.cursor = pageParam;
      }
      const { data } = await client.get('/staff/api/sample-markers/', {
        params,
      });
      return data;
    },
    initialPageParam: null,
    getNextPageParam: (lastPage) => extractCursor(lastPage.next),
    staleTime: 30_000,
  });

  // Sync all pages to store whenever data changes
  useEffect(() => {
    if (query.data?.pages) {
      const allMarkers = query.data.pages.flatMap((page) => page.results ?? []);
      setSampleMarkers(allMarkers);
    }
  }, [query.data, setSampleMarkers]);

  // Convenience function to load all remaining pages
  const fetchAllPages = useCallback(async () => {
    while (query.hasNextPage && !query.isFetchingNextPage) {
      await query.fetchNextPage();
    }
  }, [query]);

  return {
    ...query,
    fetchAllPages,
    // Flatten all pages for direct access
    allData: query.data?.pages.flatMap((page) => page.results ?? []) ?? [],
  };
}

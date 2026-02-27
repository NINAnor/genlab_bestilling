import { useQuery } from '@tanstack/react-query';
import { client } from '../config';

/**
 * Search samples via /api/samples/?search=<term>.
 * The backend filter does an OR across genlab_id (istartswith) and guid (iexact).
 * Extra filter params can be passed (e.g. is_isolated, is_invalid).
 */
export function useSampleSearch(term, extraParams = {}) {
  return useQuery({
    queryKey: ['sample-search', term, extraParams],
    queryFn: async () => {
      const { data } = await client.get('/api/samples/', {
        params: { search: term.trim(), ...extraParams },
      });
      return data.results ?? data;
    },
    enabled: term.length >= 2,
    staleTime: 30_000,
    placeholderData: (prev) => prev,
  });
}

/**
 * Search sample-marker-analyses via /api/sample-marker-analysis/?search=<term>.
 * The backend filter does an OR across sample__genlab_id (istartswith) and sample__guid (iexact).
 */
export function useSampleMarkerSearch(term) {
  return useQuery({
    queryKey: ['sample-marker-search', term],
    queryFn: async () => {
      const { data } = await client.get('/api/sample-marker-analysis/', {
        params: { search: term.trim() },
      });
      return data.results ?? data;
    },
    enabled: term.length >= 2,
    staleTime: 30_000,
    placeholderData: (prev) => prev,
  });
}

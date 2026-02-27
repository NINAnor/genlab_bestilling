import { useState, useEffect, useRef } from 'react';
import toast from 'react-hot-toast';
import { useSampleSearch, useSampleMarkerSearch } from '../hooks/useSearch';
import { usePositionAction } from '../hooks/usePositionAction';

/* ── icons ───────────────────────────────────────────────────── */

const IconSearch = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
  </svg>
);

const IconPlus = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
  </svg>
);

const IconSpinner = () => (
  <svg className="w-4 h-4 animate-spin text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
  </svg>
);

/* ── debounce hook ───────────────────────────────────────────── */

function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debouncedValue;
}

/* ── result row components ───────────────────────────────────── */

function SampleRow({ sample, onAdd, isPending }) {
  return (
    <div className="flex items-center justify-between gap-2 rounded-lg border border-gray-100 bg-gray-50/50 px-3 py-2.5 hover:border-indigo-200 hover:bg-indigo-50/30 transition-colors">
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-gray-900 truncate">{sample.genlab_id}</p>
        <p className="text-xs text-gray-500 truncate">
          {sample.name}
          {sample.species?.name && <> &middot; {sample.species.name}</>}
          {sample.type?.name && <> &middot; {sample.type.name}</>}
        </p>
        {sample.location && (
          <p className="text-xs text-gray-400 truncate mt-0.5">
            {String(sample.location.name ?? sample.location)}
          </p>
        )}
      </div>
      <button
        type="button"
        onClick={() => onAdd(sample.id)}
        disabled={isPending}
        className="flex-shrink-0 inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium
                   bg-indigo-600 text-white shadow-sm
                   hover:bg-indigo-700 active:bg-indigo-800
                   transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        title="Add to position"
      >
        <IconPlus /> Add
      </button>
    </div>
  );
}

function SampleMarkerRow({ marker, onAdd, isPending }) {
  const sample = marker.sample;
  return (
    <div className="flex items-center justify-between gap-2 rounded-lg border border-gray-100 bg-gray-50/50 px-3 py-2.5 hover:border-indigo-200 hover:bg-indigo-50/30 transition-colors">
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-gray-900 truncate">
          {sample?.genlab_id ?? `Sample #${marker.sample?.id ?? '?'}`}
        </p>
        <p className="text-xs text-gray-500 truncate">
          Marker: {marker.marker ?? `#${marker.id}`}
          {sample?.name && <> &middot; {sample.name}</>}
        </p>
        {sample?.species?.name && (
          <p className="text-xs text-gray-400 truncate mt-0.5">{sample.species.name}</p>
        )}
      </div>
      <button
        type="button"
        onClick={() => onAdd(marker.id)}
        disabled={isPending}
        className="flex-shrink-0 inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium
                   bg-indigo-600 text-white shadow-sm
                   hover:bg-indigo-700 active:bg-indigo-800
                   transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        title="Add to position"
      >
        <IconPlus /> Add
      </button>
    </div>
  );
}

/* ── main component ──────────────────────────────────────────── */

/**
 * Search panel shown for empty wells.
 * For extraction plates → searches samples, calls add_sample.
 * For analysis plates  → searches sample markers, calls add_sample_marker.
 *
 * Props:
 *   positionId – the plate position pk
 *   plateType  – "extraction" | "analysis"
 *   coordinate – e.g. "A1" (for toast messages)
 */
export default function SearchPanel({ positionId, plateType, coordinate }) {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const debouncedQuery = useDebounce(query, 300);
  const inputRef = useRef(null);
  const actionMutation = usePositionAction();

  const isExtraction = plateType === 'extraction';

  const sampleSearch = useSampleSearch(
    isExtraction ? debouncedQuery : '',
    { is_isolated: true, is_invalid: false, position__isnull: true },
  );
  const markerSearch = useSampleMarkerSearch(!isExtraction ? debouncedQuery : '');

  const search = isExtraction ? sampleSearch : markerSearch;
  const results = search.data ?? [];

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleAdd = (entityId) => {
    const action = isExtraction ? 'add_sample' : 'add_sample_marker';
    const payload = isExtraction ? { sample_id: entityId } : { sample_marker_id: entityId };

    actionMutation.mutate(
      { positionId, action, payload },
      {
        onSuccess: () => {
          toast.success(`Added to ${coordinate}`);
          setQuery('');
          setIsOpen(false);
        },
        onError: (err) =>
          toast.error(err.response?.data?.error ?? 'Failed to add'),
      },
    );
  };

  /* collapsed: show open button */
  if (!isOpen) {
    return (
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium
                   bg-indigo-600 text-white shadow-sm
                   hover:bg-indigo-700 active:bg-indigo-800
                   transition-colors"
      >
        <IconSearch />
        {isExtraction ? 'Search & Add Sample' : 'Search & Add Sample Marker'}
      </button>
    );
  }

  /* expanded: input + results */
  return (
    <div className="space-y-3">
      {/* Search input */}
      <div className="relative">
        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
          {search.isFetching ? <IconSpinner /> : <IconSearch />}
        </div>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by Genlab ID or GUID…"
          className="block w-full rounded-lg border border-gray-300 bg-white py-2 pl-9 pr-3 text-sm
                     placeholder:text-gray-400
                     focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none
                     transition-colors"
        />
      </div>

      {/* Hint / status text */}
      {debouncedQuery.length < 2 && (
        <p className="text-xs text-gray-400 text-center">
          Type at least 2 characters to search
        </p>
      )}

      {debouncedQuery.length >= 2 && !search.isFetching && results.length === 0 && (
        <p className="text-xs text-gray-400 text-center">
          No results found for &ldquo;{debouncedQuery}&rdquo;
        </p>
      )}

      {/* Results list */}
      {results.length > 0 && (
        <div className="space-y-1.5 max-h-64 overflow-y-auto pr-0.5">
          {isExtraction
            ? results.map((s) => (
                <SampleRow key={s.id} sample={s} onAdd={handleAdd} isPending={actionMutation.isPending} />
              ))
            : results.map((m) => (
                <SampleMarkerRow key={m.id} marker={m} onAdd={handleAdd} isPending={actionMutation.isPending} />
              ))}
        </div>
      )}

      {/* Cancel button */}
      <button
        type="button"
        onClick={() => { setQuery(''); setIsOpen(false); }}
        className="w-full px-3 py-1.5 rounded-md text-xs font-medium
                   bg-white text-gray-600 ring-1 ring-inset ring-gray-300
                   hover:bg-gray-50 transition-colors"
      >
        Cancel
      </button>
    </div>
  );
}

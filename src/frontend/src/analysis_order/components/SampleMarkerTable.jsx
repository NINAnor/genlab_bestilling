import { useMemo, useRef, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
} from '@tanstack/react-table';
import { useVirtualizer } from '@tanstack/react-virtual';
import classnames from 'classnames';
import useOrderStore from '../store';

// eslint-disable-next-line react/prop-types
function IndeterminateCheckbox({ indeterminate, checked, onChange, ...rest }) {
  return (
    <input
      type="checkbox"
      checked={checked}
      onChange={onChange}
      ref={(el) => {
        if (el) el.indeterminate = indeterminate;
      }}
      className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
      {...rest}
    />
  );
}

const columns = [
  {
    id: 'select',
    header: ({ table }) => (
      <IndeterminateCheckbox
        checked={table.getIsAllRowsSelected()}
        indeterminate={table.getIsSomeRowsSelected()}
        onChange={table.getToggleAllRowsSelectedHandler()}
      />
    ),
    cell: ({ row }) => (
      <IndeterminateCheckbox
        checked={row.getIsSelected()}
        onChange={row.getToggleSelectedHandler()}
        onClick={(e) => e.stopPropagation()}
      />
    ),
    enableSorting: false,
  },
  {
    id: 'genlab_id',
    accessorKey: 'sample_genlab_id',
    header: 'Sample',
    cell: ({ row }) => (
      <span className="text-sm font-mono text-gray-900">
        {row.original.sample_genlab_id ?? row.original.sample_name ?? '—'}
      </span>
    ),
    sortField: 'genlab_id',
  },
  {
    id: 'marker',
    accessorKey: 'marker_name',
    header: 'Marker',
    cell: ({ getValue }) => (
      <span className="text-sm text-gray-900">{getValue() ?? '—'}</span>
    ),
    sortField: 'marker',
  },
  {
    id: 'species',
    accessorKey: 'sample_species_name',
    header: 'Species',
    cell: ({ getValue }) => (
      <span className="text-sm text-gray-600">{getValue() ?? '—'}</span>
    ),
    sortField: 'species',
  },
  {
    accessorKey: 'sample_isolation_methods',
    header: 'Isolation',
    cell: ({ getValue }) => {
      const methods = getValue();
      const text = methods?.length ? methods.map((m) => m.name).join(', ') : '—';
      return <span className="text-sm text-gray-600">{text}</span>;
    },
  },
  {
    id: 'sample_position',
    accessorKey: 'sample_position',
    header: 'Sample Position',
    cell: ({ getValue }) => (
      <span className="text-sm font-mono text-gray-600">{getValue() ?? '—'}</span>
    ),
    sortField: 'sample_position',
  },
  {
    accessorKey: 'analysis_position',
    header: 'Analysis Position',
    cell: ({ getValue }) => (
      <span className="text-sm font-mono text-gray-600">{getValue() ?? '—'}</span>
    ),
  },
  {
    id: 'pcr',
    header: 'PCR',
    accessorFn: (row) => !!row.analysis_position,
    cell: ({ getValue }) => (
      <span className={`text-sm font-medium ${getValue() ? 'text-emerald-600' : 'text-gray-400'}`}>
        {getValue() ? '✓' : '—'}
      </span>
    ),
  },
  {
    id: 'analyzing',
    header: 'Analyzing',
    accessorFn: (row) => row.is_analyzing,
    cell: ({ getValue }) => {
      const { count, total } = getValue() || { count: 0, total: 0 };
      if (total === 0) return <span className="text-sm text-gray-400">—</span>;
      const pct = Math.round((count / total) * 100);
      return (
        <div className="flex items-center gap-2">
          <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full ${pct === 100 ? 'bg-emerald-500' : 'bg-amber-500'}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-xs text-gray-600">{count}/{total}</span>
        </div>
      );
    },
  },
  {
    id: 'output',
    header: 'Results',
    accessorFn: (row) => row.has_output,
    cell: ({ getValue }) => {
      const { count, total } = getValue() || { count: 0, total: 0 };
      if (total === 0) return <span className="text-sm text-gray-400">—</span>;
      const pct = Math.round((count / total) * 100);
      return (
        <div className="flex items-center gap-2">
          <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full ${pct === 100 ? 'bg-emerald-500' : 'bg-amber-500'}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-xs text-gray-600">{count}/{total}</span>
        </div>
      );
    },
  },
];

// Sort indicator component
// eslint-disable-next-line react/prop-types
function SortIndicator({ direction }) {
  if (!direction) {
    return (
      <span className="text-gray-300 ml-1">↕</span>
    );
  }
  return (
    <span className="text-blue-600 ml-1">
      {direction === 'asc' ? '↑' : '↓'}
    </span>
  );
}

export default function SampleMarkerTable({
  fetchNextPage,
  hasNextPage,
  isFetchingNextPage,
  totalCount,
}) {
  const sampleMarkers = useOrderStore((s) => s.sampleMarkers);
  const sampleMarkerIds = useOrderStore((s) => s.sampleMarkerIds);
  const selectedMarkerIds = useOrderStore((s) => s.selectedMarkerIds);
  const toggleMarkerSelection = useOrderStore((s) => s.toggleMarkerSelection);
  const sorting = useOrderStore((s) => s.sorting);
  const toggleSorting = useOrderStore((s) => s.toggleSorting);

  // Build ordered data array from ids and object
  const data = useMemo(
    () => sampleMarkerIds.map((id) => sampleMarkers[id]).filter(Boolean),
    [sampleMarkerIds, sampleMarkers],
  );

  // Convert store selection to TanStack Table format (keyed by row id)
  const rowSelection = useMemo(() => {
    const selection = {};
    Object.keys(selectedMarkerIds).forEach((id) => {
      selection[id] = true;
    });
    return selection;
  }, [selectedMarkerIds]);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    enableRowSelection: true,
    getRowId: (row) => String(row.id),
    state: {
      rowSelection,
    },
    onRowSelectionChange: (updater) => {
      const newSelection = typeof updater === 'function' ? updater(rowSelection) : updater;
      // Sync with store - find the diff
      const prevKeys = new Set(Object.keys(rowSelection));
      const newKeys = new Set(Object.keys(newSelection));

      // Added
      newKeys.forEach((id) => {
        if (!prevKeys.has(id)) {
          toggleMarkerSelection(id);
        }
      });

      // Removed
      prevKeys.forEach((id) => {
        if (!newKeys.has(id)) {
          toggleMarkerSelection(id);
        }
      });
    },
  });

  const { rows } = table.getRowModel();
  const parentRef = useRef(null);

  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 44, // Approximate row height in pixels
    overscan: 10,
  });

  const virtualRows = virtualizer.getVirtualItems();

  // Load more when scrolling near bottom
  const handleScroll = useCallback(() => {
    if (!parentRef.current || !hasNextPage || isFetchingNextPage) return;

    const { scrollTop, scrollHeight, clientHeight } = parentRef.current;
    // Load more when within 200px of the bottom
    if (scrollHeight - scrollTop - clientHeight < 200) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  // Attach scroll listener
  useEffect(() => {
    const el = parentRef.current;
    if (!el) return;
    el.addEventListener('scroll', handleScroll);
    return () => el.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  const selectedCount = Object.keys(selectedMarkerIds).length;

  if (data.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400 italic">
        No sample markers found
      </div>
    );
  }

  return (
    <div className="overflow-hidden">
      <div
        ref={parentRef}
        className="overflow-auto max-h-[600px]"
      >
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50 sticky top-0 z-10">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const { sortField } = header.column.columnDef;
                  const isSortable = !!sortField;
                  const isSorted = sorting.field === sortField;
                  const sortDirection = isSorted ? sorting.direction : null;

                  return (
                    <th
                      key={header.id}
                      className={classnames(
                        'px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider select-none bg-gray-50',
                        isSortable && 'cursor-pointer hover:bg-gray-100',
                      )}
                      onClick={isSortable ? () => toggleSorting(sortField) : undefined}
                    >
                      <div className="flex items-center">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {isSortable && <SortIndicator direction={sortDirection} />}
                      </div>
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {/* Top padding row */}
            {virtualRows.length > 0 && virtualRows[0].start > 0 && (
              <tr>
                <td
                  colSpan={columns.length}
                  style={{ height: virtualRows[0].start }}
                />
              </tr>
            )}
            {virtualRows.map((virtualRow) => {
              const row = rows[virtualRow.index];
              return (
                <tr
                  key={row.original.id ?? row.id}
                  data-index={virtualRow.index}
                  ref={virtualizer.measureElement}
                  onClick={() => toggleMarkerSelection(row.original.id)}
                  className={classnames(
                    'cursor-pointer hover:bg-gray-50 transition-colors',
                    row.getIsSelected() && 'bg-blue-50',
                  )}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-3 py-2 whitespace-nowrap">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              );
            })}
            {/* Bottom padding row */}
            {virtualRows.length > 0 && (
              <tr>
                <td
                  colSpan={columns.length}
                  style={{
                    height:
                      virtualizer.getTotalSize() -
                      (virtualRows[virtualRows.length - 1]?.end ?? 0),
                  }}
                />
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="mt-2 text-xs text-gray-400 text-right flex items-center justify-between">
        <div>
          {isFetchingNextPage && (
            <span className="text-blue-500">Loading more...</span>
          )}
          {!isFetchingNextPage && hasNextPage && (
            <button
              type="button"
              onClick={() => fetchNextPage()}
              className="text-blue-600 hover:underline"
            >
              Load more
            </button>
          )}
        </div>
        <div>
          {selectedCount > 0 && (
            <span className="mr-2 text-blue-600 font-medium">
              {selectedCount} selected
            </span>
          )}
          {data.length}{totalCount ? ` / ${totalCount}` : ''} sample marker{data.length !== 1 ? 's' : ''}
        </div>
      </div>
    </div>
  );
}

SampleMarkerTable.propTypes = {
  fetchNextPage: PropTypes.func.isRequired,
  hasNextPage: PropTypes.bool,
  isFetchingNextPage: PropTypes.bool,
  totalCount: PropTypes.number,
};

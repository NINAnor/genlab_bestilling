import { useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
} from '@tanstack/react-table';
import classnames from 'classnames';
import useOrderStore from '../store';

function SortIcon({ isSorted }) {
  if (!isSorted) {
    return (
      <svg className="w-3 h-3 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
        <path d="M7 3l3-3 3 3H7zm0 14l3 3 3-3H7z" />
      </svg>
    );
  }
  return (
    <svg className="w-3 h-3 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
      {isSorted === 'asc' ? (
        <path d="M7 10l3-3 3 3H7z" />
      ) : (
        <path d="M7 10l3 3 3-3H7z" />
      )}
    </svg>
  );
}

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
    accessorKey: 'sample_genlab_id',
    header: 'Sample',
    cell: ({ row }) => (
      <span className="text-sm font-mono text-gray-900">
        {row.original.sample_genlab_id ?? row.original.sample_name ?? '—'}
      </span>
    ),
    sortingFn: (rowA, rowB) => {
      const a = (rowA.original.sample_genlab_id ?? rowA.original.sample_name ?? '').toLowerCase();
      const b = (rowB.original.sample_genlab_id ?? rowB.original.sample_name ?? '').toLowerCase();
      return a.localeCompare(b);
    },
  },
  {
    accessorKey: 'marker_name',
    header: 'Marker',
    cell: ({ getValue }) => (
      <span className="text-sm text-gray-900">{getValue() ?? '—'}</span>
    ),
  },
  {
    accessorKey: 'sample_species_name',
    header: 'Species',
    cell: ({ getValue }) => (
      <span className="text-sm text-gray-600">{getValue() ?? '—'}</span>
    ),
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
    accessorKey: 'sample_position',
    header: 'Sample Position',
    cell: ({ getValue }) => (
      <span className="text-sm font-mono text-gray-600">{getValue() ?? '—'}</span>
    ),
    sortingFn: (rowA, rowB) => {
      const a = rowA.original.sample_position_index ?? Infinity;
      const b = rowB.original.sample_position_index ?? Infinity;
      return a - b;
    },
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
    sortingFn: (rowA, rowB) => {
      const a = rowA.original.analysis_position ? 1 : 0;
      const b = rowB.original.analysis_position ? 1 : 0;
      return a - b;
    },
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
    sortingFn: (rowA, rowB) => {
      const a = rowA.original.is_analyzing;
      const b = rowB.original.is_analyzing;
      const pctA = a?.total ? a.count / a.total : 0;
      const pctB = b?.total ? b.count / b.total : 0;
      return pctA - pctB;
    },
  },
  {
    id: 'output',
    header: 'Output',
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
    sortingFn: (rowA, rowB) => {
      const a = rowA.original.has_output;
      const b = rowB.original.has_output;
      const pctA = a?.total ? a.count / a.total : 0;
      const pctB = b?.total ? b.count / b.total : 0;
      return pctA - pctB;
    },
  },
];

export default function SampleMarkerTable() {
  const sampleMarkers = useOrderStore((s) => s.sampleMarkers);
  const selectedMarkerIds = useOrderStore((s) => s.selectedMarkerIds);
  const toggleMarkerSelection = useOrderStore((s) => s.toggleMarkerSelection);

  const data = useMemo(() => Object.values(sampleMarkers), [sampleMarkers]);

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
    getSortedRowModel: getSortedRowModel(),
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

  const selectedCount = Object.keys(selectedMarkerIds).length;

  if (data.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400 italic">
        No sample markers in this order yet
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  onClick={header.column.getCanSort() ? header.column.getToggleSortingHandler() : undefined}
                  className={classnames(
                    'px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider select-none',
                    header.column.getCanSort() && 'cursor-pointer hover:bg-gray-100',
                  )}
                >
                  <div className="flex items-center gap-1">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {header.column.getCanSort() && (
                      <SortIcon isSorted={header.column.getIsSorted()} />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.original.id ?? row.id}
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
          ))}
        </tbody>
      </table>
      <div className="mt-2 text-xs text-gray-400 text-right">
        {selectedCount > 0 && (
          <span className="mr-2 text-blue-600 font-medium">
            {selectedCount} selected
          </span>
        )}
        {data.length} sample marker{data.length !== 1 ? 's' : ''}
      </div>
    </div>
  );
}

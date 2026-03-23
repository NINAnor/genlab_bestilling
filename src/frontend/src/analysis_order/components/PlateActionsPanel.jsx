import { useState } from 'react';
import PropTypes from 'prop-types';
import {
  useEmptyPositions,
  useReservePositions,
} from '../hooks/useCreatePlate';

const ROWS = 'ABCDEFGH'.split('');
const COLS = Array.from({ length: 12 }, (_, i) => i + 1);

/**
 * Inline panel for bulk row/column operations on a plate.
 */
export default function PlateActionsPanel({ plateId }) {
  const [selectedRow, setSelectedRow] = useState('');
  const [selectedColumn, setSelectedColumn] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);

  const emptyPositions = useEmptyPositions();
  const reservePositions = useReservePositions();

  const isPending = emptyPositions.isPending || reservePositions.isPending;

  const handleAction = (mutation) => {
    if ((!selectedRow && !selectedColumn) || !plateId) return;
    const params = { plateId };
    if (selectedRow) params.row = selectedRow;
    if (selectedColumn) params.column = parseInt(selectedColumn, 10);
    mutation.mutate(params);
  };

  if (!plateId) return null;

  return (
    <div className="mb-4 border border-gray-200 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-3 py-2 bg-gray-50 text-left text-sm font-medium text-gray-700 hover:bg-gray-100 flex items-center justify-between"
      >
        <span>Bulk Actions (Row/Column)</span>
        <svg
          className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isExpanded && (
        <div className="p-3 space-y-4 bg-white">
          {/* Row/Column Selection */}
          <div className="flex items-center gap-2 flex-wrap">
            <select
              value={selectedRow}
              onChange={(e) => setSelectedRow(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Row (optional)</option>
              {ROWS.map((row) => (
                <option key={row} value={row}>
                  {row}
                </option>
              ))}
            </select>
            <select
              value={selectedColumn}
              onChange={(e) => setSelectedColumn(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Column (optional)</option>
              {COLS.map((col) => (
                <option key={col} value={col}>
                  {col}
                </option>
              ))}
            </select>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => handleAction(emptyPositions)}
              disabled={(!selectedRow && !selectedColumn) || isPending}
              className="px-2 py-1 text-xs font-medium rounded bg-red-100 text-red-700 hover:bg-red-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Empty
            </button>
            <button
              type="button"
              onClick={() => handleAction(reservePositions)}
              disabled={(!selectedRow && !selectedColumn) || isPending}
              className="px-2 py-1 text-xs font-medium rounded bg-amber-100 text-amber-700 hover:bg-amber-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Reserve
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

PlateActionsPanel.propTypes = {
  plateId: PropTypes.string,
};

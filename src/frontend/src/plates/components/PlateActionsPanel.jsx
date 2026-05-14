import { useState } from 'react';
import toast from 'react-hot-toast';
import { usePlateAction } from '../hooks/usePlateActions';

const ROWS = 'ABCDEFGH'.split('');
const COLS = Array.from({ length: 12 }, (_, i) => i + 1);

/**
 * Panel for bulk row/column operations on a plate.
 */
export default function PlateActionsPanel() {
  const [selectedRow, setSelectedRow] = useState('');
  const [selectedColumn, setSelectedColumn] = useState('');
  const plateAction = usePlateAction();

  const handleAction = (action, label) => {
    if (!selectedRow && !selectedColumn) {
      toast.error('Please select a row or column');
      return;
    }
    const payload = {};
    if (selectedRow) payload.row = selectedRow;
    if (selectedColumn) payload.column = parseInt(selectedColumn, 10);

    plateAction.mutate(
      { action, payload },
      {
        onSuccess: (data) => toast.success(data.message),
        onError: (err) => toast.error(err.response?.data?.error ?? `Failed to ${label}`),
      },
    );
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-100 bg-gray-50/60">
        <h4 className="text-sm font-semibold text-gray-900 tracking-wide uppercase">
          Bulk Actions
        </h4>
      </div>
      <div className="px-5 py-4 space-y-6">
        {/* Row/Column Selection */}
        <div className="space-y-3">
          <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Select Row and/or Column
          </h5>
          <div className="flex items-center gap-2">
            <select
              value={selectedRow}
              onChange={(e) => setSelectedRow(e.target.value)}
              className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg
                         focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:outline-none
                         transition-colors"
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
              className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg
                         focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:outline-none
                         transition-colors"
            >
              <option value="">Column (optional)</option>
              {COLS.map((col) => (
                <option key={col} value={col}>
                  {col}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => handleAction('empty', 'empty')}
            disabled={(!selectedRow && !selectedColumn) || plateAction.isPending}
            className="flex-1 px-3 py-2 rounded-lg text-sm font-medium
                       bg-red-50 text-red-700 ring-1 ring-inset ring-red-200
                       hover:bg-red-100 active:bg-red-200
                       disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Empty
          </button>
          <button
            type="button"
            onClick={() => handleAction('reserve', 'reserve')}
            disabled={(!selectedRow && !selectedColumn) || plateAction.isPending}
            className="flex-1 px-3 py-2 rounded-lg text-sm font-medium
                       bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200
                       hover:bg-amber-100 active:bg-amber-200
                       disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Reserve
          </button>
        </div>
      </div>
    </div>
  );
}

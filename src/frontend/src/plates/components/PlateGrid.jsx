import { useState, useCallback } from 'react';
import classnames from 'classnames';
import Well from './Well';
import usePlateStore from '../store';
import { usePlatePositions } from '../hooks/usePlatePositions';

const ROWS = 'ABCDEFGH'.split('');
const COLS = Array.from({ length: 12 }, (_, i) => i + 1);

/**
 * Convert row letter + column number to the column-wise position index
 * used by the Django model (A1=0, B1=1 … H1=7, A2=8 …).
 */
export function toPositionIndex(row, col) {
  const rowIdx = ROWS.indexOf(row);
  return (col - 1) * ROWS.length + rowIdx;
}

/**
 * Get the text content for a cell (for copy/paste to Excel).
 */
function getCellText(position, plateType) {
  if (!position) return '';
  if (position.is_reserved) return position.positive_control_name ?? 'Reserved';
  if (plateType === 'extraction' && position.sample_raw) {
    return position.sample_raw.genlab_id ?? position.sample_raw.name ?? '';
  }
  if (plateType === 'analysis' && position.sample_marker) {
    return position.sample_marker.sample_genlab_id ?? position.sample_marker.sample_name ?? '';
  }
  return '';
}

/**
 * Dumb grid component — renders the 8×12 plate and delegates clicks upward.
 *
 * Props:
 *   plateType    – "extraction" | "analysis"
 *   onWellClick  – (position, coordinate, status) => void
 *   selectedPositionId – id of the currently-selected position (highlight)
 */
export default function PlateGrid({ plateType, onWellClick, selectedPositionId }) {
  const positions = usePlateStore((s) => s.positions);
  const { isLoading, isError, error } = usePlatePositions();
  const [copyStatus, setCopyStatus] = useState(null); // 'success' | 'error' | null

  const handleCopyToClipboard = useCallback(async () => {
    // Build header row: empty cell + column numbers
    const headerRow = ['', ...COLS].join('\t');

    // Build data rows
    const dataRows = ROWS.map((row) => {
      const cells = COLS.map((col) => {
        const idx = toPositionIndex(row, col);
        const position = positions[idx] ?? null;
        return getCellText(position, plateType);
      });
      return [row, ...cells].join('\t');
    });

    const tsvContent = [headerRow, ...dataRows].join('\n');

    try {
      await navigator.clipboard.writeText(tsvContent);
      setCopyStatus('success');
      setTimeout(() => setCopyStatus(null), 2000);
    } catch {
      setCopyStatus('error');
      setTimeout(() => setCopyStatus(null), 2000);
    }
  }, [positions, plateType]);

  const positionsList = Object.values(positions);
  const counts = positionsList.reduce(
    (acc, p) => {
      if (p.is_reserved) acc.reserved += 1;
      else if (plateType === 'extraction' ? p.sample_raw : p.sample_marker) acc.filled += 1;
      else acc.empty += 1;
      return acc;
    },
    { empty: 0, filled: 0, reserved: 0 },
  );
  counts.empty = 96 - positionsList.length + counts.empty;

  if (isLoading) {
    return <p className="text-gray-500">Loading plate…</p>;
  }

  if (isError) {
    return <p className="text-red-500">Error loading plate: {error?.message ?? 'Unknown error'}</p>;
  }

  return (
    <div>
      {/* Legend */}
      <div className="flex gap-6 mb-4 text-sm flex-wrap items-center">
        <span className="flex items-center gap-1">
          <span className="inline-block w-4 h-4 rounded-lg bg-gray-100 border-2 border-gray-300" />
          Empty ({counts.empty})
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-4 h-4 rounded-lg bg-emerald-400 border-2 border-emerald-600" />
          Filled ({counts.filled})
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-4 h-4 rounded-lg bg-amber-300 border-2 border-amber-500" />
          Reserved ({counts.reserved})
        </span>
        <button
          type="button"
          onClick={handleCopyToClipboard}
          className={classnames(
            'ml-auto px-3 py-1 text-xs rounded border transition-colors print:hidden',
            copyStatus === 'success'
              ? 'bg-green-100 border-green-400 text-green-700'
              : copyStatus === 'error'
                ? 'bg-red-100 border-red-400 text-red-700'
                : 'bg-gray-100 border-gray-300 text-gray-700 hover:bg-gray-200',
          )}
          title="Copy plate layout as tab-separated grid (for Excel)"
        >
          {copyStatus === 'success'
            ? 'Copied!'
            : copyStatus === 'error'
              ? 'Failed'
              : 'Copy for Excel'}
        </button>
      </div>

      {/* Grid - scrollable container */}
      <div className="overflow-x-auto print:overflow-visible">
        <div
          className="inline-grid gap-0.5"
          style={{
            gridTemplateColumns: `2rem repeat(${COLS.length}, 6rem)`,
            gridTemplateRows: `auto repeat(${ROWS.length}, 5rem)`,
          }}
        >
          {/* Top-left empty cell */}
          <div />
          {/* Column headers */}
          {COLS.map((col) => (
            <div
              key={col}
              className="text-center text-xs font-medium text-gray-500 flex items-end justify-center pb-1"
            >
              {col}
            </div>
          ))}

          {/* Rows */}
          {ROWS.map((row) => (
            <>
              {/* Row header */}
              <div
                key={`row-${row}`}
                className="text-xs font-medium text-gray-500 flex items-center justify-center"
              >
                {row}
              </div>
              {/* Wells */}
              {COLS.map((col) => {
                const idx = toPositionIndex(row, col);
                const position = positions[idx] ?? null;
                const coordinate = `${row}${col}`;
                return (
                  <Well
                    key={coordinate}
                    position={position}
                    coordinate={coordinate}
                    plateType={plateType}
                    selected={position?.id === selectedPositionId}
                    onClick={onWellClick}
                  />
                );
              })}
            </>
          ))}
        </div>
      </div>
    </div>
  );
}

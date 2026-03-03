import React from 'react';
import classnames from 'classnames';

const ROWS = 'ABCDEFGH'.split('');
const COLS = Array.from({ length: 12 }, (_, i) => i + 1);

/**
 * Convert row letter + column number to the column-wise position index.
 */
function toPositionIndex(row, col) {
  const rowIdx = ROWS.indexOf(row);
  return (col - 1) * ROWS.length + rowIdx;
}

const STATUS_STYLES = {
  empty: 'bg-gray-100 border-gray-300',
  filled: 'bg-emerald-400 border-emerald-600',
  reserved: 'bg-amber-300 border-amber-500',
};

function getStatus(position, plateType) {
  if (!position) return 'empty';
  if (position.is_reserved) return 'reserved';
  if (plateType === 'extraction' && position.sample_raw) return 'filled';
  if (plateType === 'analysis' && position.sample_marker) return 'filled';
  if (position.sample_raw || position.sample_marker) return 'filled';
  return 'empty';
}

function getFilledLabel(position, plateType) {
  if (plateType === 'extraction' && position?.sample_raw) {
    const mainLabel =
      position.sample_raw.genlab_id ?? position.sample_raw.name ?? 'Sample';
    const orderLabel = position.sample_raw.order_id;
    return { mainLabel, orderLabel };
  }
  if (plateType === 'analysis' && position?.sample_marker) {
    const sampleLabel =
      position.sample_marker.sample_genlab_id ??
      position.sample_marker.sample_name;
    const markerLabel = position.sample_marker.marker_name;
    const orderLabel = position.sample_marker.order_id;
    return { sampleLabel, markerLabel, orderLabel };
  }
  return null;
}

function getTooltip(position, coordinate, status, plateType) {
  let base;
  if (status === 'filled') {
    if (plateType === 'extraction' && position.sample_raw) {
      const id =
        position.sample_raw.genlab_id ?? position.sample_raw.name ?? 'Sample';
      const order = position.sample_raw.order_id;
      base = order ? `${coordinate} — ${id} [#${order}]` : `${coordinate} — ${id}`;
    } else if (plateType === 'analysis' && position.sample_marker) {
      const markerName =
        position.sample_marker.marker_name ?? `#${position.sample_marker.id}`;
      const sampleName =
        position.sample_marker.sample_genlab_id ??
        position.sample_marker.sample_name ??
        '?';
      const order = position.sample_marker.order_id;
      base = order
        ? `${coordinate} — ${markerName} (${sampleName}) [#${order}]`
        : `${coordinate} — ${markerName} (${sampleName})`;
    } else {
      base = `${coordinate} — Filled`;
    }
  } else if (status === 'reserved') {
    base = `${coordinate} — Reserved`;
  } else {
    base = `${coordinate} — Empty`;
  }
  if (position?.notes) base += `\n📝 ${position.notes}`;
  return base;
}

/**
 * Well component for plate preview.
 */
function Well({ position, coordinate, plateType, onClick }) {
  const status = getStatus(position, plateType);
  const filledLabel = getFilledLabel(position, plateType);
  const tooltip = getTooltip(position, coordinate, status, plateType);
  const hasNote = !!position?.notes;
  const isClickable = !!onClick;

  return (
    <div
      title={tooltip}
      onClick={onClick}
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onKeyDown={isClickable ? (e) => e.key === 'Enter' && onClick() : undefined}
      className={classnames(
        'relative w-full h-full rounded-lg border-2 flex flex-col items-center justify-center p-0.5',
        STATUS_STYLES[status],
        isClickable && 'cursor-pointer hover:ring-2 hover:ring-blue-400 hover:ring-offset-1 transition-shadow',
      )}
    >
      {hasNote && (
        <span
          style={{
            position: 'absolute',
            top: '2px',
            right: '2px',
            width: '8px',
            height: '8px',
          }}
          className="rounded-full bg-blue-600 shadow-sm"
        />
      )}
      <span className="text-[10px] font-bold leading-tight text-gray-700">
        {coordinate}
      </span>
      {status === 'filled' && filledLabel && (
        <>
          {filledLabel.mainLabel && (
            <span className="text-[9px] leading-tight truncate max-w-full text-gray-900">
              {filledLabel.mainLabel}
            </span>
          )}
          {filledLabel.sampleLabel && (
            <span className="text-[9px] leading-tight truncate max-w-full text-gray-900">
              {filledLabel.sampleLabel}
            </span>
          )}
          {filledLabel.markerLabel && (
            <span className="text-[9px] leading-tight truncate max-w-full font-semibold text-emerald-900">
              {filledLabel.markerLabel}
            </span>
          )}
          {filledLabel.orderLabel && (
            <span className="text-[8px] leading-tight truncate max-w-full text-gray-600 italic">
              #{filledLabel.orderLabel}
            </span>
          )}
        </>
      )}
      {status === 'reserved' && (
        <span className="text-[8px] text-amber-700 font-medium">Reserved</span>
      )}
    </div>
  );
}

/**
 * Plate grid component.
 * Shows a complete visualization of the plate with filled/empty/reserved positions.
 *
 * Props:
 *   positions  – array of position objects
 *   plateType  – "extraction" | "analysis" (determines filled check)
 *   isLoading  – whether the plate is still loading
 *   onPositionClick – optional callback when a position is clicked (position, coordinate, idx) => void
 */
export default function PlatePreview({
  positions = [],
  plateType = 'analysis',
  isLoading,
  onPositionClick,
}) {
  // Index positions by their position index
  const positionsByIdx = {};
  positions.forEach((p) => {
    positionsByIdx[p.position] = p;
  });

  // Calculate counts
  const counts = positions.reduce(
    (acc, p) => {
      if (p.is_reserved) acc.reserved += 1;
      else if (plateType === 'extraction' ? p.sample_raw : p.sample_marker)
        acc.filled += 1;
      else acc.empty += 1;
      return acc;
    },
    { empty: 0, filled: 0, reserved: 0 },
  );
  counts.empty = 96 - positions.length + counts.empty;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8 text-gray-400">
        Loading plate…
      </div>
    );
  }

  return (
    <div>
      {/* Legend */}
      <div className="flex gap-6 mb-4 text-sm flex-wrap">
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
      </div>

      {/* Grid - scrollable container */}
      <div className="overflow-x-auto">
        <div
          className="inline-grid gap-0.5"
          style={{
            gridTemplateColumns: `2rem repeat(${COLS.length}, 5rem)`,
            gridTemplateRows: `auto repeat(${ROWS.length}, 4rem)`,
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
          <React.Fragment key={`row-${row}`}>
            {/* Row header */}
            <div className="text-xs font-medium text-gray-500 flex items-center justify-center">
              {row}
            </div>
            {/* Wells */}
            {COLS.map((col) => {
              const idx = toPositionIndex(row, col);
              const position = positionsByIdx[idx] ?? null;
              const coordinate = `${row}${col}`;
              return (
                <Well
                  key={coordinate}
                  position={position}
                  coordinate={coordinate}
                  plateType={plateType}
                  onClick={onPositionClick ? () => onPositionClick(position, coordinate, idx) : undefined}
                />
              );
            })}
          </React.Fragment>
        ))}
        </div>
      </div>
    </div>
  );
}

import classnames from 'classnames';

const STATUS_STYLES = {
  empty: 'bg-gray-100 border-gray-300 hover:bg-gray-200',
  filled: 'bg-emerald-400 border-emerald-600 hover:bg-emerald-500',
  reserved: 'bg-amber-300 border-amber-500 hover:bg-amber-400',
};

export function getStatus(position, plateType) {
  if (!position) return 'empty';
  if (position.is_reserved) return 'reserved';
  if (plateType === 'extraction' && position.sample_raw) return 'filled';
  if (plateType === 'analysis' && position.sample_marker) return 'filled';
  // fallback for generic check
  if (position.sample_raw || position.sample_marker) return 'filled';
  return 'empty';
}

function getFilledLabel(position, plateType) {
  if (plateType === 'extraction' && position?.sample_raw) {
    return position.sample_raw.genlab_id ?? position.sample_raw.name ?? 'Sample';
  }
  if (plateType === 'analysis' && position?.sample_marker) {
    const sampleLabel = position.sample_marker.sample_genlab_id ?? position.sample_marker.sample_name;
    const markerLabel = position.sample_marker.marker_name;
    return { sampleLabel, markerLabel };
  }
  return null;
}

function getTooltip(position, coordinate, status, plateType) {
  if (status === 'filled') {
    if (plateType === 'extraction' && position.sample_raw) {
      const id = position.sample_raw.genlab_id ?? position.sample_raw.name ?? 'Sample';
      return `${coordinate} — ${id}`;
    }
    if (plateType === 'analysis' && position.sample_marker) {
      const markerName = position.sample_marker.marker_name ?? `#${position.sample_marker.id}`;
      const sampleName = position.sample_marker.sample_genlab_id ?? position.sample_marker.sample_name ?? '?';
      return `${coordinate} — ${markerName} (${sampleName})`;
    }
  }
  if (status === 'reserved') return `${coordinate} — Reserved`;
  return `${coordinate} — Empty`;
}

export default function Well({ position, coordinate, plateType, selected, onClick }) {
  const status = getStatus(position, plateType);
  const filledLabel = getFilledLabel(position, plateType);
  const tooltip = getTooltip(position, coordinate, status, plateType);

  return (
    <button
      type="button"
      title={tooltip}
      className={classnames(
        'w-full h-full rounded-lg border-2 flex flex-col items-center justify-center transition-colors cursor-pointer select-none p-0.5 overflow-hidden',
        STATUS_STYLES[status],
        selected && 'ring-2 ring-blue-500 ring-offset-1',
      )}
      onClick={() => onClick && onClick(position, coordinate, status)}
    >
      <span className="text-[10px] font-bold leading-tight text-gray-700">{coordinate}</span>
      {status === 'filled' && filledLabel && typeof filledLabel === 'string' && (
        <span className="text-[9px] leading-tight truncate max-w-full text-gray-900">{filledLabel}</span>
      )}
      {status === 'filled' && filledLabel && typeof filledLabel === 'object' && (
        <>
          {filledLabel.sampleLabel && (
            <span className="text-[9px] leading-tight truncate max-w-full text-gray-900">{filledLabel.sampleLabel}</span>
          )}
          {filledLabel.markerLabel && (
            <span className="text-[9px] leading-tight truncate max-w-full font-semibold text-emerald-900">{filledLabel.markerLabel}</span>
          )}
        </>
      )}
      {status === 'reserved' && (
        <span className="text-[9px] leading-tight text-gray-700">Reserved</span>
      )}
    </button>
  );
}

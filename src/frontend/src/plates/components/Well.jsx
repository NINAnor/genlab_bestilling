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
    const mainLabel = position.sample_raw.genlab_id ?? position.sample_raw.name ?? 'Sample';
    const orderLabel = position.sample_raw.order_id;
    return { mainLabel, orderLabel };
  }
  if (plateType === 'analysis' && position?.sample_marker) {
    const sampleLabel = position.sample_marker.sample_genlab_id ?? position.sample_marker.sample_name;
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
      const id = position.sample_raw.genlab_id ?? position.sample_raw.name ?? 'Sample';
      const order = position.sample_raw.order_id;
      base = order ? `${coordinate} — ${id} [#${order}]` : `${coordinate} — ${id}`;
    } else if (plateType === 'analysis' && position.sample_marker) {
      const markerName = position.sample_marker.marker_name ?? `#${position.sample_marker.id}`;
      const sampleName = position.sample_marker.sample_genlab_id ?? position.sample_marker.sample_name ?? '?';
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

export default function Well({ position, coordinate, plateType, selected, onClick }) {
  const status = getStatus(position, plateType);
  const filledLabel = getFilledLabel(position, plateType);
  const tooltip = getTooltip(position, coordinate, status, plateType);

  const hasNote = !!position?.notes;

  return (
    <button
      type="button"
      title={tooltip}
      className={classnames(
        'relative w-full h-full rounded-lg border-2 flex flex-col items-center justify-center transition-colors cursor-pointer select-none p-0.5',
        STATUS_STYLES[status],
        selected && 'ring-2 ring-blue-500 ring-offset-1',
      )}
      onClick={() => onClick && onClick(position, coordinate, status)}
    >
      {hasNote && (
        <span
          style={{ position: 'absolute', top: '2px', right: '2px', width: '8px', height: '8px' }}
          className="rounded-full bg-blue-600 shadow-sm"
        />
      )}
      <span className="text-[10px] font-bold leading-tight text-gray-700">{coordinate}</span>
      {status === 'filled' && filledLabel && (
        <>
          {filledLabel.mainLabel && (
            <span className="text-[9px] leading-tight truncate max-w-full text-gray-900">{filledLabel.mainLabel}</span>
          )}
          {filledLabel.sampleLabel && (
            <span className="text-[9px] leading-tight truncate max-w-full text-gray-900">{filledLabel.sampleLabel}</span>
          )}
          {filledLabel.markerLabel && (
            <span className="text-[9px] leading-tight truncate max-w-full font-semibold text-emerald-900">{filledLabel.markerLabel}</span>
          )}
          {filledLabel.orderLabel && (
            <span className="text-[8px] leading-tight truncate max-w-full text-gray-600 italic">#{filledLabel.orderLabel}</span>
          )}
        </>
      )}
      {status === 'reserved' && (
        <span className="text-[9px] leading-tight text-gray-700">Reserved</span>
      )}
    </button>
  );
}

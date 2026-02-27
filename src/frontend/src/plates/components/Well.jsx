import classnames from 'classnames';

const STATUS_STYLES = {
  empty: 'bg-gray-100 border-gray-300 hover:bg-gray-200',
  filled: 'bg-emerald-400 border-emerald-600 hover:bg-emerald-500',
  reserved: 'bg-amber-300 border-amber-500 hover:bg-amber-400',
};

export function getStatus(position) {
  if (!position) return 'empty';
  if (position.is_reserved) return 'reserved';
  if (position.sample_raw || position.sample_marker) return 'filled';
  return 'empty';
}

function getSampleLabel(position) {
  if (position?.sample_raw) {
    return position.sample_raw.genlab_id ?? position.sample_raw.name ?? '';
  }
  if (position?.sample_marker) {
    return position.sample_marker.sample ?? `M#${position.sample_marker.id}`;
  }
  return null;
}

function getTooltip(position, coordinate, status) {
  if (status === 'filled') {
    if (position.sample_raw) {
      return `${coordinate} — ${position.sample_raw.genlab_id ?? position.sample_raw.name ?? 'Sample'}`;
    }
    if (position.sample_marker) {
      return `${coordinate} — Marker #${position.sample_marker.id}`;
    }
  }
  if (status === 'reserved') return `${coordinate} — Reserved`;
  return `${coordinate} — Empty`;
}

export default function Well({ position, coordinate, onClick }) {
  const status = getStatus(position);
  const sampleLabel = getSampleLabel(position);
  const tooltip = getTooltip(position, coordinate, status);

  return (
    <button
      type="button"
      title={tooltip}
      className={classnames(
        'w-full h-full rounded-lg border-2 flex flex-col items-center justify-center transition-colors cursor-pointer select-none p-0.5 overflow-hidden',
        STATUS_STYLES[status],
      )}
      onClick={() => onClick && onClick(position, coordinate, status)}
    >
      <span className="text-[10px] font-bold leading-tight text-gray-700">{coordinate}</span>
      {status === 'filled' && sampleLabel && (
        <span className="text-[9px] leading-tight truncate max-w-full text-gray-900">{sampleLabel}</span>
      )}
      {status === 'reserved' && (
        <span className="text-[9px] leading-tight text-gray-700">Reserved</span>
      )}
    </button>
  );
}

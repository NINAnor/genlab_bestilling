import PlateGrid from './PlateGrid';
import PositionPanel from './PositionPanel';
import usePlateStore from '../store';

function DetailRow({ label, value, mono }) {
  return (
    <div className="flex items-baseline justify-between gap-2">
      <span className="text-xs text-gray-500 shrink-0">{label}</span>
      <span className={`text-sm text-gray-900 text-right truncate ${
        mono ? 'font-mono' : ''
      }`}>
        {value ?? <span className="text-gray-300">&mdash;</span>}
      </span>
    </div>
  );
}

export default function AnalysisPlate() {
  const plateLabel = usePlateStore((s) => s.plateLabel);
  const selectPosition = usePlateStore((s) => s.selectPosition);
  const selectedPositionId = usePlateStore((s) => {
    const idx = s.selectedPositionIdx;
    return idx != null ? s.positions[idx]?.id ?? null : null;
  });

  const handleWellClick = (position, coordinate) => {
    selectPosition(position, coordinate);
  };

  return (
    <div>
      <h2 className="text-4xl font-bold mb-5">Analysis Plate {plateLabel}</h2>
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 p-4 bg-white rounded">
          <PlateGrid
            plateType="analysis"
            onWellClick={handleWellClick}
            selectedPositionId={selectedPositionId}
          />
        </div>
        <div className="col-span-1 sticky top-4 self-start">
          <PositionPanel plateType="analysis">
            {({ position, status }) => (
              <>
                {status === 'filled' && position.sample_marker && (
                  <div>
                    <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                      Sample Marker
                    </h5>
                    <div className="space-y-2.5">
                      <DetailRow label="Marker" value={position.sample_marker.marker_name} />
                      <DetailRow label="Sample" value={position.sample_marker.sample_genlab_id ?? position.sample_marker.sample_name} mono />
                      <DetailRow label="Species" value={position.sample_marker.sample_species_name} />
                    </div>
                  </div>
                )}
                {status === 'empty' && (
                  <p className="text-sm text-gray-400 italic">No marker assigned</p>
                )}
              </>
            )}
          </PositionPanel>
        </div>
      </div>
    </div>
  );
}

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

export default function ExtractionPlate() {
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
      <h2 className="text-4xl font-bold mb-5">Extraction Plate #{plateLabel}</h2>
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 p-4 bg-white rounded">
          <PlateGrid
            plateType="extraction"
            onWellClick={handleWellClick}
            selectedPositionId={selectedPositionId}
          />
        </div>
        <div className="col-span-1 sticky top-4 self-start">
          <PositionPanel plateType="extraction">
            {({ position, status }) => (
              <>
                {status === 'filled' && position.sample_raw && (
                  <div>
                    <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                      Sample Information
                    </h5>
                    <div className="space-y-2.5">
                      <DetailRow label="Genlab ID" value={position.sample_raw.genlab_id} mono />
                      <DetailRow label="Name" value={position.sample_raw.name} />
                      {position.sample_raw.order_id && (
                        <div className="flex items-baseline justify-between gap-2">
                          <span className="text-xs text-gray-500 shrink-0">Order</span>
                          <a
                            href={`/staff/orders/extraction/${position.sample_raw.order_id}/`}
                            className="text-sm text-blue-600 hover:text-blue-800 hover:underline text-right truncate"
                          >
                            #{position.sample_raw.order_id}
                          </a>
                        </div>
                      )}
                      <DetailRow label="Species" value={position.sample_raw.species_name} />
                      <DetailRow label="Type" value={position.sample_raw.type_name} />
                      <DetailRow label="Year" value={position.sample_raw.year} />
                      {position.sample_raw.pop_id && (
                        <DetailRow label="Pop ID" value={position.sample_raw.pop_id} mono />
                      )}
                      {position.sample_raw.location_name && (
                        <DetailRow label="Location" value={position.sample_raw.location_name} />
                      )}
                    </div>
                  </div>
                )}
                {status === 'empty' && (
                  <p className="text-sm text-gray-400 italic">No sample assigned</p>
                )}
              </>
            )}
          </PositionPanel>
        </div>
      </div>
    </div>
  );
}

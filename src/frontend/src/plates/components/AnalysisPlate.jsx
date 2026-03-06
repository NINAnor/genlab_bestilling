import { useRef } from 'react';
import { useReactToPrint } from 'react-to-print';
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
  const printRef = useRef(null);

  const handlePrint = useReactToPrint({
    contentRef: printRef,
    documentTitle: `Analysis_Plate_${plateLabel}`,
  });

  const handleWellClick = (position, coordinate) => {
    selectPosition(position, coordinate);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-4xl font-bold">Analysis Plate {plateLabel}</h2>
        <button
          type="button"
          onClick={handlePrint}
          className="text-sm bg-gray-100 text-gray-700 px-3 py-1.5 rounded hover:bg-gray-200 print:hidden"
        >
          Print Plate
        </button>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div ref={printRef} className="col-span-2 p-4 bg-white rounded print:col-span-3">
          <div className="hidden print:block print:mb-4">
            <h2 className="text-lg font-bold">Analysis Plate {plateLabel}</h2>
          </div>
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
                      {position.sample_marker.order_id && (
                        <div className="flex items-baseline justify-between gap-2">
                          <span className="text-xs text-gray-500 shrink-0">Order</span>
                          <a
                            href={`/staff/orders/analysis/${position.sample_marker.order_id}/`}
                            className="text-sm text-blue-600 hover:text-blue-800 hover:underline text-right truncate"
                          >
                            #{position.sample_marker.order_id}
                          </a>
                        </div>
                      )}
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

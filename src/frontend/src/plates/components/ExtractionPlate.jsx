import { useRef, useCallback, useState, useEffect } from 'react';
import { useReactToPrint } from 'react-to-print';
import PlateGrid from './PlateGrid';
import PositionPanel from './PositionPanel';
import PlateActionsPanel from './PlateActionsPanel';
import usePlateStore from '../store';

function DetailRow({ label, value, mono }) {
  return (
    <div className="flex items-baseline justify-between gap-2">
      <span className="text-xs text-gray-500 shrink-0">{label}</span>
      <span className={`text-sm text-gray-900 text-right truncate ${mono ? 'font-mono' : ''}`}>
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
    return idx != null ? (s.positions[idx]?.id ?? null) : null;
  });
  const printRef = useRef(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [extractionLabelMode, setExtractionLabelMode] = useState('genlab_id');

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const handlePrint = useReactToPrint({
    contentRef: printRef,
    documentTitle: `Extraction_Plate_${plateLabel}`,
  });

  const handleFullscreen = useCallback(() => {
    if (printRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        printRef.current.requestFullscreen();
      }
    }
  }, []);

  const handleWellClick = (position, coordinate) => {
    selectPosition(position, coordinate);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-4xl font-bold">Extraction Plate #{plateLabel}</h2>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-sm text-gray-700 select-none print:hidden">
            Show label
            <select
              className="rounded border border-gray-300 bg-white px-2 py-1"
              value={extractionLabelMode}
              onChange={(e) => setExtractionLabelMode(e.target.value)}
            >
              <option value="genlab_id">Genlab ID</option>
              <option value="sample_name">Sample name</option>
              <option value="fish_id">Fish ID</option>
            </select>
          </label>
          <button
            type="button"
            onClick={handleFullscreen}
            className="text-sm bg-gray-100 text-gray-700 px-3 py-1.5 rounded hover:bg-gray-200 print:hidden"
          >
            Fullscreen
          </button>
          <button
            type="button"
            onClick={handlePrint}
            className="text-sm bg-gray-100 text-gray-700 px-3 py-1.5 rounded hover:bg-gray-200 print:hidden"
          >
            Print Plate
          </button>
        </div>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div
          ref={printRef}
          className="xl:col-span-2 p-4 bg-white rounded print:col-span-3 min-w-0 fullscreen-plate"
        >
          <style>{`
            .fullscreen-plate:fullscreen {
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              padding: 2rem;
              background: white;
            }
            .fullscreen-plate:fullscreen .fullscreen-title {
              display: block !important;
              margin-bottom: 1.5rem;
            }
          `}</style>
          <h2 className="hidden fullscreen-title text-3xl font-bold print:block print:mb-4 print:text-lg">
            Extraction Plate #{plateLabel}
          </h2>
          <PlateGrid
            plateType="extraction"
            onWellClick={handleWellClick}
            selectedPositionId={selectedPositionId}
            isFullscreen={isFullscreen}
            extractionLabelMode={extractionLabelMode}
          />
        </div>
        <div className="xl:col-span-1 sticky top-4 self-start space-y-4 print:hidden">
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
          <PlateActionsPanel />
        </div>
      </div>
    </div>
  );
}

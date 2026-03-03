import { useState, useEffect } from 'react';
import classnames from 'classnames';
import {
  useAnalysisPlateSearch,
  usePlatePositions,
} from '../hooks/useFilterOptions';
import { useCreatePlate } from '../hooks/useCreatePlate';
import { useMovePosition } from '../hooks/usePositionActions';
import PlatePreview from '../../helpers/PlatePreview';
import PositionModal from './PositionModal';
import useOrderStore from '../store';

/**
 * Component for browsing and previewing analysis plates.
 * Two-column layout: plate list on left, preview on right.
 */
export default function PlateSearch() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPlate, setSelectedPlate] = useState(null);
  const [selectedPosition, setSelectedPosition] = useState(null);
  const setStoreSelectedPlate = useOrderStore((s) => s.setSelectedPlate);

  // Sync selected plate to store
  useEffect(() => {
    setStoreSelectedPlate(selectedPlate);
  }, [selectedPlate, setStoreSelectedPlate]);

  // Fetch plates (empty search returns all)
  const { data: plates = [], isFetching: isLoading } =
    useAnalysisPlateSearch(searchTerm);

  const { data: platePositions = [], isLoading: positionsLoading } =
    usePlatePositions(selectedPlate?.id);

  const createPlate = useCreatePlate();
  const movePosition = useMovePosition();

  // Index positions by their position index for quick lookup
  const positionsByIdx = {};
  platePositions.forEach((p) => {
    positionsByIdx[p.position] = p;
  });

  const handleCreatePlate = () => {
    createPlate.mutate(
      {},
      {
        onSuccess: (newPlate) => {
          setSelectedPlate(newPlate);
        },
      },
    );
  };

  const handlePositionClick = (position, coordinate, positionIndex) => {
    // If position doesn't exist in array, create a placeholder object
    if (!position) {
      // Position doesn't exist in DB yet, but we need the position index and coordinate
      setSelectedPosition({ coordinate, position: positionIndex, id: null });
    } else {
      setSelectedPosition({ ...position, coordinate });
    }
  };

  const handlePositionMove = (fromIdx, toIdx) => {
    const sourcePosition = positionsByIdx[fromIdx];
    if (!sourcePosition?.id) return;

    movePosition.mutate({
      sourcePositionId: sourcePosition.id,
      targetPositionIndex: toIdx,
    });
  };

  const handleCloseModal = () => {
    setSelectedPosition(null);
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="grid grid-cols-1 lg:grid-cols-3 min-h-[500px]">
        {/* Left column: Plate list */}
        <div className="lg:col-span-1 border-b lg:border-b-0 lg:border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-700">
                Analysis Plates
              </h3>
              <button
                type="button"
                onClick={handleCreatePlate}
                disabled={createPlate.isPending}
                className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {createPlate.isPending ? 'Creating…' : '+ New Plate'}
              </button>
            </div>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search plates…"
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="flex-1 overflow-y-auto">
            {isLoading && (
              <div className="p-4 text-sm text-gray-400">Loading plates…</div>
            )}
            {!isLoading && plates.length === 0 && (
              <div className="p-4 text-sm text-gray-400 italic">
                No plates found
              </div>
            )}
            {plates.map((plate, idx) => (
              <button
                key={plate.id ?? `plate-${idx}`}
                type="button"
                onClick={() => setSelectedPlate(plate)}
                className={classnames(
                  'w-full text-left px-4 py-3 border-b border-gray-100 last:border-b-0 transition-colors',
                  selectedPlate?.id === plate.id
                    ? 'bg-blue-50 border-l-4 border-l-blue-500'
                    : 'hover:bg-gray-50',
                )}
              >
                <div className="font-medium text-sm text-gray-900">
                  {plate.label}
                </div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {plate.available_positions} available positions
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Right column: Plate preview */}
        <div className="lg:col-span-2 p-4">
          {!selectedPlate && (
            <div className="h-full flex items-center justify-center text-gray-400 italic">
              Select a plate to preview
            </div>
          )}
          {selectedPlate && (
            <div>
              <h4 className="text-lg font-semibold text-gray-900 mb-4">
                {selectedPlate.label}
              </h4>
              <PlatePreview
                positions={platePositions}
                plateType="analysis"
                isLoading={positionsLoading}
                onPositionClick={handlePositionClick}
                onPositionMove={handlePositionMove}
              />
            </div>
          )}
        </div>
      </div>

      {/* Position management modal */}
      {selectedPosition && (
        <PositionModal position={selectedPosition} onClose={handleCloseModal} />
      )}
    </div>
  );
}

import { useState, useEffect, useRef } from 'react';
import classnames from 'classnames';
import {
  useAnalysisPlateSearch,
  usePlatePositions,
} from '../hooks/useFilterOptions';
import {
  useCreatePlate,
  useSetAnalysisDate,
  useUploadResultFile,
  useDeleteResultFile,
} from '../hooks/useCreatePlate';
import { useMovePosition } from '../hooks/usePositionActions';
import PlatePreview from '../../helpers/PlatePreview';
import PositionModal from './PositionModal';
import useOrderStore from '../store';

/**
 * Get today's date in YYYY-MM-DD format for datetime-local input.
 */
function getTodayDatetime() {
  const now = new Date();
  // Format as YYYY-MM-DDTHH:mm
  return now.toISOString().slice(0, 16);
}

/**
 * Component for browsing and previewing analysis plates.
 * Two-column layout: plate list on left, preview on right.
 */
export default function PlateSearch() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [minPositions, setMinPositions] = useState('');
  const [selectedPlate, setSelectedPlate] = useState(null);
  const [selectedPosition, setSelectedPosition] = useState(null);
  const [analysisDate, setAnalysisDate] = useState('');
  const setStoreSelectedPlate = useOrderStore((s) => s.setSelectedPlate);
  const fileInputRef = useRef(null);

  // Sync selected plate to store and update analysis date field
  useEffect(() => {
    setStoreSelectedPlate(selectedPlate);
    if (selectedPlate?.analysis_date) {
      // Format the date for datetime-local input
      setAnalysisDate(selectedPlate.analysis_date.slice(0, 16));
    } else if (selectedPlate) {
      // Default to today when selecting a plate without analysis_date
      setAnalysisDate(getTodayDatetime());
    } else {
      setAnalysisDate('');
    }
  }, [selectedPlate, setStoreSelectedPlate]);

  // Fetch plates (empty search returns all)
  const filters = {
    status: statusFilter || undefined,
    minAvailablePositions: minPositions || undefined,
  };
  const { data: plates = [], isFetching: isLoading } =
    useAnalysisPlateSearch(searchTerm, filters);

  const { data: platePositions = [], isLoading: positionsLoading } =
    usePlatePositions(selectedPlate?.id);

  const createPlate = useCreatePlate();
  const setAnalysisDateMutation = useSetAnalysisDate();
  const uploadResultFile = useUploadResultFile();
  const deleteResultFile = useDeleteResultFile();
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

  const handleSaveAnalysisDate = () => {
    if (!selectedPlate?.id || !analysisDate) return;
    setAnalysisDateMutation.mutate(
      {
        plateId: selectedPlate.id,
        analysisDate,
      },
      {
        onSuccess: (data) => {
          // Update selectedPlate with new analysis_date
          setSelectedPlate((prev) => ({
            ...prev,
            analysis_date: data.analysis_date,
            has_results: prev.has_results,
          }));
        },
      },
    );
  };

  const handleClearAnalysisDate = () => {
    if (!selectedPlate?.id) return;
    setAnalysisDateMutation.mutate(
      {
        plateId: selectedPlate.id,
        analysisDate: null,
      },
      {
        onSuccess: () => {
          setSelectedPlate((prev) => ({
            ...prev,
            analysis_date: null,
          }));
          setAnalysisDate('');
        },
      },
    );
  };

  const handleFileUpload = (event) => {
    const file = event.target.files?.[0];
    if (!file || !selectedPlate?.id) return;

    uploadResultFile.mutate(
      {
        plateId: selectedPlate.id,
        file,
      },
      {
        onSuccess: (data) => {
          setSelectedPlate((prev) => ({
            ...prev,
            has_results: true,
            result_file: data.result_file,
          }));
          // Clear file input
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
        },
      },
    );
  };

  const handleDeleteResultFile = () => {
    if (!selectedPlate?.id) return;

    if (!window.confirm('Are you sure you want to delete this result file?')) {
      return;
    }

    deleteResultFile.mutate(
      {
        plateId: selectedPlate.id,
      },
      {
        onSuccess: () => {
          setSelectedPlate((prev) => ({
            ...prev,
            has_results: false,
            result_file: null,
          }));
        },
      },
    );
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
            <div className="mt-2 flex gap-2">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="flex-1 border border-gray-300 rounded px-2 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All statuses</option>
                <option value="pending">Pending</option>
                <option value="analyzing">Analyzing</option>
                <option value="results">Results</option>
              </select>
              <input
                type="number"
                min="0"
                value={minPositions}
                onChange={(e) => setMinPositions(e.target.value)}
                placeholder="Min pos."
                title="Minimum available positions"
                className="w-20 border border-gray-300 rounded px-2 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
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
                <div className="flex items-center justify-between">
                  <span className="font-medium text-sm text-gray-900">
                    {plate.label}
                  </span>
                  {plate.has_results ? (
                    <span className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                      Results
                    </span>
                  ) : plate.analysis_date ? (
                    <span className="text-xs bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded">
                      Analyzing
                    </span>
                  ) : (
                    <span className="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded">
                      Pending
                    </span>
                  )}
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
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <h4 className="text-lg font-semibold text-gray-900">
                    {selectedPlate.label}
                  </h4>
                  {selectedPlate.has_results ? (
                    <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                      Results
                    </span>
                  ) : selectedPlate.analysis_date ? (
                    <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded">
                      Analyzing
                    </span>
                  ) : (
                    <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded">
                      Pending
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <label className="text-sm text-gray-600">Analysis Date:</label>
                  <input
                    type="datetime-local"
                    value={analysisDate}
                    onChange={(e) => setAnalysisDate(e.target.value)}
                    className="border border-gray-300 rounded px-2 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <button
                    type="button"
                    onClick={handleSaveAnalysisDate}
                    disabled={setAnalysisDateMutation.isPending || !analysisDate}
                    className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    {setAnalysisDateMutation.isPending ? 'Saving…' : 'Save'}
                  </button>
                  {selectedPlate.analysis_date && (
                    <button
                      type="button"
                      onClick={handleClearAnalysisDate}
                      disabled={setAnalysisDateMutation.isPending}
                      className="text-xs bg-gray-200 text-gray-700 px-3 py-1.5 rounded hover:bg-gray-300 disabled:opacity-50"
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>
              {/* Result file upload - only show if plate has been analyzed */}
              {(selectedPlate.has_results || selectedPlate.analysis_date) && (
                <div className="flex items-center gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-600">Result File:</span>
                  {selectedPlate.has_results ? (
                    <>
                      <a
                        href={selectedPlate.result_file}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:underline"
                      >
                        View File
                      </a>
                      <button
                        type="button"
                        onClick={handleDeleteResultFile}
                        disabled={deleteResultFile.isPending}
                        className="text-xs bg-red-100 text-red-700 px-3 py-1.5 rounded hover:bg-red-200 disabled:opacity-50"
                      >
                        {deleteResultFile.isPending ? 'Deleting…' : 'Delete'}
                      </button>
                    </>
                  ) : (
                    <>
                      <input
                        ref={fileInputRef}
                        type="file"
                        onChange={handleFileUpload}
                        disabled={uploadResultFile.isPending}
                        className="text-sm text-gray-600 file:mr-2 file:py-1.5 file:px-3 file:border-0 file:text-xs file:font-medium file:bg-blue-100 file:text-blue-700 file:rounded file:cursor-pointer hover:file:bg-blue-200"
                      />
                      {uploadResultFile.isPending && (
                        <span className="text-xs text-gray-500">Uploading…</span>
                      )}
                    </>
                  )}
                </div>
              )}
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

import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import {
  useAnalysisTypes,
  useMarkersForAnalysisType,
} from '../hooks/useFilterOptions';
import { useCreatePlate } from '../hooks/useCreatePlate';

/**
 * Modal for creating a new analysis plate.
 * Requires analysis type selection, optional markers and name.
 */
export default function CreatePlateModal({ isOpen, onClose, onSuccess }) {
  const [analysisTypeId, setAnalysisTypeId] = useState('');
  const [selectedMarkers, setSelectedMarkers] = useState([]);
  const [plateName, setPlateName] = useState('');

  const { data: analysisTypes = [], isLoading: typesLoading } =
    useAnalysisTypes();
  const { data: markers = [], isLoading: markersLoading } =
    useMarkersForAnalysisType(analysisTypeId || null);
  const createPlate = useCreatePlate();

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setAnalysisTypeId('');
      setSelectedMarkers([]);
      setPlateName('');
    }
  }, [isOpen]);

  // Clear selected markers when analysis type changes
  useEffect(() => {
    setSelectedMarkers([]);
  }, [analysisTypeId]);

  if (!isOpen) return null;

  const handleMarkerToggle = (markerName) => {
    setSelectedMarkers((prev) =>
      prev.includes(markerName)
        ? prev.filter((m) => m !== markerName)
        : [...prev, markerName],
    );
  };

  const handleSelectAllMarkers = () => {
    setSelectedMarkers(markers.map((m) => m.name));
  };

  const handleDeselectAllMarkers = () => {
    setSelectedMarkers([]);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!analysisTypeId) return;

    createPlate.mutate(
      {
        name: plateName.trim() || undefined,
        analysis_type: parseInt(analysisTypeId, 10),
        markers: selectedMarkers,
      },
      {
        onSuccess: (newPlate) => {
          onSuccess?.(newPlate);
          onClose();
        },
      },
    );
  };

  const isPending = createPlate.isPending;
  const canSubmit = !!analysisTypeId && !isPending;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            Create New Plate
          </h3>
          <button
            type="button"
            onClick={onClose}
            disabled={isPending}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-4 py-4 space-y-4">
          {/* Plate Name (optional) */}
          <div>
            <label
              htmlFor="plate-name"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Plate Name{' '}
              <span className="font-normal text-gray-500">(optional)</span>
            </label>
            <input
              type="text"
              id="plate-name"
              value={plateName}
              onChange={(e) => setPlateName(e.target.value)}
              disabled={isPending}
              placeholder="Human readable label…"
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
            />
          </div>

          {/* Analysis Type (required) */}
          <div>
            <label
              htmlFor="analysis-type"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Analysis Type <span className="text-red-500">*</span>
            </label>
            <select
              id="analysis-type"
              value={analysisTypeId}
              onChange={(e) => setAnalysisTypeId(e.target.value)}
              disabled={typesLoading || isPending}
              required
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
            >
              <option value="">Select analysis type…</option>
              {analysisTypes.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.name}
                </option>
              ))}
            </select>
          </div>

          {/* Allowed Markers (optional, shown after analysis type is selected) */}
          {analysisTypeId && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-sm font-medium text-gray-700">
                  Allowed Markers{' '}
                  <span className="font-normal text-gray-500">(optional)</span>
                </label>
                {markers.length > 0 && (
                  <div className="flex gap-2 text-xs">
                    <button
                      type="button"
                      onClick={handleSelectAllMarkers}
                      className="text-blue-600 hover:underline"
                    >
                      Select all
                    </button>
                    <span className="text-gray-300">|</span>
                    <button
                      type="button"
                      onClick={handleDeselectAllMarkers}
                      className="text-blue-600 hover:underline"
                    >
                      Clear
                    </button>
                  </div>
                )}
              </div>
              <p className="text-xs text-gray-500 mb-2">
                Leave empty to allow all markers for this analysis type.
              </p>
              {markersLoading ? (
                <div className="text-sm text-gray-500">Loading markers…</div>
              ) : markers.length === 0 ? (
                <div className="text-sm text-gray-500 italic">
                  No markers available for this analysis type.
                </div>
              ) : (
                <div className="max-h-40 overflow-y-auto border border-gray-200 rounded p-2 space-y-1">
                  {markers.map((marker) => (
                    <label
                      key={marker.name}
                      className="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-50 px-1 py-0.5 rounded"
                    >
                      <input
                        type="checkbox"
                        checked={selectedMarkers.includes(marker.name)}
                        onChange={() => handleMarkerToggle(marker.name)}
                        disabled={isPending}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span>{marker.name}</span>
                    </label>
                  ))}
                </div>
              )}
              {selectedMarkers.length > 0 && (
                <div className="text-xs text-gray-500 mt-1">
                  {selectedMarkers.length} marker
                  {selectedMarkers.length !== 1 ? 's' : ''} selected
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isPending}
              className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!canSubmit}
              className="px-4 py-2 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {isPending ? 'Creating…' : 'Create Plate'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

CreatePlateModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onSuccess: PropTypes.func,
};

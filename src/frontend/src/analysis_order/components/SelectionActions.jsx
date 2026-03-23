import { useState } from 'react';
import useOrderStore from '../store';
import { useAddToPlate } from '../hooks/useAddToPlate';

/**
 * Action bar that appears when sample markers are selected.
 * Allows adding selected markers to the currently selected plate.
 */
export default function SelectionActions() {
  const selectedMarkerIds = useOrderStore((s) => s.selectedMarkerIds);
  const sampleMarkers = useOrderStore((s) => s.sampleMarkers);
  const clearSelection = useOrderStore((s) => s.clearSelection);
  const selectedPlate = useOrderStore((s) => s.selectedPlate);

  const [replicates, setReplicates] = useState(1);
  const addToPlate = useAddToPlate();

  const selectedIds = Object.keys(selectedMarkerIds).filter((id) => selectedMarkerIds[id]);
  const selectedCount = selectedIds.length;

  if (selectedCount === 0) {
    return null;
  }

  // Get the IDs in table order (by sample genlab_id, then marker name)
  const orderedIds = Object.values(sampleMarkers)
    .filter((m) => selectedMarkerIds[String(m.id)])
    .sort((a, b) => {
      const aKey = `${a.sample_genlab_id ?? a.sample_name ?? ''}-${a.marker_name ?? ''}`;
      const bKey = `${b.sample_genlab_id ?? b.sample_name ?? ''}-${b.marker_name ?? ''}`;
      return aKey.localeCompare(bKey);
    })
    .map((m) => m.id);

  const handleAddToPlate = () => {
    if (!selectedPlate) {
      return;
    }
    addToPlate.mutate({
      plateId: selectedPlate.id,
      sampleMarkerIds: orderedIds,
      replicates,
    });
  };

  const totalToAdd = selectedCount * replicates;

  // When using replicates > 1, max 8 sample markers can be selected
  const maxSamplesForReplicates = 8;
  const exceedsReplicateLimit = replicates > 1 && selectedCount > maxSamplesForReplicates;

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-center justify-between gap-4 mt-3">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-blue-800">
          {selectedCount} sample marker{selectedCount === 1 ? '' : 's'} selected
        </span>
        <button
          type="button"
          onClick={clearSelection}
          className="text-xs text-blue-600 hover:text-blue-800 underline"
        >
          Clear selection
        </button>
      </div>

      <div className="flex items-center gap-3">
        {selectedPlate ? (
          <>
            <span className="text-sm text-gray-600">
              Add to <strong>{selectedPlate.label}</strong>
            </span>
            <label className="flex items-center gap-1 text-sm text-gray-600">
              <span>×</span>
              <input
                type="number"
                min="1"
                max="10"
                value={replicates}
                onChange={(e) => setReplicates(Math.max(1, Math.min(10, parseInt(e.target.value, 10) || 1)))}
                className="w-12 px-1 py-0.5 border border-gray-300 rounded text-center text-sm"
              />
              <span className="text-gray-500">replicates</span>
            </label>
            {exceedsReplicateLimit && (
              <span className="text-xs text-red-600">
                Max {maxSamplesForReplicates} samples with replicates
              </span>
            )}
            <button
              type="button"
              onClick={handleAddToPlate}
              disabled={addToPlate.isPending || exceedsReplicateLimit}
              className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {addToPlate.isPending ? 'Adding…' : `Add ${totalToAdd} to plate`}
            </button>
          </>
        ) : (
          <span className="text-sm text-gray-500 italic">
            Select a plate above to add markers
          </span>
        )}
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import {
  useReservePosition,
  useUnreservePosition,
  useRemoveSampleMarker,
  useEditPositionNotes,
} from '../hooks/usePositionActions';

/**
 * Modal for managing a plate position.
 * Allows reserve/unreserve, remove sample marker, edit notes.
 */
export default function PositionModal({ position, onClose }) {
  const [notes, setNotes] = useState(position?.notes ?? '');
  const [showNotesForm, setShowNotesForm] = useState(false);

  const reserve = useReservePosition();
  const unreserve = useUnreservePosition();
  const removeSampleMarker = useRemoveSampleMarker();
  const editNotes = useEditPositionNotes();

  useEffect(() => {
    setNotes(position?.notes ?? '');
    setShowNotesForm(false);
  }, [position]);

  if (!position) return null;

  const hasId = position.id != null;
  const status = position.is_reserved
    ? 'reserved'
    : position.sample_marker
      ? 'filled'
      : 'empty';

  const handleReserve = () => {
    if (!hasId) return;
    reserve.mutate(position.id, {
      onSuccess: onClose,
    });
  };

  const handleUnreserve = () => {
    if (!hasId) return;
    unreserve.mutate(position.id, {
      onSuccess: onClose,
    });
  };

  const handleRemoveSampleMarker = () => {
    if (!hasId) return;
    if (
      window.confirm(
        'Are you sure you want to remove the sample marker from this position?',
      )
    ) {
      removeSampleMarker.mutate(position.id, {
        onSuccess: onClose,
      });
    }
  };

  const handleSaveNotes = () => {
    if (!hasId) return;
    editNotes.mutate(
      { positionId: position.id, notes },
      {
        onSuccess: () => {
          setShowNotesForm(false);
        },
      },
    );
  };

  const isPending =
    reserve.isPending ||
    unreserve.isPending ||
    removeSampleMarker.isPending ||
    editNotes.isPending;

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
            Position {position.coordinate}
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="px-4 py-3 space-y-4">
          {/* Status badge */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Status:</span>
            {status === 'empty' && (
              <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded">
                Empty
              </span>
            )}
            {status === 'reserved' && (
              <span className="px-2 py-0.5 text-xs font-medium bg-amber-100 text-amber-700 rounded">
                Reserved
              </span>
            )}
            {status === 'filled' && (
              <span className="px-2 py-0.5 text-xs font-medium bg-emerald-100 text-emerald-700 rounded">
                Filled
              </span>
            )}
          </div>

          {/* Sample marker info */}
          {position.sample_marker && (
            <div className="bg-gray-50 rounded-lg p-3 space-y-1">
              <div className="text-sm font-medium text-gray-900">Sample Marker</div>
              <div className="text-sm text-gray-600">
                <span className="font-medium">Sample:</span>{' '}
                {position.sample_marker.sample_genlab_id ??
                  position.sample_marker.sample_name ??
                  '—'}
              </div>
              <div className="text-sm text-gray-600">
                <span className="font-medium">Marker:</span>{' '}
                {position.sample_marker.marker_name ?? '—'}
              </div>
              {position.sample_marker.order_id && (
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Order:</span> #{position.sample_marker.order_id}
                </div>
              )}
            </div>
          )}

          {/* Notes */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-gray-700">Notes</span>
              {hasId && !showNotesForm && (
                <button
                  type="button"
                  onClick={() => setShowNotesForm(true)}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  {position.notes ? 'Edit' : 'Add'}
                </button>
              )}
            </div>
            {showNotesForm ? (
              <div className="space-y-2">
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                  rows={2}
                  placeholder="Add notes…"
                />
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleSaveNotes}
                    disabled={editNotes.isPending || !hasId}
                    className="px-3 py-1 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    {editNotes.isPending ? 'Saving…' : 'Save'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setNotes(position.notes ?? '');
                      setShowNotesForm(false);
                    }}
                    className="px-3 py-1 text-xs font-medium text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-600">
                {position.notes || <span className="italic text-gray-400">No notes</span>}
              </p>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="px-4 py-3 border-t border-gray-200 flex flex-wrap gap-2">
          {!hasId && (
            <span className="text-sm text-gray-500 italic">
              Position not in database yet
            </span>
          )}

          {hasId && status === 'empty' && (
            <button
              type="button"
              onClick={handleReserve}
              disabled={isPending}
              className="px-3 py-1.5 text-sm font-medium text-amber-700 bg-amber-100 rounded hover:bg-amber-200 disabled:opacity-50"
            >
              {reserve.isPending ? 'Reserving…' : 'Reserve Position'}
            </button>
          )}

          {hasId && status === 'reserved' && (
            <button
              type="button"
              onClick={handleUnreserve}
              disabled={isPending}
              className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
            >
              {unreserve.isPending ? 'Unreserving…' : 'Remove Reservation'}
            </button>
          )}

          {hasId && status === 'filled' && (
            <button
              type="button"
              onClick={handleRemoveSampleMarker}
              disabled={isPending}
              className="px-3 py-1.5 text-sm font-medium text-red-700 bg-red-100 rounded hover:bg-red-200 disabled:opacity-50"
            >
              {removeSampleMarker.isPending ? 'Removing…' : 'Remove Sample Marker'}
            </button>
          )}
        </div>

        {/* Error messages */}
        {(reserve.error || unreserve.error || removeSampleMarker.error || editNotes.error) && (
          <div className="px-4 py-2 bg-red-50 border-t border-red-200 text-sm text-red-700">
            {reserve.error?.message ||
              unreserve.error?.message ||
              removeSampleMarker.error?.message ||
              editNotes.error?.message}
          </div>
        )}
      </div>
    </div>
  );
}

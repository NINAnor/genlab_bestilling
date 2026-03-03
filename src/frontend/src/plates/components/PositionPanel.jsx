import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import toast from 'react-hot-toast';
import usePlateStore from '../store';
import { usePositionAction } from '../hooks/usePositionAction';
import { usePositiveControls, useSetPositiveControl } from '../hooks/usePositiveControls';
import { getStatus } from './Well';
import SearchPanel from './SearchPanel';

/* ── tiny inline SVG icons ───────────────────────────────────── */

const IconCursor = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-10 h-10 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M15.042 21.672 13.684 16.6m0 0-2.51 2.225.569-9.47 5.227 7.917-3.286-.672ZM12 2.25V4.5m5.834.166-1.591 1.591M20.25 10.5H18M7.757 14.743l-1.59 1.59M6 10.5H3.75m4.007-4.243-1.59-1.59" />
  </svg>
);

const IconClose = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
  </svg>
);

const IconLock = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 inline-block mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
  </svg>
);

const IconUnlock = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 inline-block mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10.5V6.75a4.5 4.5 0 1 1 9 0v3.75M3.75 21.75h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H3.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
  </svg>
);

const IconTrash = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 inline-block mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
  </svg>
);

/* ── status config ───────────────────────────────────────────── */

const STATUS_CONFIG = {
  filled: {
    label: 'Filled',
    dot: 'bg-emerald-500',
    badge: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-600/20',
    accent: 'border-l-emerald-500',
  },
  reserved: {
    label: 'Reserved',
    dot: 'bg-amber-500',
    badge: 'bg-amber-50 text-amber-700 ring-1 ring-amber-600/20',
    accent: 'border-l-amber-500',
  },
  empty: {
    label: 'Empty',
    dot: 'bg-gray-400',
    badge: 'bg-gray-50 text-gray-600 ring-1 ring-gray-500/20',
    accent: 'border-l-gray-400',
  },
};

/* ── component ───────────────────────────────────────────────── */

/**
 * Side panel showing details & actions for the selected plate position.
 *
 * Props:
 *   plateType – "extraction" | "analysis"
 *   children  – render-prop receiving { position, coordinate, status }
 */

export default function PositionPanel({ plateType, children }) {
  const positions = usePlateStore((s) => s.positions);
  const selectedPositionIdx = usePlateStore((s) => s.selectedPositionIdx);
  const selectedCoordinate = usePlateStore((s) => s.selectedCoordinate);
  const clearSelection = usePlateStore((s) => s.clearSelection);
  const actionMutation = usePositionAction();
  const [confirmAction, setConfirmAction] = useState(null);
  const [editingNotes, setEditingNotes] = useState(false);
  const [noteDraft, setNoteDraft] = useState('');
  const [selectedPositiveControl, setSelectedPositiveControl] = useState(null);
  const { data: positiveControls = [] } = usePositiveControls();
  const setPositiveControlMutation = useSetPositiveControl();

  const position = selectedPositionIdx != null ? positions[selectedPositionIdx] : null;

  // Reset confirmation and notes editor when selection changes
  useEffect(() => {
    setConfirmAction(null);
    setEditingNotes(false);
    setSelectedPositiveControl(position?.positive_control ?? null);
  }, [selectedPositionIdx, position?.positive_control]);

  const status = getStatus(position, plateType);
  const cfg = STATUS_CONFIG[status];

  /* ── empty state ──────────────────────────────────────────── */
  if (!position) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 bg-gray-50/60">
          <h4 className="text-sm font-semibold text-gray-900 tracking-wide uppercase">
            Position Details
          </h4>
        </div>
        <div className="flex flex-col items-center justify-center py-14 px-6 text-center gap-3">
          <IconCursor />
          <p className="text-sm text-gray-400 leading-relaxed">
            Select a well on the plate to view its details and available actions.
          </p>
        </div>
      </div>
    );
  }

  /* ── actions ──────────────────────────────────────────────── */
  const handleAction = (action, successMsg) => {
    actionMutation.mutate(
      { positionId: position.id, action },
      {
        onSuccess: () => toast.success(successMsg),
        onError: (err) => toast.error(err.response?.data?.error ?? `Failed to ${action}`),
      },
    );
  };

  /* ── selected state ───────────────────────────────────────── */
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Header with coordinate + status */}
      <div className={`border-l-4 ${cfg.accent} px-5 py-4 bg-gray-50/60 flex items-center justify-between`}>
        <div className="flex items-center gap-3">
          <span className="text-2xl font-bold text-gray-900 tracking-tight">
            {selectedCoordinate}
          </span>
          <div className="flex flex-col gap-1">
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.badge}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
              {cfg.label}
            </span>
            {status === 'reserved' && position.positive_control_name && (
              <span className="text-xs text-gray-600 pl-1">{position.positive_control_name}</span>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={clearSelection}
          className="p-1 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-200/60 transition-colors"
          title="Close panel"
        >
          <IconClose />
        </button>
      </div>

      <div className="divide-y divide-gray-100">
        {/* Meta info */}
        {position.filled_at && (
          <div className="px-5 py-3">
            <div className="flex items-center text-xs text-gray-500 gap-1.5">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
              Filled {position.filled_at}
            </div>
          </div>
        )}

        {/* Notes section — always visible */}
        <div className="px-5 py-3 space-y-2">
          <div className="flex items-center justify-between">
            <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
              </svg>
              Notes
            </h5>
            {!editingNotes && (
              <button
                type="button"
                onClick={() => { setNoteDraft(position.notes ?? ''); setEditingNotes(true); }}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium transition-colors"
              >
                {position.notes ? 'Edit' : 'Add note'}
              </button>
            )}
          </div>

          {editingNotes ? (
            <div className="space-y-2">
              <textarea
                value={noteDraft}
                onChange={(e) => setNoteDraft(e.target.value)}
                rows={3}
                className="block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm
                           placeholder:text-gray-400
                           focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none
                           transition-colors resize-none"
                placeholder="Add a note for this position…"
                autoFocus
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    actionMutation.mutate(
                      { positionId: position.id, action: 'edit_notes', payload: { notes: noteDraft } },
                      {
                        onSuccess: () => { toast.success('Note saved'); setEditingNotes(false); },
                        onError: (err) => toast.error(err.response?.data?.error ?? 'Failed to save note'),
                      },
                    );
                  }}
                  disabled={actionMutation.isPending}
                  className="flex-1 px-3 py-1.5 rounded-md text-sm font-medium
                             bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800
                             transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={() => setEditingNotes(false)}
                  className="flex-1 px-3 py-1.5 rounded-md text-sm font-medium
                             bg-white text-gray-700 ring-1 ring-inset ring-gray-300
                             hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : position.notes ? (
            <div className="bg-blue-50/60 rounded-lg px-3 py-2">
              <p className="text-xs text-blue-800 leading-relaxed whitespace-pre-wrap">{position.notes}</p>
            </div>
          ) : (
            <p className="text-xs text-gray-400 italic">No notes</p>
          )}
        </div>

        {/* Type-specific content */}
        {children && (
          <div className="px-5 py-4">
            {children({ position, coordinate: selectedCoordinate, status })}
          </div>
        )}

        {/* Actions */}
        <div className="px-5 py-4 space-y-2">
          <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Actions
          </h5>

          {/* Confirmation dialog */}
          {confirmAction && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3 mb-2">
              <p className="text-sm text-red-800 mb-3">{confirmAction.message}</p>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    handleAction(confirmAction.action, confirmAction.successMsg);
                    setConfirmAction(null);
                  }}
                  disabled={actionMutation.isPending}
                  className="flex-1 px-3 py-1.5 rounded-md text-sm font-medium
                             bg-red-600 text-white hover:bg-red-700 active:bg-red-800
                             transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Confirm
                </button>
                <button
                  onClick={() => setConfirmAction(null)}
                  className="flex-1 px-3 py-1.5 rounded-md text-sm font-medium
                             bg-white text-gray-700 ring-1 ring-inset ring-gray-300
                             hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {status === 'empty' && !confirmAction && (
            <>
              <SearchPanel
                positionId={position.id}
                plateType={plateType}
                coordinate={selectedCoordinate}
              />
              <button
                onClick={() => handleAction('reserve', `${selectedCoordinate} reserved`)}
                disabled={actionMutation.isPending}
                className="w-full inline-flex items-center justify-center px-4 py-2.5 rounded-lg text-sm font-medium
                           bg-amber-500 text-white shadow-sm
                           hover:bg-amber-600 active:bg-amber-700
                           transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <IconLock />
                Reserve Position
              </button>
            </>
          )}

          {status === 'reserved' && !confirmAction && (
            <>
              {/* Positive control selector */}
              {positiveControls.length > 0 && (
                <div className="mb-3">
                  <label
                    htmlFor="positive-control-select"
                    className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2"
                  >
                    Positive Control
                  </label>
                  <select
                    id="positive-control-select"
                    value={selectedPositiveControl ?? ''}
                    onChange={(e) => {
                      const newValue = e.target.value ? parseInt(e.target.value, 10) : null;
                      setSelectedPositiveControl(newValue);
                      setPositiveControlMutation.mutate(
                        { positionId: position.id, positiveControlId: newValue },
                        {
                          onSuccess: () => toast.success('Positive control updated'),
                          onError: (err) => toast.error(err.response?.data?.error ?? 'Failed to update positive control'),
                        },
                      );
                    }}
                    disabled={setPositiveControlMutation.isPending}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg
                               focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:outline-none
                               disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <option value="">None</option>
                    {positiveControls.map((pc) => (
                      <option key={pc.id} value={pc.id}>
                        {pc.name}
                      </option>
                    ))}
                  </select>
                  {setPositiveControlMutation.isPending && (
                    <span className="text-xs text-gray-500 mt-1">Saving…</span>
                  )}
                </div>
              )}
              <button
                onClick={() => handleAction('unreserve', `${selectedCoordinate} unreserved`)}
                disabled={actionMutation.isPending}
                className="w-full inline-flex items-center justify-center px-4 py-2.5 rounded-lg text-sm font-medium
                           bg-white text-gray-700 shadow-sm ring-1 ring-inset ring-gray-300
                           hover:bg-gray-50 active:bg-gray-100
                           transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <IconUnlock />
                Remove Reservation
              </button>
            </>
          )}

          {status === 'filled' && position.sample_raw && !confirmAction && (
            <button
              onClick={() =>
                setConfirmAction({
                  action: 'remove_sample',
                  message: `Remove the sample from position ${selectedCoordinate}? This will free the position but won't delete the sample.`,
                  successMsg: `Sample removed from ${selectedCoordinate}`,
                })
              }
              disabled={actionMutation.isPending}
              className="w-full inline-flex items-center justify-center px-4 py-2.5 rounded-lg text-sm font-medium
                         bg-white text-red-700 shadow-sm ring-1 ring-inset ring-red-300
                         hover:bg-red-50 active:bg-red-100
                         transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <IconTrash />
              Remove Sample
            </button>
          )}

          {status === 'filled' && position.sample_marker && !confirmAction && (
            <button
              onClick={() =>
                setConfirmAction({
                  action: 'remove_analysis',
                  message: `Remove the sample marker from position ${selectedCoordinate}? This will free the position but won't delete the marker analysis.`,
                  successMsg: `Sample marker removed from ${selectedCoordinate}`,
                })
              }
              disabled={actionMutation.isPending}
              className="w-full inline-flex items-center justify-center px-4 py-2.5 rounded-lg text-sm font-medium
                         bg-white text-red-700 shadow-sm ring-1 ring-inset ring-red-300
                         hover:bg-red-50 active:bg-red-100
                         transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <IconTrash />
              Remove Sample Marker
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

PositionPanel.propTypes = {
  plateType: PropTypes.oneOf(['extraction', 'analysis']).isRequired,
  children: PropTypes.func,
};

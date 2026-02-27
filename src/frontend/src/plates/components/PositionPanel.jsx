import toast from 'react-hot-toast';
import usePlateStore from '../store';
import { usePositionAction } from '../hooks/usePositionAction';
import { getStatus } from './Well';

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

  const position = selectedPositionIdx != null ? positions[selectedPositionIdx] : null;
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
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.badge}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
            {cfg.label}
          </span>
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
        {(position.filled_at || position.notes) && (
          <div className="px-5 py-3 space-y-2">
            {position.filled_at && (
              <div className="flex items-center text-xs text-gray-500 gap-1.5">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                </svg>
                Filled {position.filled_at}
              </div>
            )}
            {position.notes && (
              <div className="bg-blue-50/60 rounded-lg px-3 py-2">
                <p className="text-xs text-blue-800 leading-relaxed">{position.notes}</p>
              </div>
            )}
          </div>
        )}

        {/* Type-specific content */}
        {children && (
          <div className="px-5 py-4">
            {children({ position, coordinate: selectedCoordinate, status })}
          </div>
        )}

        {/* Actions */}
        {(status === 'empty' || status === 'reserved') && (
          <div className="px-5 py-4 space-y-2">
            <h5 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Actions
            </h5>

            {status === 'empty' && (
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
            )}

            {status === 'reserved' && (
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
            )}
          </div>
        )}
      </div>
    </div>
  );
}

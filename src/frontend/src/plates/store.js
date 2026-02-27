import { create } from 'zustand';

/**
 * Zustand store for plate state.
 *
 * `positions` is a map keyed by position index (0-95), values are the
 * serialized PlatePosition objects returned by the API.
 */
const usePlateStore = create((set) => ({
  plateId: null,
  positions: {},

  /** Initialise from config injected by Django template */
  init: (cfg) =>
    set({
      plateId: cfg.plate_id,
    }),

  /** Bulk-set positions from API response */
  setPositions: (positionList) =>
    set({
      positions: Object.fromEntries(
        positionList.map((p) => [p.position, p]),
      ),
    }),

  /** Update a single position (after a mutation) */
  updatePosition: (position) =>
    set((state) => ({
      positions: { ...state.positions, [position.position]: position },
    })),
}));

export default usePlateStore;

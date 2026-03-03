import { create } from 'zustand';

/**
 * Zustand store for analysis order sample markers management.
 *
 * `sampleMarkers` is a map keyed by sample marker id.
 */
const useOrderStore = create((set) => ({
  orderId: null,
  orderLabel: null,
  sampleMarkers: {},
  selectedMarkerIds: {},
  selectedPlate: null,

  /** Initialise from config injected by Django template */
  init: (cfg) =>
    set({
      orderId: cfg.order_id ?? null,
      orderLabel: cfg.order_label ?? null,
    }),

  /** Set the selected order for filtering */
  setSelectedOrder: (orderId, orderLabel) =>
    set({
      orderId: orderId ?? null,
      orderLabel: orderLabel ?? null,
    }),

  /** Set the currently selected plate (for adding sample markers) */
  setSelectedPlate: (plate) =>
    set({ selectedPlate: plate }),

  /** Toggle selection of a single marker */
  toggleMarkerSelection: (id) =>
    set((state) => {
      const key = String(id);
      const newSelection = { ...state.selectedMarkerIds };
      if (newSelection[key]) {
        delete newSelection[key];
      } else {
        newSelection[key] = true;
      }
      return { selectedMarkerIds: newSelection };
    }),

  /** Clear all selections */
  clearSelection: () =>
    set({ selectedMarkerIds: {} }),

  /** Bulk-set sample markers from API response */
  setSampleMarkers: (markerList) =>
    set({
      sampleMarkers: Object.fromEntries(
        markerList.map((m) => [m.id, m]),
      ),
    }),
}));

export default useOrderStore;

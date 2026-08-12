import { create } from 'zustand';

/**
 * Zustand store for analysis order sample markers management.
 *
 * `sampleMarkers` is a map keyed by sample marker id (for fast lookup).
 * `sampleMarkerIds` is an array of ids preserving the order from API.
 * `sorting` contains the current sort field and direction.
 */
const useOrderStore = create((set) => ({
  orderId: null,
  orderLabel: null,
  orderStatus: null,
  orderStatusLabel: null,
  sampleMarkers: {},
  sampleMarkerIds: [],
  selectedMarkerIds: {},
  selectedPlate: null,
  selectedPositionForAdd: null, // { id, coordinate } - for adding single marker to specific position
  sorting: { field: null, direction: 'asc' }, // 'asc' or 'desc'
  sampleDisplayMode: 'genlab_id',

  /** Initialise from config injected by Django template */
  init: (cfg) =>
    set({
      orderId: cfg.order_id ?? null,
      orderLabel: cfg.order_label ?? null,
      orderStatus: cfg.order_status ?? null,
      orderStatusLabel: cfg.order_status_label ?? null,
    }),

  /** Set which sample identifier to display in analysis order UIs */
  setSampleDisplayMode: (sampleDisplayMode) => set({ sampleDisplayMode }),

  /** Set the selected order for filtering */
  setSelectedOrder: (orderId, orderLabel) =>
    set({
      orderId: orderId ?? null,
      orderLabel: orderLabel ?? null,
    }),

  /** Set the currently selected plate (for adding sample markers) */
  setSelectedPlate: (plate) => set({ selectedPlate: plate }),

  /** Set a position for single sample marker addition (id + coordinate) */
  setSelectedPositionForAdd: (position) => set({ selectedPositionForAdd: position }),

  /** Clear the position selection */
  clearSelectedPositionForAdd: () => set({ selectedPositionForAdd: null }),

  /** Set sorting field and direction */
  setSorting: (field, direction) => set({ sorting: { field, direction } }),

  /** Toggle sorting for a field */
  toggleSorting: (field) =>
    set((state) => {
      let newSorting;
      if (state.sorting.field === field) {
        // Toggle direction or clear if already descending
        if (state.sorting.direction === 'asc') {
          newSorting = { field, direction: 'desc' };
        } else {
          // Clear sorting
          newSorting = { field: null, direction: 'asc' };
        }
      } else {
        // New field, start with ascending
        newSorting = { field, direction: 'asc' };
      }
      console.log('[store] toggleSorting:', field, '-> new sorting:', newSorting);
      return { sorting: newSorting };
    }),

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
  clearSelection: () => set({ selectedMarkerIds: {} }),

  /** Bulk-set sample markers from API response (replaces all, preserves order) */
  setSampleMarkers: (markerList) =>
    set({
      sampleMarkers: Object.fromEntries(markerList.map((m) => [m.id, m])),
      sampleMarkerIds: markerList.map((m) => m.id),
    }),

  /** Clear all sample markers */
  clearSampleMarkers: () => set({ sampleMarkers: {}, sampleMarkerIds: [] }),
}));

export default useOrderStore;

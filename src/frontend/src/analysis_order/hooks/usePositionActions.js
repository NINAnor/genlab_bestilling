import { useMutation, useQueryClient } from '@tanstack/react-query';
import { client } from '../config';

/**
 * Invalidate all queries related to plate positions and sample markers.
 * Uses partial key matching so all related queries are refreshed.
 */
function invalidatePositionQueries(queryClient, { includePlates = true } = {}) {
  queryClient.invalidateQueries({ queryKey: ['analysisPlatePositions'] });
  queryClient.invalidateQueries({ queryKey: ['sample-markers'] });
  if (includePlates) {
    queryClient.invalidateQueries({ queryKey: ['analysis-plates-search'] });
  }
}

/**
 * Factory to create position action mutation hooks.
 * Reduces duplication for simple POST actions on plate positions.
 */
function usePositionActionMutation(action, { includePlates = true } = {}) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (positionId) => {
      const { data } = await client.post(
        `/api/plate-positions/${positionId}/${action}/`,
      );
      return data;
    },
    onSuccess: () => {
      invalidatePositionQueries(queryClient, { includePlates });
    },
  });
}

/**
 * Hook for reserving a plate position.
 */
export function useReservePosition() {
  return usePositionActionMutation('reserve');
}

/**
 * Hook for unreserving a plate position.
 */
export function useUnreservePosition() {
  return usePositionActionMutation('unreserve');
}

/**
 * Hook for removing a sample marker from a plate position.
 */
export function useRemoveSampleMarker() {
  return usePositionActionMutation('remove_analysis');
}

/**
 * Hook for editing notes on a plate position.
 */
export function useEditPositionNotes() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ positionId, notes }) => {
      const { data } = await client.post(
        `/api/plate-positions/${positionId}/edit_notes/`,
        { notes },
      );
      return data;
    },
    onSuccess: () => {
      invalidatePositionQueries(queryClient, { includePlates: false });
    },
  });
}

/**
 * Hook for moving a sample marker from one position to another.
 */
export function useMovePosition() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ sourcePositionId, targetPositionIndex }) => {
      const { data } = await client.post(
        `/api/plate-positions/${sourcePositionId}/move_to/`,
        { target_position: targetPositionIndex },
      );
      return data;
    },
    onSuccess: () => {
      invalidatePositionQueries(queryClient);
    },
  });
}

/**
 * Hook for setting a positive control on a reserved position.
 */
export function useSetPositiveControl() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ positionId, positiveControlId }) => {
      const { data } = await client.post(
        `/api/plate-positions/${positionId}/set_positive_control/`,
        { positive_control_id: positiveControlId },
      );
      return data;
    },
    onSuccess: () => {
      invalidatePositionQueries(queryClient, { includePlates: false });
    },
  });
}

/**
 * Hook for toggling the invalid status of a plate position.
 */
export function useTogglePositionInvalid() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (positionId) => {
      const { data } = await client.post(
        `/api/plate-positions/${positionId}/toggle-invalid/`,
      );
      return data;
    },
    onSuccess: () => {
      invalidatePositionQueries(queryClient, { includePlates: false });
    },
  });
}

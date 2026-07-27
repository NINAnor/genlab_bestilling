import { useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { client } from '../config';

/**
 * Mutation hook to create a new analysis plate.
 * @param {Object} params
 * @param {string} params.name - Optional plate name
 * @param {number} params.analysis_type - Required analysis type ID
 * @param {string[]} params.markers - Optional array of marker names (primary keys)
 */
export function useCreatePlate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ name, analysis_type, markers = [] } = {}) => {
      const { data } = await client.post('/staff/api/analysis-plates/', {
        name,
        analysis_type,
        markers,
      });
      return data;
    },
    onSuccess: (data) => {
      toast.success(`Created plate ${data.label}`);
      // Invalidate plate queries to refresh the list
      queryClient.invalidateQueries({ queryKey: ['analysis-plates-search'] });
    },
    onError: (error) => {
      const message = error.response?.data?.error || 'Failed to create plate';
      toast.error(message);
    },
  });
}

/**
 * Mutation hook to set the analysis date for a plate.
 */
export function useSetAnalysisDate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ plateId, analysisDate }) => {
      const { data } = await client.post(
        `/staff/api/analysis-plates/${plateId}/set-analysis-date/`,
        { analysis_date: analysisDate },
      );
      return data;
    },
    onSuccess: () => {
      toast.success('Analysis date updated');
      queryClient.invalidateQueries({ queryKey: ['analysis-plates-search'] });
    },
    onError: (error) => {
      const message = error.response?.data?.error || 'Failed to update analysis date';
      toast.error(message);
    },
  });
}

/**
 * Mutation hook to upload a result file for a plate.
 */
export function useUploadResultFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ plateId, file }) => {
      const formData = new FormData();
      formData.append('result_file', file);
      const { data } = await client.post(
        `/staff/api/analysis-plates/${plateId}/upload-result-file/`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        },
      );
      return data;
    },
    onSuccess: () => {
      toast.success('Result file uploaded');
      queryClient.invalidateQueries({ queryKey: ['analysis-plates-search'] });
    },
    onError: (error) => {
      const message = error.response?.data?.error || 'Failed to upload result file';
      toast.error(message);
    },
  });
}

/**
 * Mutation hook to delete a result file for a plate.
 */
export function useDeleteResultFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ plateId }) => {
      const { data } = await client.post(
        `/staff/api/analysis-plates/${plateId}/delete-result-file/`,
      );
      return data;
    },
    onSuccess: () => {
      toast.success('Result file deleted');
      queryClient.invalidateQueries({ queryKey: ['analysis-plates-search'] });
    },
    onError: (error) => {
      const message = error.response?.data?.error || 'Failed to delete result file';
      toast.error(message);
    },
  });
}

/**
 * Mutation hook to update the name of a plate.
 */
export function useUpdatePlateName() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ plateId, name }) => {
      const { data } = await client.post(`/staff/api/analysis-plates/${plateId}/set-name/`, {
        name,
      });
      return data;
    },
    onSuccess: () => {
      toast.success('Plate name updated');
      queryClient.invalidateQueries({ queryKey: ['analysis-plates-search'] });
    },
    onError: (error) => {
      const message = error.response?.data?.error || 'Failed to update plate name';
      toast.error(message);
    },
  });
}

/**
 * Mutation hook to clone a plate.
 * Creates a new plate with same name, analysis_type, markers, and filled positions,
 * but without analysis_date and result_file.
 */
export function useClonePlate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ plateId }) => {
      const { data } = await client.post(`/staff/api/analysis-plates/${plateId}/clone/`);
      return data;
    },
    onSuccess: (data) => {
      toast.success(data.message || 'Plate cloned successfully');
      queryClient.invalidateQueries({ queryKey: ['analysis-plates-search'] });
    },
    onError: (error) => {
      const message = error.response?.data?.error || 'Failed to clone plate';
      toast.error(message);
    },
  });
}

/**
 * Mutation hook to empty positions on a plate by row and/or column.
 */
export function useEmptyPositions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ plateId, row, column }) => {
      const payload = {};
      if (row) payload.row = row;
      if (column !== undefined && column !== null) payload.column = column;
      const { data } = await client.post(`/staff/api/analysis-plates/${plateId}/empty/`, payload);
      return data;
    },
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries({ queryKey: ['analysis-plates-search'] });
      queryClient.invalidateQueries({ queryKey: ['analysisPlatePositions'] });
    },
    onError: (error) => {
      const message = error.response?.data?.error || 'Failed to empty positions';
      toast.error(message);
    },
  });
}

/**
 * Mutation hook to reserve positions on a plate by row and/or column.
 */
export function useReservePositions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ plateId, row, column }) => {
      const payload = {};
      if (row) payload.row = row;
      if (column !== undefined && column !== null) payload.column = column;
      const { data } = await client.post(`/staff/api/analysis-plates/${plateId}/reserve/`, payload);
      return data;
    },
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries({ queryKey: ['analysis-plates-search'] });
      queryClient.invalidateQueries({ queryKey: ['analysisPlatePositions'] });
    },
    onError: (error) => {
      const message = error.response?.data?.error || 'Failed to reserve positions';
      toast.error(message);
    },
  });
}

/**
 * Mutation hook to delete a plate.
 */
export function useDeletePlate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ plateId }) => {
      const { data } = await client.delete(`/staff/api/analysis-plates/${plateId}/delete/`);
      return data;
    },
    onSuccess: (data) => {
      toast.success(data.message || 'Plate deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['analysis-plates-search'] });
    },
    onError: (error) => {
      const message = error.response?.data?.error || 'Failed to delete plate';
      toast.error(message);
    },
  });
}

/**
 * Mutation hook to update a plate's properties (name, analysis_type, markers).
 * @param {Object} params
 * @param {number} params.plateId - The plate ID to update
 * @param {string} [params.name] - Optional plate name
 * @param {number} [params.analysis_type] - Optional analysis type ID
 * @param {string[]} [params.markers] - Optional array of marker names
 */
export function useUpdatePlate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ plateId, name, analysis_type, markers }) => {
      const payload = {};
      if (name !== undefined) payload.name = name;
      if (analysis_type !== undefined) payload.analysis_type = analysis_type;
      if (markers !== undefined) payload.markers = markers;
      const { data } = await client.patch(`/staff/api/analysis-plates/${plateId}/`, payload);
      return data;
    },
    onSuccess: (data) => {
      toast.success(`Updated plate ${data.label}`);
      queryClient.invalidateQueries({ queryKey: ['analysis-plates-search'] });
    },
    onError: (error) => {
      const message = error.response?.data?.error || 'Failed to update plate';
      toast.error(message);
    },
  });
}

/**
 * Mutation hook to set or clear the billing date for a plate.
 * @param {Object} params
 * @param {string} params.plateId - The plate UUID
 * @param {string|null} params.billedAt - ISO datetime string or null to clear
 */
export function useSetPlateBilled() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ plateId, billedAt }) => {
      const { data } = await client.patch(`/staff/api/analysis-plates/${plateId}/`, {
        billed_at: billedAt,
      });
      return data;
    },
    onSuccess: (data) => {
      const message = data.billed_at ? 'Billing date updated' : 'Billing date cleared';
      toast.success(message);
      queryClient.invalidateQueries({ queryKey: ['analysis-plates-search'] });
    },
    onError: (error) => {
      const message = error.response?.data?.error || 'Failed to update billing date';
      toast.error(message);
    },
  });
}

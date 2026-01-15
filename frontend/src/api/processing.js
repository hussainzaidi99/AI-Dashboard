import apiClient from './client';

export const processingApi = {
    start: async (fileId, options = {}) => {
        const response = await apiClient.post('/processing', {
            file_id: fileId,
            ...options
        });
        return response.data;
    },

    getStatus: async (fileId) => {
        const response = await apiClient.get(`/processing/status/${fileId}`);
        return response.data;
    },

    getResult: async (fileId) => {
        const response = await apiClient.get(`/processing/result/${fileId}`);
        return response.data;
    }
};

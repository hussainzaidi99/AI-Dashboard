import apiClient from './client';

export const dataApi = {
    getRows: async (fileId, sheetIndex = 0, limit = 100) => {
        const response = await apiClient.get(`/data/${fileId}`, {
            params: { sheet_index: sheetIndex, limit }
        });
        return response.data;
    },

    getProfile: async (fileId, sheetIndex = 0) => {
        const response = await apiClient.get('/data/profile', {
            params: { file_id: fileId, sheet_index: sheetIndex }
        });
        return response.data;
    },

    getQuality: async (fileId, sheetIndex = 0) => {
        const response = await apiClient.get('/data/quality', {
            params: { file_id: fileId, sheet_index: sheetIndex }
        });
        return response.data;
    },

    getStatistics: async (fileId, sheetIndex = 0) => {
        const response = await apiClient.get('/data/statistics', {
            params: { file_id: fileId, sheet_index: sheetIndex }
        });
        return response.data;
    }
};

import apiClient from './client';

export const chartsApi = {
    create: async (payload) => {
        const response = await apiClient.post('/charts/create', payload);
        return response.data;
    },

    recommend: async (fileId, sheetIndex = 0, userIntent = null) => {
        const response = await apiClient.post('/charts/recommend', null, {
            params: { file_id: fileId, sheet_index: sheetIndex, user_intent: userIntent }
        });
        return response.data;
    },

    getDashboard: async (fileId, sheetIndex = 0) => {
        const response = await apiClient.post('/charts/dashboard', {
            file_id: fileId,
            sheet_index: sheetIndex
        });
        return response.data;
    },

    getTypes: async () => {
        const response = await apiClient.get('/charts/types');
        return response.data;
    }
};

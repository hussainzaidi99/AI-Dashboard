import apiClient from './client';

export const aiApi = {
    getInsights: async (fileId, sheetIndex = 0) => {
        const response = await apiClient.post('/ai/insights', {
            file_id: fileId,
            sheet_index: sheetIndex
        });
        return response.data;
    },

    askQuestion: async (fileId, question, sheetIndex = 0) => {
        const response = await apiClient.post('/ai/ask', {
            file_id: fileId,
            question: question,
            sheet_index: sheetIndex
        });
        return response.data;
    },

    parseQuery: async (fileId, query, sheetIndex = 0) => {
        const response = await apiClient.post('/ai/query', {
            file_id: fileId,
            query: query,
            sheet_index: sheetIndex
        });
        return response.data;
    },

    suggestQueries: async (fileId, sheetIndex = 0) => {
        const response = await apiClient.post('/ai/suggest-queries', {
            file_id: fileId,
            sheet_index: sheetIndex
        });
        return response.data;
    }
};

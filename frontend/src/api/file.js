import apiClient from './client';

export const fileApi = {
    upload: async (file, onUploadProgress) => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await apiClient.post('/upload/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: (progressEvent) => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                if (onUploadProgress) onUploadProgress(percentCompleted);
            },
        });
        return response.data;
    },

    list: async () => {
        const response = await apiClient.get('/upload/list');
        return response.data;
    },

    getStatus: async (fileId) => {
        const response = await apiClient.get(`/upload/status/${fileId}`);
        return response.data;
    },

    delete: async (fileId) => {
        const response = await apiClient.delete(`/upload/delete/${fileId}`);
        return response.data;
    }
};

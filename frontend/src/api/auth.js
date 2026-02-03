import apiClient from './client';

export const authApi = {
    login: async (email, password) => {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);
        const response = await apiClient.post('/auth/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        return response.data;
    },
    googleLogin: async (token) => {
        const response = await apiClient.post('/auth/google', { token });
        return response.data;
    },
    register: async (email, password, fullName) => {
        const response = await apiClient.post('/auth/register', {
            email,
            password,
            full_name: fullName,
            role: 'user'
        });
        return response.data;
    },
    verifyEmail: async (email, code) => {
        const response = await apiClient.post('/auth/verify-email', { email, code });
        return response.data;
    },
    resendVerification: async (email) => {
        const response = await apiClient.post('/auth/resend-verification', { email });
        return response.data;
    },
    requestPasswordReset: async (email) => {
        const response = await apiClient.post('/auth/password-reset/send-code', { email });
        return response.data;
    },
    verifyResetCode: async (email, code) => {
        const response = await apiClient.post('/auth/password-reset/verify-code', { email, code });
        return response.data;
    },
    confirmPasswordReset: async (email, code, newPassword) => {
        const response = await apiClient.post('/auth/password-reset/confirm', {
            email,
            code,
            new_password: newPassword
        });
        return response.data;
    }
};

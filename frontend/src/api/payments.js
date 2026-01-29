import client from './client';

export const paymentsApi = {
    // Create checkout session
    createCheckoutSession: async (planId) => {
        const response = await client.post(`/payments/create-checkout-session?plan_id=${planId}`);
        return response.data;
    },

    // Confirm payment session
    confirmPayment: async (sessionId) => {
        const response = await client.get(`/payments/confirm?session_id=${sessionId}`);
        return response.data;
    }
};

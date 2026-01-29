
import client from './client';

export const creditsApi = {
    // Get user's current credit balance
    getCredits: async () => {
        const response = await client.get('/credits/');
        return response.data;
    },

    // Grant free tier (Dev/Testing only)
    grantFreeTier: async () => {
        const response = await client.post('/credits/grant-free-tier');
        return response.data;
    }
};

import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { GoogleOAuthProvider } from '@react-oauth/google'
import App from './App.jsx'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

import { DatasetProvider } from './context/DatasetContext';
import { AuthProvider } from './context/AuthContext';

import { BrowserRouter } from 'react-router-dom';

// Safety check for Google Client ID
const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
if (!googleClientId) {
  console.error('❌ VITE_GOOGLE_CLIENT_ID is not set! Google OAuth will not work.');
  console.error('Please add VITE_GOOGLE_CLIENT_ID to your environment variables in AWS Amplify.');
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <GoogleOAuthProvider clientId={googleClientId || 'dummy-client-id'}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthProvider>
            <DatasetProvider>
              <App />
            </DatasetProvider>
          </AuthProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </GoogleOAuthProvider>
  </React.StrictMode>,
)

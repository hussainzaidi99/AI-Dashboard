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
import { ThemeProvider } from './context/ThemeContext';
import { NotificationProvider } from './context/NotificationContext';


import { BrowserRouter } from 'react-router-dom';

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

if (!googleClientId) {
  console.warn('⚠️ VITE_GOOGLE_CLIENT_ID is not configured. Google OAuth will be disabled.');
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {googleClientId ? (
      <GoogleOAuthProvider clientId={googleClientId}>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <NotificationProvider>
              <AuthProvider>
                <ThemeProvider>
                  <DatasetProvider>
                    <App />
                  </DatasetProvider>
                </ThemeProvider>
              </AuthProvider>
            </NotificationProvider>
          </BrowserRouter>
        </QueryClientProvider>
      </GoogleOAuthProvider>
    ) : (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <NotificationProvider>
            <AuthProvider>
              <ThemeProvider>
                <DatasetProvider>
                  <App />
                </DatasetProvider>
              </ThemeProvider>
            </AuthProvider>
          </NotificationProvider>
        </BrowserRouter>
      </QueryClientProvider>
    )}
  </React.StrictMode>,
)

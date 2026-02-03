import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/dashboard/Layout';
import Landing from './pages/Landing';
import Overview from './pages/Overview';
import DataUpload from './pages/DataUpload';
import VisualAnalysis from './pages/VisualAnalysis';
import RawData from './pages/RawData';
import AIIntelligence from './pages/AIIntelligence';
import Login from './pages/Login';
import Register from './pages/Register';
import EmailVerification from './pages/EmailVerification';
import ForgotPassword from './pages/ForgotPassword';
import Chatbot from './components/ai/Chatbot';
import Pricing from './pages/Pricing';
import PaymentStatus from './pages/PaymentStatus';
import Docs from './pages/Docs';
import Privacy from './pages/Privacy';
import Terms from './pages/Terms';
import Settings from './pages/Settings';
import About from './pages/About';
import ProtectedRoute from './components/shared/ProtectedRoute';
import { useAuth } from './context/AuthContext';
import { Toaster } from './components/ui/Sonner';

function App() {
  const { isAuthenticated, loading } = useAuth();
  const [authView, setAuthView] = useState('login');

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-white/5 border-t-white rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <>
      <Toaster position="top-right" richColors closeButton />
      <Routes>
        <Route
          path="/"
          element={<Landing />}
        />

        <Route
          path="/login"
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : (
              authView === 'login'
                ? <Login onToggle={() => setAuthView('register')} />
                : <Navigate to="/register" replace />
            )
          }
        />
        <Route
          path="/register"
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : (
              authView === 'register'
                ? <Register onToggle={() => setAuthView('login')} />
                : <Navigate to="/login" replace />
            )
          }
        />

        {/* Email Verification - Public Route */}
        <Route
          path="/verify-email"
          element={<EmailVerification />}
        />

        <Route
          path="/forgot-password"
          element={<ForgotPassword />}
        />

        <Route path="/docs" element={<Docs />} />
        <Route path="/privacy" element={<Privacy />} />
        <Route path="/terms" element={<Terms />} />

        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Layout>
                <Routes>
                  <Route path="/dashboard" element={<Overview />} />
                  <Route path="/upload" element={<DataUpload />} />
                  <Route path="/intelligence" element={<AIIntelligence />} />
                  <Route path="/data" element={<RawData />} />
                  <Route path="/pricing" element={<Pricing />} />
                  <Route path="/payment/success" element={<PaymentStatus />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/about" element={<About />} />
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
                <Chatbot />
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </>
  );
}

export default App;

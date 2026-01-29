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
import Chatbot from './components/ai/Chatbot';
import Pricing from './pages/Pricing';
import PaymentStatus from './pages/PaymentStatus';
import ProtectedRoute from './components/shared/ProtectedRoute';
import { useAuth } from './context/AuthContext';

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
                <Route path="/templates" element={<div className="p-10 text-center"><h2 className="text-3xl font-bold">Dashboard Templates</h2><p className="text-muted-foreground mt-2">Coming Soon...</p></div>} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
              <Chatbot />
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;

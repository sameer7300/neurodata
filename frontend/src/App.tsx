import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import './styles/animations.css';

// Layout Components
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import GuidanceBot from './components/GuidanceBot';

// Page Components
import HomePage from './pages/HomePage';
import DatasetsPage from './pages/DatasetsPage';
import DatasetDetailPage from './pages/DatasetDetailPage';
import ProfilePage from './pages/ProfilePage';
import UploadPage from './pages/UploadPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import SettingsPage from './pages/SettingsPage';
import EscrowPage from './pages/EscrowPage';
import PurchasesPage from './pages/PurchasesPage';
import MLTrainingPage from './pages/MLTrainingPage';
import MLJobDetailPage from './pages/MLJobDetailPage';

// Auth Components
import ProtectedRoute from './components/auth/ProtectedRoute';

// Context Providers
import { Web3Provider } from './contexts/Web3Context';
import { AuthProvider } from './contexts/AuthContext';

function App() {
  return (
    <Web3Provider>
      <AuthProvider>
        <Router>
          <div className="min-h-screen bg-gray-50 flex flex-col">
            <Navbar />
            
            <main className="flex-1">
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/datasets" element={<DatasetsPage />} />
                <Route path="/datasets/:id" element={<DatasetDetailPage />} />
                
                {/* Protected Routes - Require Authentication */}
                <Route path="/dashboard" element={
                  <ProtectedRoute>
                    <DashboardPage />
                  </ProtectedRoute>
                } />
                <Route path="/profile" element={
                  <ProtectedRoute>
                    <ProfilePage />
                  </ProtectedRoute>
                } />
                <Route path="/upload" element={
                  <ProtectedRoute>
                    <UploadPage />
                  </ProtectedRoute>
                } />
                <Route path="/settings" element={
                  <ProtectedRoute>
                    <SettingsPage />
                  </ProtectedRoute>
                } />
                <Route path="/marketplace/escrows" element={
                  <ProtectedRoute>
                    <EscrowPage />
                  </ProtectedRoute>
                } />
                <Route path="/marketplace/purchases" element={
                  <ProtectedRoute>
                    <PurchasesPage />
                  </ProtectedRoute>
                } />
                <Route path="/ml/training" element={
                  <ProtectedRoute>
                    <MLTrainingPage />
                  </ProtectedRoute>
                } />
                <Route path="/ml/jobs/:jobId" element={
                  <ProtectedRoute>
                    <MLJobDetailPage />
                  </ProtectedRoute>
                } />
                
                {/* Auth Routes - Redirect if already authenticated */}
                <Route path="/login" element={
                  <ProtectedRoute requireAuth={false}>
                    <LoginPage />
                  </ProtectedRoute>
                } />
                <Route path="/register" element={
                  <ProtectedRoute requireAuth={false}>
                    <RegisterPage />
                  </ProtectedRoute>
                } />
              </Routes>
            </main>
            
            <Footer />
            
            {/* Guidance Bot */}
            <GuidanceBot />
            
            {/* Toast Notifications */}
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#363636',
                  color: '#fff',
                },
                success: {
                  duration: 3000,
                  iconTheme: {
                    primary: '#22c55e',
                    secondary: '#fff',
                  },
                },
                error: {
                  duration: 5000,
                  iconTheme: {
                    primary: '#ef4444',
                    secondary: '#fff',
                  },
                },
              }}
            />
          </div>
        </Router>
      </AuthProvider>
    </Web3Provider>
  );
}

export default App;

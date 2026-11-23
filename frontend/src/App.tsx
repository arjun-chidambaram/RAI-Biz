import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { VerifyOtpPage } from './pages/VerifyOtpPage';
import { DashboardPage } from './pages/DashboardPage';
import { BusinessProfilePage } from './pages/BusinessProfilePage';
import { AssessmentPage } from './pages/AssessmentPage';
import { FairnessPage } from './pages/FairnessPage';
import { ExplainableAIPage } from './pages/ExplainableAIPage';
import { PrivacyGuardPage } from './pages/PrivacyGuardPage';
import { GreenAIMonitorPage } from './pages/GreenAIMonitorPage';
import { DatasetManagerPage } from './pages/DatasetManagerPage';
import { RiskCenterPage } from './pages/RiskCenterPage';
import { RecommendationsPage } from './pages/RecommendationsPage';
import { ReportsPage } from './pages/ReportsPage';
import { HistoryPage } from './pages/HistoryPage';
import { SettingsPage } from './pages/SettingsPage';

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Authentication Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/verify-otp" element={<VerifyOtpPage />} />

          {/* Protected RAI-Biz Platform Modules */}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<Layout />}>
              <Route index element={<DashboardPage />} />
              <Route path="profile" element={<BusinessProfilePage />} />
              <Route path="assessment" element={<AssessmentPage />} />
              <Route path="fairness" element={<FairnessPage />} />
              <Route path="xai" element={<ExplainableAIPage />} />
              <Route path="privacy" element={<PrivacyGuardPage />} />
              <Route path="green-ai" element={<GreenAIMonitorPage />} />
              <Route path="datasets" element={<DatasetManagerPage />} />
              <Route path="risks" element={<RiskCenterPage />} />
              <Route path="recommendations" element={<RecommendationsPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="history" element={<HistoryPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;

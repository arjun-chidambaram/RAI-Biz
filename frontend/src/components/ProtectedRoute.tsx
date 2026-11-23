import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, Loader2 } from 'lucide-react';

export const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-100">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-teal-500 via-sky-500 to-indigo-600 flex items-center justify-center shadow-xl shadow-teal-500/20 mb-4 animate-pulse">
          <ShieldCheck className="w-8 h-8 text-white" />
        </div>
        <div className="flex items-center space-x-2 text-sm text-slate-400">
          <Loader2 className="w-4 h-4 animate-spin text-teal-400" />
          <span>Verifying RAI-Biz session...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
};

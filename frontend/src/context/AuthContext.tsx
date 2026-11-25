import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api, User, Business, AIApplication, AuthStatusResponse } from '../api/client';

interface AuthContextType {
  user: User | null;
  business: Business | null;
  application: AIApplication | null;
  loading: boolean;
  isAuthenticated: boolean;
  pendingEmail: string;
  setPendingEmail: (email: string) => void;
  sendOtp: (email: string) => Promise<{ success: boolean; message: string; email: string }>;
  verifyOtp: (email: string, otp: string) => Promise<AuthStatusResponse>;
  resendOtp: (email: string) => Promise<{ success: boolean; message: string; email: string }>;
  demoLogin: (email: string) => Promise<AuthStatusResponse>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [business, setBusiness] = useState<Business | null>(null);
  const [application, setApplication] = useState<AIApplication | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [pendingEmail, setPendingEmail] = useState<string>(() => {
    return sessionStorage.getItem('rai_biz_pending_email') || '';
  });

  const updatePendingEmail = (email: string) => {
    setPendingEmail(email);
    if (email) {
      sessionStorage.setItem('rai_biz_pending_email', email);
    } else {
      sessionStorage.removeItem('rai_biz_pending_email');
    }
  };

  const refreshUser = async () => {
    try {
      const res = await api.getMe();
      if (res.authenticated && res.user) {
        setUser(res.user);
        setBusiness(res.business || null);
        setApplication(res.application || null);
      } else {
        setUser(null);
        setBusiness(null);
        setApplication(null);
      }
    } catch {
      setUser(null);
      setBusiness(null);
      setApplication(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const sendOtp = async (email: string) => {
    const res = await api.sendOtp(email);
    if (res.success) {
      updatePendingEmail(email);
    }
    return res;
  };

  const resendOtp = async (email: string) => {
    return api.resendOtp(email);
  };

  const verifyOtp = async (email: string, otp: string) => {
    const res = await api.verifyOtp(email, otp);
    if (res.authenticated && res.user) {
      setUser(res.user);
      setBusiness(res.business || null);
      setApplication(res.application || null);
      updatePendingEmail('');
    }
    return res;
  };

  const demoLogin = async (email: string) => {
    const res = await api.demoLogin(email);
    if (res.authenticated && res.user) {
      setUser(res.user);
      setBusiness(res.business || null);
      setApplication(res.application || null);
      updatePendingEmail('');
    }
    return res;
  };

  const logout = async () => {
    try {
      await api.logout();
    } finally {
      setUser(null);
      setBusiness(null);
      setApplication(null);
      updatePendingEmail('');
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        business,
        application,
        loading,
        isAuthenticated: !!user,
        pendingEmail,
        setPendingEmail: updatePendingEmail,
        sendOtp,
        verifyOtp,
        resendOtp,
        demoLogin,
        logout,
        refreshUser
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

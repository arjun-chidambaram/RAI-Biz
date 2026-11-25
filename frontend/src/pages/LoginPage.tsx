import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ShieldCheck, Mail, ArrowRight, Loader2, AlertCircle, CheckCircle, Sparkles, Lock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [infoMessage, setInfoMessage] = useState('');
  const { sendOtp, demoLogin, isAuthenticated, setPendingEmail } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (isAuthenticated) {
      const from = (location.state as any)?.from?.pathname || '/';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  const validateEmail = (val: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val.trim());
  };

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');
    setInfoMessage('');

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail) {
      setErrorMessage('Please enter your work or corporate email address.');
      return;
    }
    if (!validateEmail(cleanEmail)) {
      setErrorMessage('Please enter a valid email format (e.g., name@company.com).');
      return;
    }

    try {
      setLoading(true);
      const res = await sendOtp(cleanEmail);
      if (res.success) {
        setPendingEmail(cleanEmail);
        navigate('/verify-otp', { state: { email: cleanEmail } });
      } else {
        setErrorMessage(res.message || 'Failed to send verification code.');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'An error occurred while connecting to authentication service.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async (demoEmail: string) => {
    setErrorMessage('');
    setInfoMessage('');
    try {
      setDemoLoading(demoEmail);
      const res = await demoLogin(demoEmail);
      if (res.authenticated) {
        setInfoMessage(`Authenticated as ${res.user?.role || 'Demo User'}. Redirecting to workspace...`);
        const from = (location.state as any)?.from?.pathname || '/';
        navigate(from, { replace: true });
      } else {
        setErrorMessage(res.message || 'Demo authentication failed.');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'An error occurred connecting to demo authentication service.');
    } finally {
      setDemoLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md z-10">
        {/* Brand Header */}
        <div className="flex justify-center mb-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-teal-500 via-sky-500 to-indigo-600 flex items-center justify-center shadow-xl shadow-teal-500/25 border border-teal-400/20">
            <ShieldCheck className="w-8 h-8 text-white" />
          </div>
        </div>
        <div className="text-center">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-400 text-xs font-semibold mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            <span>SME AI Governance & Risk Optimization</span>
          </div>
          <h2 className="text-3xl font-extrabold tracking-tight text-white">
            RAI-Biz Platform
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Secure, passwordless authentication for SME executives and AI teams.
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md z-10 px-4 sm:px-0">
        <div className="bg-slate-900/90 border border-slate-800 backdrop-blur-xl py-8 px-6 shadow-2xl rounded-2xl sm:px-10">
          <form className="space-y-5" onSubmit={handleSendOtp}>
            <div>
              <label htmlFor="email" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                Work Email Address
              </label>
              <div className="relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <Mail className="h-4 w-4 text-slate-500" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@enterprise.com"
                  className="block w-full pl-10 pr-3 py-2.5 bg-slate-950/70 border border-slate-700 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition"
                  disabled={loading}
                />
              </div>
              <p className="mt-1.5 text-[11px] text-slate-400">
                Single-use 6-digit OTP will be dispatched. New users are automatically registered.
              </p>
            </div>

            {/* Error Banner */}
            {errorMessage && (
              <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800/80 text-rose-300 text-xs flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Info Banner */}
            {infoMessage && (
              <div className="p-3 rounded-lg bg-teal-950/50 border border-teal-800/80 text-teal-300 text-xs flex items-start space-x-2">
                <CheckCircle className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
                <span>{infoMessage}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center py-2.5 px-4 rounded-lg shadow-lg text-sm font-semibold text-white bg-gradient-to-r from-teal-500 via-sky-600 to-indigo-600 hover:from-teal-400 hover:to-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  <span>Sending Verification Code...</span>
                </>
              ) : (
                <>
                  <span>Send Verification Code</span>
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-0.5 transition-transform" />
                </>
              )}
            </button>
          </form>

          {/* Controlled Hackathon Demo Access */}
          <div className="mt-6 pt-5 border-t border-slate-800/80 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-teal-400 flex items-center space-x-1.5">
                <Sparkles className="w-3.5 h-3.5 text-teal-400" />
                <span>Hackathon Demo Access</span>
              </span>
              <span className="text-[10px] text-sky-400 bg-sky-950/80 px-2 py-0.5 rounded border border-sky-800/50 font-medium">
                1-Click Judge Session
              </span>
            </div>

            <p className="text-[11px] text-slate-400 leading-relaxed">
              Resend sandbox restricts OTP dispatch to the verified account owner. Evaluators and judges can launch isolated demo environments directly:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                disabled={loading || !!demoLoading}
                onClick={() => handleDemoLogin('admin@smarthire.ai')}
                className="p-2.5 bg-slate-800/80 hover:bg-slate-800 border border-teal-500/30 hover:border-teal-500/60 rounded-xl text-left transition group disabled:opacity-50 disabled:cursor-not-allowed shadow-xs"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-slate-200 group-hover:text-white flex items-center space-x-1">
                    <span>SmartHire Admin</span>
                  </span>
                  <span className="text-[9px] bg-teal-950/90 text-teal-300 px-1.5 py-0.5 rounded border border-teal-700/50">
                    SME Lead
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 truncate">
                  {demoLoading === 'admin@smarthire.ai' ? (
                    <span className="flex items-center text-teal-400">
                      <Loader2 className="w-3 h-3 animate-spin mr-1" />
                      Authenticating...
                    </span>
                  ) : (
                    'admin@smarthire.ai'
                  )}
                </div>
              </button>

              <button
                type="button"
                disabled={loading || !!demoLoading}
                onClick={() => handleDemoLogin('auditor@raibiz.io')}
                className="p-2.5 bg-slate-800/80 hover:bg-slate-800 border border-sky-500/30 hover:border-sky-500/60 rounded-xl text-left transition group disabled:opacity-50 disabled:cursor-not-allowed shadow-xs"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-slate-200 group-hover:text-white flex items-center space-x-1">
                    <span>Independent Auditor</span>
                  </span>
                  <span className="text-[9px] bg-sky-950/90 text-sky-300 px-1.5 py-0.5 rounded border border-sky-700/50">
                    Audit View
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 truncate">
                  {demoLoading === 'auditor@raibiz.io' ? (
                    <span className="flex items-center text-sky-400">
                      <Loader2 className="w-3 h-3 animate-spin mr-1" />
                      Authenticating...
                    </span>
                  ) : (
                    'auditor@raibiz.io'
                  )}
                </div>
              </button>
            </div>
          </div>

          {/* Security Features Callout */}
          <div className="mt-6 flex items-center justify-center space-x-2 text-[11px] text-slate-500">
            <Lock className="w-3.5 h-3.5 text-teal-500" />
            <span>Cryptographic 256-bit hash verification & HttpOnly sessions</span>
          </div>
        </div>

        {/* Footer info */}
        <p className="mt-4 text-center text-xs text-slate-500">
          RAI-Biz Responsible AI Governance & Risk Assessment Framework
        </p>
      </div>
    </div>
  );
};

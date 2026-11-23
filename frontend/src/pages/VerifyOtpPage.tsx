import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ShieldCheck, ArrowLeft, RefreshCw, Loader2, AlertCircle, CheckCircle, KeyRound, Mail } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const VerifyOtpPage: React.FC = () => {
  const [otpDigits, setOtpDigits] = useState<string[]>(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [cooldown, setCooldown] = useState<number>(60);
  
  const { verifyOtp, resendOtp, pendingEmail, setPendingEmail } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const email = (location.state as any)?.email || pendingEmail;
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // If no email is provided, redirect back to login
  useEffect(() => {
    if (!email) {
      navigate('/login', { replace: true });
    }
  }, [email, navigate]);

  // Countdown timer for resend
  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  // Focus first input on mount
  useEffect(() => {
    if (inputRefs.current[0]) {
      inputRefs.current[0].focus();
    }
  }, []);

  const handleDigitChange = (index: number, val: string) => {
    // Only allow numbers
    const clean = val.replace(/\D/g, '');
    if (!clean) {
      const copy = [...otpDigits];
      copy[index] = '';
      setOtpDigits(copy);
      return;
    }

    // If pasted multiple digits
    if (clean.length > 1) {
      const copy = [...otpDigits];
      const chars = clean.slice(0, 6).split('');
      chars.forEach((c, i) => {
        if (index + i < 6) copy[index + i] = c;
      });
      setOtpDigits(copy);
      const nextIndex = Math.min(index + chars.length, 5);
      inputRefs.current[nextIndex]?.focus();
      return;
    }

    const copy = [...otpDigits];
    copy[index] = clean;
    setOtpDigits(copy);

    // Auto advance to next input
    if (index < 5 && clean) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const fullOtp = otpDigits.join('');

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');

    if (fullOtp.length !== 6) {
      setErrorMessage('Please enter the complete 6-digit verification code.');
      return;
    }

    try {
      setLoading(true);
      const res = await verifyOtp(email, fullOtp);
      if (res.authenticated) {
        setSuccessMessage('Authentication verified successfully! Redirecting...');
        setTimeout(() => {
          navigate('/', { replace: true });
        }, 600);
      } else {
        setErrorMessage(res.message || 'Verification failed. Please check the code.');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Invalid or expired verification code.');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (cooldown > 0 || resending) return;
    setErrorMessage('');
    setSuccessMessage('');

    try {
      setResending(true);
      const res = await resendOtp(email);
      if (res.success) {
        setSuccessMessage('A fresh verification code has been dispatched.');
        setCooldown(60);
        setOtpDigits(['', '', '', '', '', '']);
        inputRefs.current[0]?.focus();
      } else {
        setErrorMessage(res.message || 'Failed to resend code.');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to resend verification code.');
    } finally {
      setResending(false);
    }
  };

  const handleChangeEmail = () => {
    setPendingEmail('');
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md z-10">
        {/* Brand Header */}
        <div className="flex justify-center mb-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-teal-500 via-sky-500 to-indigo-600 flex items-center justify-center shadow-xl shadow-teal-500/25 border border-teal-400/20">
            <KeyRound className="w-8 h-8 text-white" />
          </div>
        </div>
        <div className="text-center">
          <h2 className="text-3xl font-extrabold tracking-tight text-white">
            Verify Your Email
          </h2>
          <div className="mt-2 text-sm text-slate-400 flex items-center justify-center space-x-1.5">
            <span>Code dispatched to:</span>
            <span className="font-semibold text-teal-400">{email}</span>
          </div>
          <button
            type="button"
            onClick={handleChangeEmail}
            className="mt-1 text-xs text-sky-400 hover:text-sky-300 inline-flex items-center space-x-1 underline underline-offset-2 transition"
          >
            <ArrowLeft className="w-3 h-3" />
            <span>Change email address</span>
          </button>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md z-10 px-4 sm:px-0">
        <div className="bg-slate-900/90 border border-slate-800 backdrop-blur-xl py-8 px-6 shadow-2xl rounded-2xl sm:px-10">
          <form className="space-y-6" onSubmit={handleVerify}>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 text-center mb-3">
                Enter 6-Digit Verification Code
              </label>

              {/* 6 Digit Inputs */}
              <div className="flex justify-center space-x-2 sm:space-x-3">
                {otpDigits.map((digit, idx) => (
                  <input
                    key={idx}
                    ref={(el) => {
                      inputRefs.current[idx] = el;
                    }}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleDigitChange(idx, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(idx, e)}
                    className="w-11 h-14 sm:w-12 sm:h-14 text-center text-xl font-bold bg-slate-950/70 border border-slate-700 rounded-xl text-teal-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition shadow-inner"
                    disabled={loading}
                  />
                ))}
              </div>
              <p className="mt-2 text-center text-[11px] text-slate-500">
                Code expires in 5 minutes. Single-use only.
              </p>
            </div>

            {/* Error Banner */}
            {errorMessage && (
              <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800/80 text-rose-300 text-xs flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Success Banner */}
            {successMessage && (
              <div className="p-3 rounded-lg bg-emerald-950/50 border border-emerald-800/80 text-emerald-300 text-xs flex items-start space-x-2">
                <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>{successMessage}</span>
              </div>
            )}

            {/* Verify Button */}
            <button
              type="submit"
              disabled={loading || fullOtp.length !== 6}
              className="w-full flex items-center justify-center py-2.5 px-4 rounded-lg shadow-lg text-sm font-semibold text-white bg-gradient-to-r from-teal-500 via-sky-600 to-indigo-600 hover:from-teal-400 hover:to-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  <span>Verifying Code...</span>
                </>
              ) : (
                <span>Verify & Enter Workspace</span>
              )}
            </button>

            {/* Resend OTP Section */}
            <div className="pt-2 flex flex-col items-center justify-center space-y-2 text-xs">
              {cooldown > 0 ? (
                <div className="text-slate-400 flex items-center space-x-1.5">
                  <RefreshCw className="w-3.5 h-3.5 text-slate-500 animate-spin" />
                  <span>Resend code in <strong className="text-teal-400">{cooldown}s</strong></span>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={handleResend}
                  disabled={resending}
                  className="text-teal-400 hover:text-teal-300 font-medium inline-flex items-center space-x-1.5 hover:underline transition"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${resending ? 'animate-spin' : ''}`} />
                  <span>Resend verification code</span>
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Back Link */}
        <div className="mt-4 text-center">
          <button
            onClick={() => navigate('/login')}
            className="text-xs text-slate-500 hover:text-slate-400 inline-flex items-center space-x-1 transition"
          >
            <ArrowLeft className="w-3 h-3" />
            <span>Return to Login</span>
          </button>
        </div>
      </div>
    </div>
  );
};

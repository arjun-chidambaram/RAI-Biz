import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Building2,
  ClipboardCheck,
  Scale,
  Eye,
  ShieldCheck,
  Leaf,
  Database,
  AlertTriangle,
  Sparkles,
  FileText,
  History,
  Settings,
  ChevronRight,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  ShieldAlert,
  LogOut,
  UserCheck
} from 'lucide-react';
import { api, DashboardSummary } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const Layout: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, business, application, logout } = useAuth();

  const loadSummary = async () => {
    try {
      setLoading(true);
      const data = await api.getDashboardSummary();
      setSummary(data);
    } catch (err) {
      console.error("Failed to load dashboard summary", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, [location.pathname]);

  const handleSeedDemo = async () => {
    try {
      setSeeding(true);
      await api.seedDemo();
      await loadSummary();
      navigate('/');
    } catch (err) {
      alert("Failed to seed demo data");
    } finally {
      setSeeding(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navItems = [
    { name: 'Overview', path: '/', icon: LayoutDashboard },
    { name: 'Business Profile', path: '/profile', icon: Building2 },
    { name: 'AI Assessment', path: '/assessment', icon: ClipboardCheck },
    { name: 'Fairness & Bias Detection', path: '/fairness', icon: Scale },
    { name: 'Explainable AI', path: '/xai', icon: Eye },
    { name: 'Privacy Guard', path: '/privacy', icon: ShieldCheck },
    { name: 'Green AI Monitor', path: '/green-ai', icon: Leaf },
    { name: 'Dataset Manager', path: '/datasets', icon: Database },
    { name: 'Risk Center', path: '/risks', icon: AlertTriangle, badge: summary?.high_critical_risks_count ? `${summary.high_critical_risks_count}` : undefined },
    { name: 'Recommendations', path: '/recommendations', icon: Sparkles },
    { name: 'Reports', path: '/reports', icon: FileText },
    { name: 'Assessment History', path: '/history', icon: History },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  const userInitials = (user?.full_name || user?.email || 'RA')
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="flex h-screen bg-slate-50 text-slate-800 font-sans overflow-hidden">
      {/* Dark Navy Sidebar */}
      <aside className="w-68 bg-[#0B1528] text-slate-300 flex flex-col flex-shrink-0 z-30 shadow-xl border-r border-slate-800">
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-500 via-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-teal-500/20">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-extrabold text-white text-lg tracking-tight">RAI-Biz</span>
                <span className="text-[10px] font-semibold bg-teal-500/20 text-teal-400 px-1.5 py-0.5 rounded border border-teal-500/30">SME</span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">Responsible AI Platform</p>
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto custom-scrollbar">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all group ${
                  isActive
                    ? 'bg-gradient-to-r from-teal-600 to-sky-700 text-white font-semibold shadow-md shadow-teal-900/20'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-4 h-4 transition-colors ${isActive ? 'text-white' : 'text-slate-400 group-hover:text-teal-400'}`} />
                  <span className="truncate">{item.name}</span>
                </div>
                {item.badge && (
                  <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-rose-500 text-white shadow-sm">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* User Profile in Sidebar */}
        {user && (
          <div className="px-3 pt-2 pb-1 border-t border-slate-800/80 bg-slate-950/40">
            <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800/60">
              <div className="flex items-center space-x-2.5 min-w-0">
                <div className="w-8 h-8 rounded-lg bg-teal-500/20 text-teal-400 border border-teal-500/30 font-bold flex items-center justify-center text-xs shrink-0">
                  {userInitials}
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-slate-200 truncate">{user.email}</p>
                  <p className="text-[10px] text-teal-400 truncate">{user.role || 'Compliance Officer'}</p>
                </div>
              </div>
              <button
                onClick={handleLogout}
                title="Log out of session"
                className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 rounded-md transition"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {/* Bottom Demo Card */}
        <div className="p-3 m-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] font-semibold text-slate-300">Shared Demo Workspace</span>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          </div>
          <p className="text-[11px] text-slate-400 mb-2 leading-relaxed">
            Recruitment AI audit scenario with pre-analyzed fairness, privacy & green metrics.
          </p>
          <button
            onClick={handleSeedDemo}
            disabled={seeding}
            className="w-full flex items-center justify-center space-x-1.5 py-1.5 px-2.5 bg-slate-800 hover:bg-slate-700 text-teal-400 rounded-lg text-[11px] font-medium border border-teal-500/20 hover:border-teal-500/40 transition"
          >
            <RefreshCw className={`w-3 h-3 ${seeding ? 'animate-spin' : ''}`} />
            <span>{seeding ? 'Seeding Demo...' : 'Reload Demo Scenario'}</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header Bar */}
        <header className="h-16 bg-white border-b border-slate-200/80 px-6 flex items-center justify-between flex-shrink-0 z-20 shadow-xs">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-xs">
              <span className="font-semibold text-slate-900 text-sm">
                {summary?.business?.name || business?.name || "Enterprise Workspace"}
              </span>
              <span className="text-slate-300">•</span>
              <span className="px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 font-medium border border-sky-100 flex items-center space-x-1">
                <span>App:</span>
                <span className="font-semibold">{summary?.application?.name || application?.name || "Active AI System"}</span>
              </span>
              <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">
                {summary?.business?.industry || business?.industry || "Technology"}
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            {/* Risk Alert Pill */}
            {summary && summary.high_critical_risks_count > 0 ? (
              <NavLink
                to="/risks"
                className="flex items-center space-x-1.5 px-3 py-1.5 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg font-medium hover:bg-rose-100 transition shadow-2xs"
              >
                <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
                <span>{summary.high_critical_risks_count} Critical / High Risks</span>
              </NavLink>
            ) : (
              <span className="flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-lg font-medium">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Governance Safe</span>
              </span>
            )}

            {/* Quick Assessment Score Badge */}
            <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg">
              <span className="text-slate-500 font-medium">RAI Index:</span>
              <span className={`font-bold ${
                (summary?.overall_governance_score || 0) >= 80 ? 'text-emerald-600' :
                (summary?.overall_governance_score || 0) >= 60 ? 'text-amber-600' : 'text-rose-600'
              }`}>
                {summary?.overall_governance_score ? `${summary.overall_governance_score.toFixed(1)}/100` : 'Not Assessed'}
              </span>
            </div>

            {/* API Docs Link */}
            <a
              href={api.getDocsUrl()}
              target="_blank"
              rel="noreferrer"
              className="p-2 text-slate-500 hover:text-slate-800 rounded-lg hover:bg-slate-100 transition"
              title="Interactive FastAPI Swagger Docs"
            >
              <ExternalLink className="w-4 h-4" />
            </a>

            {/* User Email & Logout Pill */}
            {user ? (
              <div className="flex items-center space-x-2 pl-2 border-l border-slate-200">
                <div className="flex items-center space-x-2 bg-slate-50 border border-slate-200 py-1 px-2.5 rounded-lg">
                  <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-teal-600 to-sky-700 text-white font-bold flex items-center justify-center text-[10px]">
                    {userInitials}
                  </div>
                  <span className="text-slate-700 font-medium hidden md:inline truncate max-w-[140px]">
                    {user.email}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-1 py-1.5 px-2 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg border border-transparent hover:border-rose-200 transition font-medium"
                  title="Sign Out"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </div>
            ) : (
              <button
                onClick={() => navigate('/login')}
                className="py-1.5 px-3 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-medium transition"
              >
                Sign In
              </button>
            )}
          </div>
        </header>

        {/* Dynamic Route View */}
        <main className="flex-1 overflow-y-auto bg-[#f8fafc] p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

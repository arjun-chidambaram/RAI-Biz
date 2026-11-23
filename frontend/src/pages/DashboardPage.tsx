import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import {
  ShieldCheck,
  Scale,
  Eye,
  Lock,
  Leaf,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  TrendingUp,
  FileText,
  Clock,
  Layers,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Zap,
  Info
} from 'lucide-react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell
} from 'recharts';
import { api, DashboardSummary } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const DashboardPage: React.FC = () => {
  const { business: authBiz, application: authApp } = useAuth();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const data = await api.getDashboardSummary();
      setSummary(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-emerald-600 bg-emerald-50 border-emerald-200';
    if (score >= 60) return 'text-amber-600 bg-amber-50 border-amber-200';
    return 'text-rose-600 bg-rose-50 border-rose-200';
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      default:
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500 space-x-2">
        <div className="w-5 h-5 border-2 border-teal-600 border-t-transparent rounded-full animate-spin"></div>
        <span>Loading Executive Governance Dashboard...</span>
      </div>
    );
  }

  const radarData = summary?.radar_data || [
    { subject: 'Fairness', score: 0, fullMark: 100 },
    { subject: 'Transparency', score: 0, fullMark: 100 },
    { subject: 'Data Privacy', score: 0, fullMark: 100 },
    { subject: 'Green AI', score: 0, fullMark: 100 },
  ];

  const riskChartData = [
    { name: 'Critical', count: summary?.risk_distribution?.['Critical'] || 0, color: '#e11d48' },
    { name: 'High', count: summary?.risk_distribution?.['High'] || 0, color: '#f97316' },
    { name: 'Medium', count: summary?.risk_distribution?.['Medium'] || 0, color: '#f59e0b' },
    { name: 'Low', count: summary?.risk_distribution?.['Low'] || 0, color: '#10b981' },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Banner / Welcome */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 p-6 rounded-2xl text-white shadow-lg border border-slate-700/50">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-teal-500/20 text-teal-300 border border-teal-500/30">
              Responsible AI Governance
            </span>
            <span className="text-slate-400 text-xs">Self-Reported SME Evaluation</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">
            {summary?.business?.name || authBiz?.name || "Enterprise Workspace"} AI Risk & Governance Center
          </h1>
          <p className="text-slate-300 text-xs mt-1 max-w-2xl leading-relaxed">
            Continuous auditing for <b>{summary?.application?.name || authApp?.name || "Active AI System"}</b> across algorithmic fairness, explainability, PII privacy protection, and carbon sustainability.
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-shrink-0">
          <NavLink
            to="/assessment"
            className="px-4 py-2 bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-600 hover:to-teal-700 text-white rounded-xl text-xs font-semibold shadow-md shadow-teal-900/30 transition flex items-center space-x-1.5"
          >
            <span>Take Governance Audit</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </NavLink>
          <NavLink
            to="/reports"
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-medium border border-slate-700 transition flex items-center space-x-1.5"
          >
            <FileText className="w-3.5 h-3.5 text-teal-400" />
            <span>Executive PDF</span>
          </NavLink>
        </div>
      </div>

      {/* Governance Dimension Score Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {/* Overall Index Card */}
        <div className="col-span-2 md:col-span-1 bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
            <span className="font-medium">RAI Governance Index</span>
            <ShieldCheck className="w-4 h-4 text-teal-600" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-slate-900">
              {summary?.overall_governance_score?.toFixed(1) || '0.0'}
            </span>
            <span className="text-xs text-slate-400 font-semibold">/ 100</span>
          </div>
          <div className="mt-3">
            <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${getScoreColor(summary?.overall_governance_score || 0)}`}>
              {(summary?.overall_governance_score || 0) >= 80 ? 'Compliant' : (summary?.overall_governance_score || 0) >= 60 ? 'Moderate Risk' : 'High Deficiencies'}
            </span>
          </div>
        </div>

        {/* Fairness Score Card */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
            <span className="font-medium">Fairness & Equity</span>
            <Scale className="w-4 h-4 text-sky-600" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-slate-900">
              {summary?.fairness_score?.toFixed(1) || '0.0'}
            </span>
            <span className="text-xs text-slate-400 font-semibold">/ 100</span>
          </div>
          <div className="mt-3">
            <NavLink to="/fairness" className="text-[11px] font-medium text-sky-600 hover:text-sky-800 flex items-center space-x-1">
              <span>Inspect Bias</span>
              <ArrowRight className="w-3 h-3" />
            </NavLink>
          </div>
        </div>

        {/* Transparency Score Card */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
            <span className="font-medium">Explainability</span>
            <Eye className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-slate-900">
              {summary?.transparency_score?.toFixed(1) || '0.0'}
            </span>
            <span className="text-xs text-slate-400 font-semibold">/ 100</span>
          </div>
          <div className="mt-3">
            <NavLink to="/xai" className="text-[11px] font-medium text-indigo-600 hover:text-indigo-800 flex items-center space-x-1">
              <span>View SHAP</span>
              <ArrowRight className="w-3 h-3" />
            </NavLink>
          </div>
        </div>

        {/* Privacy Score Card */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
            <span className="font-medium">Data Privacy</span>
            <Lock className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-slate-900">
              {summary?.privacy_score?.toFixed(1) || '0.0'}
            </span>
            <span className="text-xs text-slate-400 font-semibold">/ 100</span>
          </div>
          <div className="mt-3">
            <NavLink to="/privacy" className="text-[11px] font-medium text-emerald-600 hover:text-emerald-800 flex items-center space-x-1">
              <span>Scan PII</span>
              <ArrowRight className="w-3 h-3" />
            </NavLink>
          </div>
        </div>

        {/* Green AI Score Card */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
            <span className="font-medium">Green AI & Carbon</span>
            <Leaf className="w-4 h-4 text-teal-600" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-slate-900">
              {summary?.sustainability_score?.toFixed(1) || '0.0'}
            </span>
            <span className="text-xs text-slate-400 font-semibold">/ 100</span>
          </div>
          <div className="mt-3">
            <NavLink to="/green-ai" className="text-[11px] font-medium text-teal-600 hover:text-teal-800 flex items-center space-x-1">
              <span>Track CO2e</span>
              <ArrowRight className="w-3 h-3" />
            </NavLink>
          </div>
        </div>
      </div>

      {/* Main Analytics Grid: Radar Chart + Risk Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Radar Chart (2 Cols) */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Responsible AI Multi-Dimensional Radar</h2>
              <p className="text-xs text-slate-500">Evaluation across the 4 core governance pillars (Target: 80+ across each)</p>
            </div>
            <span className="text-xs px-2.5 py-1 rounded-md bg-slate-100 text-slate-600 font-medium">
              4 Categories / 20 Criteria
            </span>
          </div>

          <div className="h-68 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#475569', fontSize: 11, fontWeight: 600 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#cbd5e1" />
                <Radar name="Current Score" dataKey="score" stroke="#0d9488" fill="#14b8a6" fillOpacity={0.4} />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-4 gap-2 pt-4 border-t border-slate-100 text-center text-xs">
            {radarData.map((d) => (
              <div key={d.subject} className="p-2 rounded-lg bg-slate-50">
                <span className="block text-slate-500 text-[11px] truncate">{d.subject}</span>
                <span className={`font-bold text-sm ${d.score >= 80 ? 'text-emerald-600' : d.score >= 60 ? 'text-amber-600' : 'text-rose-600'}`}>
                  {d.score.toFixed(1)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Distribution & Quick Stats (1 Col) */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-bold text-slate-900">Risk Severity Distribution</h2>
              <NavLink to="/risks" className="text-xs font-semibold text-teal-600 hover:text-teal-800 flex items-center space-x-1">
                <span>View All ({summary?.total_risks_count || 0})</span>
                <ArrowRight className="w-3 h-3" />
              </NavLink>
            </div>

            <p className="text-xs text-slate-500 mb-4">
              Open vulnerabilities gathered automatically from Assessment, Bias, Privacy, and Green AI modules.
            </p>

            {/* Severity Bars */}
            <div className="space-y-3">
              {riskChartData.map((item) => (
                <div key={item.name} className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2 w-24">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }}></span>
                    <span className="font-medium text-slate-700">{item.name}</span>
                  </div>
                  <div className="flex-1 mx-3 h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        backgroundColor: item.color,
                        width: `${Math.min(100, item.count * 25)}%`
                      }}
                    ></div>
                  </div>
                  <span className="font-bold text-slate-900 w-6 text-right">{item.count}</span>
                </div>
              ))}
            </div>

            {/* Quick KPI stats */}
            <div className="mt-6 pt-4 border-t border-slate-100 grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-rose-50/70 border border-rose-100">
                <span className="text-rose-600 font-medium block">High/Critical</span>
                <span className="text-xl font-bold text-rose-800">{summary?.high_critical_risks_count || 0}</span>
              </div>
              <div className="p-3 rounded-xl bg-emerald-50/70 border border-emerald-100">
                <span className="text-emerald-600 font-medium block">Resolved</span>
                <span className="text-xl font-bold text-emerald-800">{summary?.resolved_risks_count || 0}</span>
              </div>
            </div>
          </div>

          <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-start space-x-2">
            <Info className="w-4 h-4 text-teal-600 flex-shrink-0 mt-0.5" />
            <p className="text-[11px] leading-relaxed">
              Target zero Open Critical risks prior to expanding automated AI service decisioning.
            </p>
          </div>
        </div>
      </div>

      {/* Critical Alerts & Recommended SME Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active High-Risk Alerts */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              <h2 className="text-sm font-bold text-slate-900">Active High-Priority Alerts</h2>
            </div>
            <NavLink to="/risks" className="text-xs text-teal-600 hover:text-teal-800 font-semibold">
              Manage in Risk Center
            </NavLink>
          </div>

          <div className="space-y-3">
            {summary?.recent_alerts && summary.recent_alerts.length > 0 ? (
              summary.recent_alerts.map((alert) => (
                <div key={alert.id} className="p-3 rounded-xl border border-slate-200/80 hover:border-slate-300 transition bg-slate-50/50">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getSeverityBadge(alert.severity)}`}>
                      {alert.severity.toUpperCase()}
                    </span>
                    <span className="text-[10px] text-slate-400 capitalize">Module: {alert.module}</span>
                  </div>
                  <h3 className="text-xs font-bold text-slate-900">{alert.title}</h3>
                  <p className="text-[11px] text-slate-600 mt-1 line-clamp-2 leading-relaxed">
                    {alert.impact}
                  </p>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-slate-400 text-xs">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
                <span>No open critical alerts registered.</span>
              </div>
            )}
          </div>
        </div>

        {/* Priority AI Recommendations */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-teal-600" />
              <h2 className="text-sm font-bold text-slate-900">Priority Governance Action Plan</h2>
            </div>
            <NavLink to="/recommendations" className="text-xs text-teal-600 hover:text-teal-800 font-semibold">
              Full Plan
            </NavLink>
          </div>

          <div className="space-y-3">
            {summary?.top_recommendations && summary.top_recommendations.length > 0 ? (
              summary.top_recommendations.slice(0, 3).map((rec) => (
                <div key={rec.id} className="p-3 rounded-xl border border-slate-200/80 hover:border-teal-200 transition bg-slate-50/50">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-sky-100 text-sky-800">
                      Team: {rec.responsible_team}
                    </span>
                    <span className="text-[10px] font-semibold text-rose-600">
                      Priority: {rec.priority}
                    </span>
                  </div>
                  <h3 className="text-xs font-bold text-slate-900">{rec.problem}</h3>
                  <p className="text-[11px] text-slate-600 mt-1 line-clamp-2 leading-relaxed">
                    {rec.action}
                  </p>
                  <div className="mt-2 text-[10px] text-teal-700 font-medium">
                    Benefit: {rec.expected_business_benefit}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-slate-400 text-xs">
                <span>Complete assessment to generate targeted action items.</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Legal & Self-Reported Governance Notice */}
      <div className="p-4 rounded-xl bg-slate-100/80 border border-slate-200 text-slate-500 text-[11px] leading-relaxed flex items-start space-x-3">
        <Info className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
        <div>
          <b>Self-Reported Governance Assessment Notice:</b> Scores and metrics generated within RAI-Biz reflect SME self-reported questionnaire responses, statistical bias evaluations, and preliminary heuristic scans. They do not constitute statutory audit certifications, legal liability shields, or formal conformity assessments under regulatory frameworks such as the EU AI Act or ISO/IEC 42001.
        </div>
      </div>
    </div>
  );
};

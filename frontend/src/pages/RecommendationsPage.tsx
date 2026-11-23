import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  CheckCircle2,
  Clock,
  Filter,
  Users,
  Building,
  ShieldAlert,
  ArrowRight,
  TrendingUp,
  RefreshCw,
  Cpu,
  Scale,
  Briefcase
} from 'lucide-react';
import { api, RecommendationItem } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const RecommendationsPage: React.FC = () => {
  const { application } = useAuth();
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedTeam, setSelectedTeam] = useState<string>('all');
  const [selectedPriority, setSelectedPriority] = useState<string>('all');

  useEffect(() => {
    loadRecommendations();
  }, [application?.id]);

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      const targetAppId = application?.id || 1;
      const data = await api.getRecommendations(targetAppId);
      setRecommendations(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      const targetAppId = application?.id || 1;
      const data = await api.generateRecommendations(targetAppId);
      setRecommendations(data);
    } catch (err) {
      alert("Failed to generate recommendations");
    } finally {
      setGenerating(false);
    }
  };

  const getPriorityBadge = (pri: string) => {
    switch (pri.toLowerCase()) {
      case 'high':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'medium':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      default:
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
    }
  };

  const getTeamIcon = (team: string) => {
    switch (team.toLowerCase()) {
      case 'engineering':
        return Cpu;
      case 'legal & compliance':
        return Scale;
      case 'hr & operations':
        return Users;
      default:
        return Briefcase;
    }
  };

  const filtered = recommendations.filter((r) => {
    if (selectedTeam !== 'all' && r.responsible_team !== selectedTeam) return false;
    if (selectedPriority !== 'all' && r.priority !== selectedPriority) return false;
    return true;
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-50 text-teal-700 border border-teal-200">
                MODULE 8
              </span>
              <span className="text-xs text-slate-400 font-medium">Deterministic Heuristics & Optional Gemini API</span>
            </div>
            <h1 className="text-xl font-bold text-slate-900">AI Recommendation Engine</h1>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
              Prioritized, cross-functional remediation roadmap translating governance deficiencies into measurable commercial and risk-reduction outcomes.
            </p>
          </div>

          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-4 py-2.5 bg-gradient-to-r from-teal-600 to-sky-700 hover:from-teal-700 hover:to-sky-800 text-white rounded-xl text-xs font-bold transition flex items-center space-x-1.5 shadow-md shadow-teal-900/20"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${generating ? 'animate-spin' : ''}`} />
            <span>{generating ? 'Synthesizing...' : 'Re-Generate Recommendations'}</span>
          </button>
        </div>

        {/* Filter Bar */}
        <div className="mt-5 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <span className="text-slate-400 font-medium">Responsible Team:</span>
              <select
                value={selectedTeam}
                onChange={(e) => setSelectedTeam(e.target.value)}
                className="px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50 text-xs font-semibold"
              >
                <option value="all">All Teams</option>
                <option value="Engineering">Engineering</option>
                <option value="Legal & Compliance">Legal & Compliance</option>
                <option value="HR & Operations">HR & Operations</option>
                <option value="Executive Leadership">Executive Leadership</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-slate-400 font-medium">Priority:</span>
              <select
                value={selectedPriority}
                onChange={(e) => setSelectedPriority(e.target.value)}
                className="px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50 text-xs font-semibold"
              >
                <option value="all">All Priorities</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>
          </div>

          <span className="text-slate-400 font-medium">
            {filtered.length} Action Items
          </span>
        </div>
      </div>

      {/* Recommendations Cards */}
      <div className="space-y-4">
        {loading ? (
          <div className="py-12 text-center text-slate-400 text-xs">
            Loading recommendations...
          </div>
        ) : filtered.length > 0 ? (
          filtered.map((rec) => {
            const TeamIcon = getTeamIcon(rec.responsible_team);

            return (
              <div
                key={rec.id}
                className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs hover:border-slate-300 transition space-y-3.5"
              >
                {/* Header Strip */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold border ${getPriorityBadge(rec.priority)}`}>
                      {rec.priority.toUpperCase()} PRIORITY
                    </span>
                    <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-sky-50 text-sky-800 border border-sky-200 flex items-center space-x-1">
                      <TeamIcon className="w-3 h-3 text-sky-600" />
                      <span>{rec.responsible_team}</span>
                    </span>
                    <span className="text-[10px] text-slate-400 capitalize">
                      Module: {rec.source_module}
                    </span>
                  </div>

                  <span className="text-[10px] text-slate-400">
                    Created {new Date(rec.created_at).toLocaleDateString()}
                  </span>
                </div>

                {/* Problem & Action */}
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{rec.problem}</h3>
                  <div className="mt-1 text-xs text-slate-600 leading-relaxed">
                    <span className="font-semibold text-slate-800">Why It Matters: </span>
                    {rec.why_it_matters}
                  </div>
                </div>

                {/* Concrete Action Card */}
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-800 space-y-1">
                  <span className="text-[10px] font-bold text-teal-700 uppercase tracking-wider block">
                    Targeted Action Plan
                  </span>
                  <p className="font-medium leading-relaxed">
                    {rec.action}
                  </p>
                </div>

                {/* Expected Business Benefit */}
                <div className="p-3 rounded-xl bg-emerald-50/70 border border-emerald-200/80 text-xs flex items-start space-x-2">
                  <TrendingUp className="w-4 h-4 text-emerald-700 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-emerald-900">Expected Business Benefit: </span>
                    <span className="text-emerald-800">{rec.expected_business_benefit}</span>
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center py-12 bg-white rounded-2xl border border-slate-200/80 text-slate-400 text-xs">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
            <span>No recommendations match filter criteria.</span>
          </div>
        )}
      </div>
    </div>
  );
};

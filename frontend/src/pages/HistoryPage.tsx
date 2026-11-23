import React, { useState, useEffect } from 'react';
import {
  History,
  Calendar,
  ShieldCheck,
  Download,
  Eye,
  CheckCircle2,
  TrendingUp,
  FileText
} from 'lucide-react';
import { api, AssessmentResult } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const HistoryPage: React.FC = () => {
  const { application } = useAuth();
  const [assessments, setAssessments] = useState<AssessmentResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAssessment, setSelectedAssessment] = useState<AssessmentResult | null>(null);

  useEffect(() => {
    loadHistory();
  }, [application?.id]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const targetAppId = application?.id || 1;
      const data = await api.getAssessments(targetAppId);
      setAssessments(data);
      if (data.length > 0) {
        // Fetch detailed version of first assessment
        const detailed = await api.getAssessment(data[0].id);
        setSelectedAssessment(detailed);
      } else {
        setSelectedAssessment(null);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = async (id: number) => {
    try {
      const detailed = await api.getAssessment(id);
      setSelectedAssessment(detailed);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDownload = (id: number) => {
    const url = api.getPdfReportUrl(id);
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                AUDIT HISTORY
              </span>
              <span className="text-xs text-slate-400 font-medium">Temporal Governance Score Tracking</span>
            </div>
            <h1 className="text-xl font-bold text-slate-900">Governance Assessment History</h1>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
              Immutable timeline of historical self-assessments, score trajectories, and archived regulatory disclosure snapshots.
            </p>
          </div>

          <span className="text-xs font-semibold px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-700">
            {assessments.length} Completed Audits
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline Table (1 Col) */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-3">
          <h2 className="text-sm font-bold text-slate-900 mb-2">Historical Audit Runs</h2>

          {loading ? (
            <div className="text-center py-8 text-slate-400 text-xs">
              Loading timeline...
            </div>
          ) : assessments.length > 0 ? (
            <div className="space-y-2.5">
              {assessments.map((a) => {
                const isSelected = selectedAssessment?.id === a.id;
                return (
                  <div
                    key={a.id}
                    onClick={() => handleSelect(a.id)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition ${
                      isSelected
                        ? 'border-teal-600 bg-teal-50/40 shadow-xs'
                        : 'border-slate-200/80 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-bold text-slate-900 truncate">
                        {a.name}
                      </span>
                      <span className={`text-xs font-extrabold px-2 py-0.5 rounded ${
                        a.overall_score >= 80 ? 'bg-emerald-100 text-emerald-800' :
                        a.overall_score >= 60 ? 'bg-amber-100 text-amber-800' : 'bg-rose-100 text-rose-800'
                      }`}>
                        {a.overall_score.toFixed(1)}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                      <span className="flex items-center space-x-1">
                        <Calendar className="w-3 h-3" />
                        <span>{new Date(a.completed_at).toLocaleDateString()}</span>
                      </span>
                      <span className="text-teal-700 font-medium">View Detail →</span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-400 text-xs">
              No historical assessments found.
            </div>
          )}
        </div>

        {/* Detailed Breakdown Card (2 Cols) */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-6">
          {selectedAssessment ? (
            <>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
                <div>
                  <span className="text-[10px] font-bold text-teal-600 uppercase tracking-wider block">
                    Audit Run Snapshot #{selectedAssessment.id}
                  </span>
                  <h3 className="text-base font-bold text-slate-900">
                    {selectedAssessment.name}
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    Completed on {new Date(selectedAssessment.completed_at).toLocaleString()}
                  </p>
                </div>

                <button
                  onClick={() => handleDownload(selectedAssessment.id)}
                  className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-bold transition flex items-center space-x-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download PDF</span>
                </button>
              </div>

              {/* 4 Dimension Scorecards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center text-xs">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-slate-500 block text-[10px]">Fairness</span>
                  <span className="text-lg font-bold text-sky-700">
                    {selectedAssessment.fairness_score.toFixed(1)}/100
                  </span>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-slate-500 block text-[10px]">Transparency</span>
                  <span className="text-lg font-bold text-indigo-700">
                    {selectedAssessment.transparency_score.toFixed(1)}/100
                  </span>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-slate-500 block text-[10px]">Data Privacy</span>
                  <span className="text-lg font-bold text-emerald-700">
                    {selectedAssessment.privacy_score.toFixed(1)}/100
                  </span>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-slate-500 block text-[10px]">Green AI</span>
                  <span className="text-lg font-bold text-teal-700">
                    {selectedAssessment.sustainability_score.toFixed(1)}/100
                  </span>
                </div>
              </div>

              {/* Individual Question Responses Table */}
              <div>
                <h4 className="text-xs font-bold text-slate-800 mb-2">Itemized Question Audit Log (20 Responses)</h4>
                {selectedAssessment.responses && selectedAssessment.responses.length > 0 ? (
                  <div className="overflow-x-auto max-h-80 border border-slate-200 rounded-xl">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] sticky top-0">
                        <tr>
                          <th className="px-3 py-2">ID</th>
                          <th className="px-3 py-2">Question / Standard</th>
                          <th className="px-3 py-2 text-center">Answer</th>
                          <th className="px-3 py-2">Audit Notes</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 text-[11px]">
                        {selectedAssessment.responses.map((r) => (
                          <tr key={r.question_id} className="hover:bg-slate-50/60">
                            <td className="px-3 py-2 font-bold font-mono text-slate-700">{r.question_id}</td>
                            <td className="px-3 py-2 text-slate-800 font-medium max-w-sm">{r.question_text}</td>
                            <td className="px-3 py-2 text-center">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                r.answer === 'Yes' ? 'bg-emerald-100 text-emerald-800' :
                                r.answer === 'Partially' ? 'bg-amber-100 text-amber-800' :
                                r.answer === 'No' ? 'bg-rose-100 text-rose-800' : 'bg-slate-100 text-slate-700'
                              }`}>
                                {r.answer}
                              </span>
                            </td>
                            <td className="px-3 py-2 text-slate-500 italic max-w-xs truncate">
                              {r.notes || '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-xs text-slate-400">Detailed responses not available for this run.</div>
                )}
              </div>
            </>
          ) : (
            <div className="text-center py-16 text-slate-400 text-xs">
              Select an audit from the left to inspect detailed snapshot.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

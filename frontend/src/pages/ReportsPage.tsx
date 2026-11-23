import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  CheckCircle2,
  AlertTriangle,
  Building2,
  ShieldCheck,
  Scale,
  Eye,
  Lock,
  Leaf,
  Info,
  Clock,
  Printer
} from 'lucide-react';
import { api, AssessmentResult } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const ReportsPage: React.FC = () => {
  const { business, application } = useAuth();
  const [assessments, setAssessments] = useState<AssessmentResult[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAssessments();
  }, [application?.id]);

  const loadAssessments = async () => {
    try {
      setLoading(true);
      const data = await api.getAssessments(application?.id);
      setAssessments(data);
      if (data.length > 0) {
        setSelectedId(data[0].id);
      } else {
        setSelectedId(null);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const selectedAssessment = assessments.find((a) => a.id === selectedId);

  const handleDownload = () => {
    if (!selectedId) return;
    const url = api.getPdfReportUrl(selectedId);
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-50 text-teal-700 border border-teal-200">
                MODULE 9
              </span>
              <span className="text-xs text-slate-400 font-medium">ReportLab Document Engine • Multi-Section Audit</span>
            </div>
            <h1 className="text-xl font-bold text-slate-900">Executive Responsible AI PDF Reports</h1>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
              Export comprehensive, publication-grade governance reports suitable for enterprise clients, insurance underwriters, and internal compliance boards.
            </p>
          </div>

          <button
            onClick={handleDownload}
            disabled={!selectedId}
            className="px-5 py-2.5 bg-gradient-to-r from-teal-600 to-sky-700 hover:from-teal-700 hover:to-sky-800 text-white rounded-xl text-xs font-bold transition flex items-center space-x-2 shadow-md shadow-teal-900/20"
          >
            <Download className="w-4 h-4" />
            <span>Download Executive PDF Report</span>
          </button>
        </div>

        {/* Assessment Run Selector */}
        {assessments.length > 1 && (
          <div className="mt-4 pt-4 border-t border-slate-100 flex items-center space-x-3 text-xs">
            <span className="text-slate-500 font-medium">Select Audit Run:</span>
            <select
              value={selectedId || ''}
              onChange={(e) => setSelectedId(Number(e.target.value))}
              className="px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 font-semibold"
            >
              {assessments.map((a) => (
                <option key={a.id} value={a.id}>
                  Audit #{a.id} • {new Date(a.completed_at).toLocaleDateString()} (Score: {a.overall_score.toFixed(1)})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Report Preview Document Card */}
      {selectedAssessment ? (
        <div className="bg-white p-8 rounded-2xl border border-slate-200/90 shadow-sm space-y-6">
          {/* Document Header Preview */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b-2 border-teal-600 gap-4">
            <div>
              <span className="text-xs font-bold text-teal-700 uppercase tracking-widest block">
                Official Governance Documentation
              </span>
              <h2 className="text-2xl font-black text-slate-900 tracking-tight">
                RAI-Biz Governance Audit Report
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Target System: <b>{application?.name || "Active AI System"}</b> • Audit ID #{selectedAssessment.id}
              </p>
            </div>

            <div className="text-right text-xs text-slate-500 space-y-0.5">
              <div><b>Generated:</b> {new Date().toLocaleDateString()}</div>
              <div><b>Methodology:</b> RAI-Biz Universal Governance Engine v2.0</div>
              <div><b>Status:</b> Completed Self-Assessment</div>
            </div>
          </div>

          {/* Report Sections Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
            {/* Section 1 & 2 */}
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                <h3 className="font-bold text-slate-900 mb-2 flex items-center space-x-1.5">
                  <Building2 className="w-4 h-4 text-slate-600" />
                  <span>1. SME Profile & Target AI Application</span>
                </h3>
                <ul className="space-y-1 text-slate-600">
                  <li>• Organization: {business?.name || "Enterprise Workspace"} ({business?.size || "Not Provided"} employees)</li>
                  <li>• Function: {application?.business_function || "Operational AI Processing"}</li>
                  <li>• Decision Impact: {application?.automated_decision_impact || "Medium"}</li>
                  <li>• Human Oversight: {application?.human_oversight || "Human-in-the-loop"}</li>
                </ul>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                <h3 className="font-bold text-slate-900 mb-2 flex items-center space-x-1.5">
                  <ShieldCheck className="w-4 h-4 text-teal-600" />
                  <span>2. Executive Responsible AI Scorecard</span>
                </h3>
                <div className="grid grid-cols-2 gap-2 text-center pt-1">
                  <div className="p-2 bg-white rounded-lg border border-slate-200">
                    <span className="text-slate-400 text-[10px] block">Overall Index</span>
                    <span className="text-base font-extrabold text-slate-900">
                      {selectedAssessment.overall_score.toFixed(1)}/100
                    </span>
                  </div>
                  <div className="p-2 bg-white rounded-lg border border-slate-200">
                    <span className="text-slate-400 text-[10px] block">Fairness</span>
                    <span className="text-base font-bold text-sky-700">
                      {selectedAssessment.fairness_score.toFixed(1)}/100
                    </span>
                  </div>
                  <div className="p-2 bg-white rounded-lg border border-slate-200">
                    <span className="text-slate-400 text-[10px] block">Transparency</span>
                    <span className="text-base font-bold text-indigo-700">
                      {selectedAssessment.transparency_score.toFixed(1)}/100
                    </span>
                  </div>
                  <div className="p-2 bg-white rounded-lg border border-slate-200">
                    <span className="text-slate-400 text-[10px] block">Privacy & Green</span>
                    <span className="text-base font-bold text-emerald-700">
                      {selectedAssessment.privacy_score.toFixed(1)} / {selectedAssessment.sustainability_score.toFixed(1)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Section 3 & 4 */}
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                <h3 className="font-bold text-slate-900 mb-2 flex items-center space-x-1.5">
                  <Scale className="w-4 h-4 text-sky-600" />
                  <span>3. Deep Technical Findings</span>
                </h3>
                <ul className="space-y-1.5 text-slate-600">
                  <li>• <b>Fairness:</b> Demographic parity ratio evaluated against EEOC 80% threshold.</li>
                  <li>• <b>Explainability:</b> Game-theoretic SHAP feature attributions mapped.</li>
                  <li>• <b>Privacy:</b> Heuristic regex screening for SSNs, phone numbers, and emails.</li>
                  <li>• <b>Green AI:</b> Carbon emissions modeled against regional grid factors.</li>
                </ul>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                <h3 className="font-bold text-slate-900 mb-2 flex items-center space-x-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  <span>4. Risk Ledger & Actionable Roadmap</span>
                </h3>
                <p className="text-slate-600 leading-relaxed">
                  Includes full open risk ledger with empirical evidence quotes, assigned mitigation teams (Engineering, Compliance, HR), and prioritized remediation timelines.
                </p>
              </div>
            </div>
          </div>

          {/* Legal Limitations Notice */}
          <div className="pt-4 border-t border-slate-200 text-[11px] text-slate-400 leading-relaxed italic">
            <b>Statutory Audit Notice:</b> {selectedAssessment.disclaimer}
          </div>
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-2xl border border-slate-200/80 text-slate-400 text-xs">
          No assessment records found. Take an assessment to unlock PDF reporting.
        </div>
      )}
    </div>
  );
};

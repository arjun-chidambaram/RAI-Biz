import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Lock,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  FileSearch,
  Info,
  ShieldAlert,
  Database,
  Trash2,
  FileText
} from 'lucide-react';
import { api, Dataset, PrivacyScanResponse } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const PrivacyGuardPage: React.FC = () => {
  const { application } = useAuth();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null);
  const [scanning, setScanning] = useState(false);
  const [results, setResults] = useState<PrivacyScanResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInitialData();
  }, [application?.id]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const dsList = await api.getDatasets(application?.id);
      setDatasets(dsList);
      if (dsList.length > 0) {
        setSelectedDatasetId(dsList[0].id);
        runScan(dsList[0].id);
      } else {
        setSelectedDatasetId(null);
        setResults(null);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const runScan = async (dsId?: number) => {
    const idToUse = dsId || selectedDatasetId;
    if (!idToUse) return;

    try {
      setScanning(true);
      const res = await api.scanPrivacy({
        application_id: application?.id || 1,
        dataset_id: idToUse
      });
      setResults(res);
    } catch (err: any) {
      alert("Error scanning privacy: " + (err.message || "Failed"));
    } finally {
      setScanning(false);
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'medium':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      default:
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                MODULE 4
              </span>
              <span className="text-xs text-slate-400 font-medium">PII Heuristic Screening • Data Minimization</span>
            </div>
            <h1 className="text-xl font-bold text-slate-900">Data Privacy & PII Governance Guard</h1>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
              Automated screening for unmasked personal identifiers (emails, phone numbers, SSNs), duplicate records, and data minimization policy violations.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            {datasets.length > 0 && (
              <>
                <span className="text-xs text-slate-500 font-medium">Target Dataset:</span>
                <select
                  value={selectedDatasetId || ''}
                  onChange={(e) => {
                    const id = Number(e.target.value);
                    setSelectedDatasetId(id);
                    runScan(id);
                  }}
                  className="text-xs px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 focus:outline-hidden font-medium"
                >
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.original_filename} ({d.row_count} rows)
                    </option>
                  ))}
                </select>
              </>
            )}

            <button
              onClick={() => runScan()}
              disabled={scanning || datasets.length === 0}
              className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-700 hover:from-emerald-700 hover:to-teal-800 text-white rounded-xl text-xs font-bold transition flex items-center space-x-1.5 shadow-xs disabled:opacity-50"
            >
              <FileSearch className={`w-3.5 h-3.5 ${scanning ? 'animate-spin' : ''}`} />
              <span>{scanning ? 'Scanning...' : 'Re-Scan Dataset'}</span>
            </button>
          </div>
        </div>

        {/* Security & Confidentiality Notice */}
        <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-600 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Lock className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span className="text-[11px]">
              <b>Zero-External-Transmission Guarantee:</b> Uploaded dataset rows are scanned locally. Raw sensitive values are masked in memory and NEVER transmitted to third-party LLM APIs.
            </span>
          </div>
          <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-bold">
            Air-Gapped Privacy
          </span>
        </div>
      </div>

      {datasets.length === 0 && !loading && (
        <div className="bg-amber-50/70 border border-amber-200/80 rounded-2xl p-6 text-amber-900 flex items-start space-x-3">
          <Info className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="text-sm font-semibold">No Dataset Ingested for {application?.name || 'this Application'}</div>
            <p className="text-xs text-amber-800 leading-relaxed">
              PII scanning and heuristic privacy screening require an ingested tabular dataset. Please visit the{' '}
              <a href="/datasets" className="font-semibold underline hover:text-amber-950">
                Dataset Manager
              </a>{' '}
              to upload your business operational data.
            </p>
          </div>
        </div>
      )}

      {results && (
        <>
          {/* Key Privacy KPIs */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
              <span className="text-[11px] font-semibold text-slate-500 block">Total Records Screened</span>
              <span className="text-2xl font-extrabold text-slate-900 mt-1 block">
                {results.total_records_scanned}
              </span>
              <p className="text-[11px] text-slate-400 mt-0.5">Rows inspected for PII patterns</p>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
              <span className="text-[11px] font-semibold text-slate-500 block">Unmasked PII Detections</span>
              <span className={`text-2xl font-extrabold mt-1 block ${results.pii_detected_count > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                {results.pii_detected_count} matches
              </span>
              <p className="text-[11px] text-slate-400 mt-0.5">{results.findings.length} sensitive columns flagged</p>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
              <span className="text-[11px] font-semibold text-slate-500 block">Data Hygiene & Duplicates</span>
              <span className={`text-2xl font-extrabold mt-1 block ${results.duplicate_rows > 0 ? 'text-amber-600' : 'text-slate-900'}`}>
                {results.duplicate_rows} duplicate rows
              </span>
              <p className="text-[11px] text-slate-400 mt-0.5">Data deduplication status</p>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
              <span className="text-[11px] font-semibold text-slate-500 block">Privacy Risk Tier</span>
              <span className={`text-xl font-extrabold mt-1 inline-block px-3 py-1 rounded-lg border ${getSeverityBadge(results.risk_level)}`}>
                {results.risk_level.toUpperCase()}
              </span>
              <p className="text-[11px] text-slate-400 mt-2">Added to Risk Center</p>
            </div>
          </div>

          {/* Detected Sensitive Patterns Table */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-sm font-bold text-slate-900">Detected Personal Identifiers (PII)</h2>
                <p className="text-xs text-slate-500">Heuristic pattern matches across dataset columns (values masked for privacy)</p>
              </div>
              <span className="text-xs px-2.5 py-1 rounded-md bg-rose-50 text-rose-700 font-bold border border-rose-200">
                {results.findings.length} Flagged Columns
              </span>
            </div>

            {results.findings.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-500 uppercase text-[10px]">
                      <th className="py-2.5 font-bold">Target Column</th>
                      <th className="py-2.5 font-bold">PII Classification</th>
                      <th className="py-2.5 font-bold">Severity</th>
                      <th className="py-2.5 font-bold text-center">Matches</th>
                      <th className="py-2.5 font-bold">Sanitized / Masked Preview</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {results.findings.map((f, i) => (
                      <tr key={i} className="hover:bg-slate-50/80">
                        <td className="py-3 font-bold text-slate-800 font-mono text-xs">{f.column}</td>
                        <td className="py-3 text-slate-700 font-semibold">{f.pii_type}</td>
                        <td className="py-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getSeverityBadge(f.risk_severity)}`}>
                            {f.risk_severity.toUpperCase()}
                          </span>
                        </td>
                        <td className="py-3 text-center font-bold text-slate-900">{f.match_count}</td>
                        <td className="py-3 font-mono text-slate-600 bg-slate-50 px-2 rounded">
                          {f.sample_masked}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-400 text-xs">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
                <span>No direct PII patterns detected in screened rows.</span>
              </div>
            )}
          </div>

          {/* Data Minimization Alerts & Governance Checklist */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Data Minimization Alerts */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
              <h2 className="text-sm font-bold text-slate-900 mb-1 flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>Data Minimization & Policy Alerts</span>
              </h2>
              <p className="text-xs text-slate-500 mb-4">Unnecessary high-cardinality attributes or sensitive tokens</p>

              <div className="space-y-2.5">
                {results.data_minimization_alerts.length > 0 ? (
                  results.data_minimization_alerts.map((alert, i) => (
                    <div key={i} className="p-3 rounded-xl bg-amber-50/60 border border-amber-200/70 text-xs text-amber-900">
                      {alert}
                    </div>
                  ))
                ) : (
                  <div className="text-center py-6 text-slate-400 text-xs">
                    No data minimization violations detected.
                  </div>
                )}
              </div>
            </div>

            {/* Governance Checklist Status */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
              <h2 className="text-sm font-bold text-slate-900 mb-1 flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Privacy Hygiene Checklist</span>
              </h2>
              <p className="text-xs text-slate-500 mb-4">Pipeline data protection status</p>

              <div className="space-y-3 text-xs">
                {Object.entries(results.governance_checklist_status).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200/70">
                    <span className="font-semibold text-slate-800">{k}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      v.toLowerCase().includes('clean') || v.toLowerCase().includes('complete') || v.toLowerCase().includes('compliant')
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-rose-100 text-rose-800'
                    }`}>
                      {v}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Legal Audit Disclaimer */}
          <div className="p-4 rounded-xl bg-slate-100/80 border border-slate-200 text-slate-500 text-[11px] leading-relaxed flex items-start space-x-3">
            <Info className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
            <div>
              <b>Preliminary Screening Disclaimer:</b> {results.disclaimer}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

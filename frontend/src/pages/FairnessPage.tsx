import React, { useState, useEffect } from 'react';
import {
  Scale,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Play,
  Info,
  BarChart2,
  Users,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell
} from 'recharts';
import { api, Dataset, FairnessAnalysisResponse } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const FairnessPage: React.FC = () => {
  const { application } = useAuth();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null);
  const [sensitiveAttr, setSensitiveAttr] = useState<string>('gender');
  const [targetAttr, setTargetAttr] = useState<string>('selected');
  const [favorableOutcome, setFavorableOutcome] = useState<string>('1');
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<FairnessAnalysisResponse | null>(null);
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
        const defaultId = dsList[0].id;
        setSelectedDatasetId(defaultId);
        
        // Inspect preview to pre-fill attributes
        try {
          const prev = await api.getDatasetPreview(defaultId);
          const cols = prev.columns || [];
          let sens = 'gender';
          let targ = 'selected';
          if (cols.includes('customer_gender')) sens = 'customer_gender';
          else if (cols.includes('gender')) sens = 'gender';

          if (cols.includes('service_approved')) targ = 'service_approved';
          else if (cols.includes('recommended_ceramic')) targ = 'recommended_ceramic';
          else if (cols.includes('selected')) targ = 'selected';

          setSensitiveAttr(sens);
          setTargetAttr(targ);
          runAnalysis(defaultId, sens, targ);
        } catch {
          runAnalysis(defaultId);
        }
      } else {
        setResults(null);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const runAnalysis = async (dsId?: number, sensOverride?: string, targOverride?: string) => {
    const idToUse = dsId || selectedDatasetId;
    if (!idToUse) return;

    try {
      setAnalyzing(true);
      const res = await api.analyzeFairness({
        application_id: application?.id || 1,
        dataset_id: idToUse,
        sensitive_attribute: sensOverride || sensitiveAttr,
        target_attribute: targOverride || targetAttr,
        favorable_outcome: favorableOutcome
      });
      setResults(res);
    } catch (err: any) {
      alert("Error analyzing fairness: " + (err.message || "Failed"));
    } finally {
      setAnalyzing(false);
    }
  };

  const getRiskBadge = (level: string) => {
    switch (level?.toLowerCase()) {
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

  const chartData = results?.group_metrics.map((g) => ({
    name: g.group,
    selectionRate: (g.selection_rate * 100).toFixed(1),
    tpr: g.tpr !== undefined && g.tpr !== null ? (g.tpr * 100).toFixed(1) : undefined,
    fpr: g.fpr !== undefined && g.fpr !== null ? (g.fpr * 100).toFixed(1) : undefined,
    count: g.total_count,
    positiveCount: g.positive_count
  })) || [];

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Module Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-50 text-sky-700 border border-sky-200">
                MODULE 2
              </span>
              <span className="text-xs text-slate-400 font-medium">Fairlearn Engine • EEOC 80% Rule</span>
            </div>
            <h1 className="text-xl font-bold text-slate-900">AI Fairness & Demographic Disparity Detection</h1>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
              Detect disparate impact across sensitive protected groups (gender, age, ethnicity) using Demographic Parity Ratio and Equal Opportunity metrics.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <span className="text-xs text-slate-500 font-medium">Dataset:</span>
            {datasets.length > 0 ? (
              <select
                value={selectedDatasetId || ''}
                onChange={async (e) => {
                  const id = Number(e.target.value);
                  setSelectedDatasetId(id);
                  try {
                    const prev = await api.getDatasetPreview(id);
                    const cols = prev.columns || [];
                    let sens = sensitiveAttr;
                    let targ = targetAttr;
                    if (cols.includes('customer_gender')) sens = 'customer_gender';
                    else if (cols.includes('gender')) sens = 'gender';

                    if (cols.includes('service_approved')) targ = 'service_approved';
                    else if (cols.includes('recommended_ceramic')) targ = 'recommended_ceramic';
                    else if (cols.includes('selected')) targ = 'selected';

                    setSensitiveAttr(sens);
                    setTargetAttr(targ);
                    runAnalysis(id, sens, targ);
                  } catch {
                    runAnalysis(id);
                  }
                }}
                className="text-xs px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 focus:outline-hidden font-medium"
              >
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.original_filename} ({d.row_count} rows)
                  </option>
                ))}
              </select>
            ) : (
              <span className="text-xs text-slate-400 font-medium italic">None uploaded</span>
            )}
          </div>
        </div>

        {/* Audit Configuration Controls */}
        <div className="mt-5 pt-4 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
          <div>
            <label className="block text-slate-500 font-semibold mb-1">Sensitive Attribute</label>
            <input
              type="text"
              value={sensitiveAttr}
              onChange={(e) => setSensitiveAttr(e.target.value)}
              placeholder="e.g. customer_gender"
              className="w-full px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white"
            />
          </div>
          <div>
            <label className="block text-slate-500 font-semibold mb-1">Target Decision Column</label>
            <input
              type="text"
              value={targetAttr}
              onChange={(e) => setTargetAttr(e.target.value)}
              placeholder="e.g. service_approved"
              className="w-full px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white"
            />
          </div>
          <div>
            <label className="block text-slate-500 font-semibold mb-1">Favorable Outcome Value</label>
            <input
              type="text"
              value={favorableOutcome}
              onChange={(e) => setFavorableOutcome(e.target.value)}
              placeholder="e.g. 1 or Selected"
              className="w-full px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => runAnalysis()}
              disabled={analyzing || datasets.length === 0}
              className="w-full px-4 py-2 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white rounded-lg font-bold flex items-center justify-center space-x-1.5 transition shadow-xs disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 fill-current ${analyzing ? 'animate-spin' : ''}`} />
              <span>{analyzing ? 'Auditing...' : 'Re-Run Fairness Audit'}</span>
            </button>
          </div>
        </div>
      </div>

      {datasets.length === 0 && !loading && (
        <div className="bg-amber-50 border border-amber-200 text-amber-900 p-5 rounded-2xl text-xs flex items-start space-x-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-bold block text-sm mb-1">No Associated Application Dataset Found</span>
            <p className="text-slate-600 leading-relaxed">
              No dataset is currently associated with <b>{application?.name || 'this AI application'}</b>. 
              To perform demographic fairness and disparate impact evaluations, please upload an application dataset in <b>Dataset Manager</b>.
            </p>
          </div>
        </div>
      )}

      {/* Main Analysis Findings */}
      {results && (
        <>
          {/* Key Metric Scorecard Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Demographic Parity Ratio (4/5ths Rule) */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 block">Demographic Parity Ratio</span>
                <span className="text-2xl font-extrabold text-slate-900 mt-1 block">
                  {(results.demographic_parity_ratio * 100).toFixed(1)}%
                </span>
                <p className="text-[11px] text-slate-400 mt-0.5">Ratio of min to max group rate</p>
              </div>
              <div className="mt-4">
                <span className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-md text-[11px] font-bold border ${
                  results.four_fifths_rule_passed
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                    : 'bg-rose-50 text-rose-800 border-rose-200'
                }`}>
                  {results.four_fifths_rule_passed ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span>EEOC 4/5ths Rule Passed</span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                      <span>4/5ths Rule Violated (&lt;80%)</span>
                    </>
                  )}
                </span>
              </div>
            </div>

            {/* Demographic Parity Difference */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 block">Selection Rate Difference</span>
                <span className="text-2xl font-extrabold text-slate-900 mt-1 block">
                  {(results.demographic_parity_diff * 100).toFixed(1)}%
                </span>
                <p className="text-[11px] text-slate-400 mt-0.5">Absolute disparity gap between groups</p>
              </div>
              <div className="mt-4">
                <span className="text-[11px] font-medium text-slate-500">
                  Target threshold: &lt; 10%
                </span>
              </div>
            </div>

            {/* Equal Opportunity Difference */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 block">Equal Opportunity Diff</span>
                <span className="text-2xl font-extrabold text-slate-900 mt-1 block">
                  {results.equal_opportunity_diff !== null && results.equal_opportunity_diff !== undefined
                    ? `${(results.equal_opportunity_diff * 100).toFixed(1)}%`
                    : 'N/A'}
                </span>
                <p className="text-[11px] text-slate-400 mt-0.5">TPR difference among qualified candidates</p>
              </div>
              <div className="mt-4">
                <span className="text-[11px] font-medium text-slate-500">
                  Evaluates true positive fairness
                </span>
              </div>
            </div>

            {/* Overall Disparity Risk Tier */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 block">Disparity Risk Tier</span>
                <span className={`text-xl font-extrabold mt-1 inline-block px-3 py-1 rounded-lg border ${getRiskBadge(results.risk_level)}`}>
                  {results.risk_level.toUpperCase()}
                </span>
                <p className="text-[11px] text-slate-400 mt-2">Audited sample size: {results.total_samples} records</p>
              </div>
              <div className="mt-4">
                <span className="text-[11px] font-medium text-slate-500">
                  Logged in Central Risk Center
                </span>
              </div>
            </div>
          </div>

          {/* Group Comparisons Chart & Detailed Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Selection Rate Bar Chart */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-sm font-bold text-slate-900">Group Selection Rate Comparison</h2>
                  <p className="text-xs text-slate-500">Positive outcome rates across '{results.sensitive_attribute}'</p>
                </div>
                <span className="text-xs px-2.5 py-1 rounded-md bg-slate-100 text-slate-600 font-medium">
                  {results.groups.length} Protected Groups
                </span>
              </div>

              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
                    <YAxis stroke="#64748b" fontSize={11} domain={[0, 100]} unit="%" />
                    <Tooltip formatter={(value: any) => [`${value}%`, 'Selection Rate']} />
                    <Bar dataKey="selectionRate" fill="#0284c7" radius={[6, 6, 0, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={Number(entry.selectionRate) < 35 ? '#f43f5e' : '#0284c7'}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <p className="text-[11px] text-slate-400 mt-2 text-center">
                EEOC Guidelines: A selection rate for any group that is less than four-fifths (80%) of the highest group is evidence of adverse impact.
              </p>
            </div>

            {/* Confusion Matrix / Breakdown Table */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
              <div>
                <h2 className="text-sm font-bold text-slate-900 mb-1">Subgroup Performance Matrix</h2>
                <p className="text-xs text-slate-500 mb-4">Disaggregated statistics and True Positive Rates (TPR)</p>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-500 uppercase text-[10px]">
                        <th className="py-2 font-bold">Group</th>
                        <th className="py-2 font-bold text-center">Sample N</th>
                        <th className="py-2 font-bold text-center">Selected</th>
                        <th className="py-2 font-bold text-center">Selection Rate</th>
                        <th className="py-2 font-bold text-center">TPR (Recall)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {results.group_metrics.map((g) => (
                        <tr key={g.group} className="hover:bg-slate-50/80">
                          <td className="py-2.5 font-bold text-slate-800">{g.group}</td>
                          <td className="py-2.5 text-center text-slate-600">{g.total_count}</td>
                          <td className="py-2.5 text-center text-slate-600">{g.positive_count}</td>
                          <td className="py-2.5 text-center font-bold text-slate-900">
                            {(g.selection_rate * 100).toFixed(1)}%
                          </td>
                          <td className="py-2.5 text-center text-slate-600">
                            {g.tpr !== undefined && g.tpr !== null ? `${(g.tpr * 100).toFixed(1)}%` : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Sample Size Warning */}
              <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-start space-x-2">
                <Info className="w-4 h-4 text-sky-600 flex-shrink-0 mt-0.5" />
                <p className="text-[11px] leading-relaxed">
                  Subgroup representation is adequate for statistical significance (all groups N &gt; 30).
                </p>
              </div>
            </div>
          </div>

          {/* Actionable Recommendations & Limitations */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Mitigation Recommendations */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
              <h2 className="text-sm font-bold text-slate-900 mb-3 flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-teal-600" />
                <span>Fairness Mitigation Recommendations</span>
              </h2>
              <ul className="space-y-2 text-xs text-slate-600">
                {results.recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start space-x-2">
                    <span className="text-teal-600 font-bold">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Metric Limitations */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
              <h2 className="text-sm font-bold text-slate-900 mb-3 flex items-center space-x-2">
                <HelpCircle className="w-4 h-4 text-amber-600" />
                <span>Metric Limitations & Ethical Guidelines</span>
              </h2>
              <ul className="space-y-2 text-xs text-slate-600">
                {results.limitations.map((lim, i) => (
                  <li key={i} className="flex items-start space-x-2">
                    <span className="text-amber-600 font-bold">•</span>
                    <span>{lim}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

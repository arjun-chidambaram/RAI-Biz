import React, { useState, useEffect } from 'react';
import {
  Eye,
  Sparkles,
  HelpCircle,
  Play,
  Info,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  User,
  ArrowRight,
  TrendingUp,
  Cpu,
  Database,
  X
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { api, Dataset, XAIAnalysisResponse, SampleExplanation } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const ExplainableAIPage: React.FC = () => {
  const { application } = useAuth();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(null);
  const [targetAttribute, setTargetAttribute] = useState<string>('');
  const [availableColumns, setAvailableColumns] = useState<string[]>([]);
  const [modelType, setModelType] = useState<string>('RandomForest');
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<XAIAnalysisResponse | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<SampleExplanation | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    loadDatasetsAndExplain();
  }, [application?.id]);

  const loadDatasetsAndExplain = async () => {
    try {
      setLoading(true);
      setErrorMessage(null);
      const dsList = await api.getDatasets(application?.id);
      setDatasets(dsList);
      if (dsList.length > 0) {
        const firstDs = dsList[0];
        setSelectedDatasetId(firstDs.id);
        
        // Fetch columns for target selection
        try {
          const preview = await api.getDatasetPreview(firstDs.id);
          setAvailableColumns(preview.columns);
        } catch (e) {
          console.error("Preview column fetch error", e);
        }

        if (firstDs.row_count < 4) {
          setErrorMessage(
            `Dataset "${firstDs.original_filename}" has only ${firstDs.row_count} record(s). A minimum of 4 records is required to perform ML train/test splitting and explainability analysis.`
          );
          setResults(null);
        } else {
          await runExplainability(modelType, firstDs.id, '');
        }
      } else {
        setResults(null);
      }
    } catch (err: any) {
      console.error("Failed to load datasets for XAI", err);
      setErrorMessage(err.message || "Failed to load application datasets");
    } finally {
      setLoading(false);
    }
  };

  const handleDatasetChange = async (newId: number) => {
    setSelectedDatasetId(newId);
    setErrorMessage(null);
    const ds = datasets.find(d => d.id === newId);
    
    try {
      const preview = await api.getDatasetPreview(newId);
      setAvailableColumns(preview.columns);

      let currentTarget = targetAttribute;
      if (currentTarget && !preview.columns.includes(currentTarget)) {
        currentTarget = '';
        setTargetAttribute('');
      }

      if (ds && ds.row_count < 4) {
        setErrorMessage(
          `Dataset "${ds.original_filename}" has only ${ds.row_count} record(s). A minimum of 4 records is required to train and explain ML models. Please select a larger dataset or upload one in Dataset Manager.`
        );
        setResults(null);
        return;
      }

      await runExplainability(modelType, newId, currentTarget);
    } catch (err: any) {
      console.error("Failed switching dataset for XAI", err);
      setErrorMessage(err.message || "Failed to inspect selected dataset");
    }
  };

  const runExplainability = async (typeOverride?: string, dsIdOverride?: number, targetOverride?: string) => {
    const type = typeOverride || modelType;
    const dsId = dsIdOverride || selectedDatasetId;
    const target = targetOverride !== undefined ? targetOverride : targetAttribute;
    if (!application?.id && !dsId) return;

    const ds = datasets.find(d => d.id === dsId);
    if (ds && ds.row_count < 4) {
      setErrorMessage(
        `Dataset "${ds.original_filename}" has only ${ds.row_count} record(s). A minimum of 4 records is required to train and explain ML models. Please upload or select a dataset with at least 4 records.`
      );
      setResults(null);
      return;
    }

    try {
      setAnalyzing(true);
      setErrorMessage(null);
      const res = await api.analyzeExplainability({
        application_id: application?.id || 1,
        dataset_id: dsId || undefined,
        target_attribute: target || undefined,
        model_type: type
      });
      setResults(res);
      if (res.sample_explanations.length > 0) {
        setSelectedCandidate(res.sample_explanations[0]);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to train & explain model.");
      setResults(null);
    } finally {
      setAnalyzing(false);
      setLoading(false);
    }
  };

  const selectedDataset = datasets.find(d => d.id === selectedDatasetId);
  const isDatasetTooSmall = Boolean(selectedDataset && selectedDataset.row_count < 4);

  const globalChartData = results?.global_importance.map((f) => ({
    name: f.feature,
    importance: (f.importance * 100).toFixed(1),
    description: f.description
  })) || [];

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                MODULE 3
              </span>
              <span className="text-xs text-slate-400 font-medium">SHAP Game-Theoretic Attribution • scikit-learn</span>
            </div>
            <h1 className="text-xl font-bold text-slate-900">Explainable AI (XAI) & Model Transparency</h1>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
              Disclose global feature importances and individual local SHAP attribution breakdowns for why individual records receive specific model decisions.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {datasets.length > 0 && (
              <select
                value={selectedDatasetId || ''}
                onChange={(e) => handleDatasetChange(Number(e.target.value))}
                className="text-xs px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 focus:outline-hidden font-medium"
              >
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.original_filename} ({d.row_count} rows)
                  </option>
                ))}
              </select>
            )}

            {availableColumns.length > 0 && (
              <select
                value={targetAttribute}
                onChange={(e) => {
                  const newTarget = e.target.value;
                  setTargetAttribute(newTarget);
                  runExplainability(modelType, selectedDatasetId || undefined, newTarget);
                }}
                disabled={analyzing || isDatasetTooSmall}
                className="text-xs px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 focus:outline-hidden font-medium disabled:opacity-50"
              >
                <option value="">Target: Auto-Detect</option>
                {availableColumns.map((col) => (
                  <option key={col} value={col}>Target: {col}</option>
                ))}
              </select>
            )}

            <select
              value={modelType}
              onChange={(e) => {
                const newType = e.target.value;
                setModelType(newType);
                runExplainability(newType);
              }}
              disabled={analyzing || isDatasetTooSmall}
              className="text-xs px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 focus:outline-hidden font-medium disabled:opacity-50"
            >
              <option value="RandomForest">Random Forest Classifier</option>
              <option value="GradientBoosting">Gradient Boosting Machine</option>
              <option value="LogisticRegression">Logistic Regression</option>
            </select>

            <button
              onClick={() => runExplainability()}
              disabled={analyzing || datasets.length === 0 || isDatasetTooSmall}
              title={isDatasetTooSmall ? "Dataset has fewer than 4 records; minimum 4 records required." : undefined}
              className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-sky-600 hover:from-indigo-700 hover:to-sky-700 text-white rounded-xl text-xs font-bold transition flex items-center space-x-1.5 shadow-xs disabled:opacity-50"
            >
              <Cpu className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
              <span>{analyzing ? 'Training...' : 'Re-Train & Explain'}</span>
            </button>
          </div>
        </div>

        {/* Model Accuracy & Specs Strip */}
        {results && (
          <div className="mt-5 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-4 text-xs">
            <div className="flex items-center space-x-4">
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Trained Algorithm</span>
                <span className="font-bold text-slate-800">{results.model_name}</span>
              </div>
              <div className="pl-4 border-l border-slate-200">
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Test Set Accuracy</span>
                <span className="font-extrabold text-emerald-600 text-sm">{(results.model_accuracy * 100).toFixed(1)}%</span>
              </div>
              <div className="pl-4 border-l border-slate-200">
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Attribution Engine</span>
                <span className="font-semibold text-slate-700">{results.methodology.split(' ')[0]}</span>
              </div>
            </div>

            <span className="px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-700 font-medium text-[11px] border border-indigo-100">
              High Decision Explainability
            </span>
          </div>
        )}
      </div>

      {/* Actionable Error/Warning Banner */}
      {errorMessage && (
        <div className="bg-rose-50 border border-rose-200 text-rose-900 p-4 rounded-2xl text-xs flex items-start justify-between shadow-xs">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block text-sm mb-1">Explainability Notice</span>
              <p className="text-slate-700 leading-relaxed font-medium">{errorMessage}</p>
              {isDatasetTooSmall && (
                <p className="text-slate-500 mt-2 text-[11px]">
                  Tip: Navigate to <b>Dataset Manager</b> to upload a training dataset with at least 4 records and a binary classification target column.
                </p>
              )}
            </div>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-rose-400 hover:text-rose-600 p-1 rounded-lg transition"
            aria-label="Dismiss alert"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {datasets.length === 0 && !loading && (
        <div className="bg-amber-50 border border-amber-200 text-amber-900 p-5 rounded-2xl text-xs flex items-start space-x-3">
          <Database className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-bold block text-sm mb-1">No Associated Application Dataset Found</span>
            <p className="text-slate-600 leading-relaxed">
              No training dataset is currently associated with <b>{application?.name || 'this AI application'}</b>. 
              To train explainability models and inspect SHAP attributions, please upload an application dataset in <b>Dataset Manager</b>.
            </p>
          </div>
        </div>
      )}

      {results && (
        <>
          {/* Global Feature Importance Chart */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-sm font-bold text-slate-900">Global Feature Importance (Model-Wide)</h2>
                <p className="text-xs text-slate-500">Relative contribution percentage of each feature in overall predictions</p>
              </div>
              <span className="text-xs px-2.5 py-1 rounded-md bg-slate-100 text-slate-600 font-medium">
                Top Features
              </span>
            </div>

            <div className="h-60 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={globalChartData} layout="vertical" margin={{ top: 5, right: 30, left: 60, bottom: 5 }}>
                  <XAxis type="number" domain={[0, 100]} unit="%" fontSize={11} stroke="#64748b" />
                  <YAxis type="category" dataKey="name" fontSize={11} stroke="#64748b" />
                  <Tooltip formatter={(value: any) => [`${value}%`, 'Relative Weight']} />
                  <Bar dataKey="importance" fill="#4f46e5" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Local / Individual Prediction Explanations */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Record Selector List */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
              <h2 className="text-sm font-bold text-slate-900 mb-1">Individual Audit Samples</h2>
              <p className="text-xs text-slate-500 mb-4">Select record to inspect local SHAP attributions</p>

              <div className="space-y-2">
                {results.sample_explanations.map((sample, idx) => {
                  const isSelected = selectedCandidate?.sample_id === sample.sample_id;
                  const isPositive = sample.prediction === 1;

                  return (
                    <div
                      key={sample.sample_id}
                      onClick={() => setSelectedCandidate(sample)}
                      className={`p-3 rounded-xl border cursor-pointer transition flex items-center justify-between ${
                        isSelected
                          ? 'border-indigo-600 bg-indigo-50/50 shadow-xs'
                          : 'border-slate-200/80 hover:border-slate-300 bg-white'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                          isPositive ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                        }`}>
                          #{sample.sample_id}
                        </div>
                        <div>
                          <div className="text-xs font-bold text-slate-900">
                            Record #{sample.sample_id}
                          </div>
                          <div className="text-[10px] text-slate-400">
                            Confidence: {(sample.probability * 100).toFixed(1)}%
                          </div>
                        </div>
                      </div>

                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        isPositive ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'
                      }`}>
                        {isPositive ? 'POSITIVE' : 'ALTERNATIVE'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Individual Record Explanation Card (2 Cols) */}
            <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
              {selectedCandidate ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <div>
                      <span className="text-[10px] font-bold text-indigo-600 uppercase tracking-wider block">
                        Detailed Decision Breakdown
                      </span>
                      <h3 className="text-sm font-bold text-slate-900">
                        Record Decision Audit: #{selectedCandidate.sample_id}
                      </h3>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-slate-400 block font-medium">Model Probability</span>
                      <span className="text-lg font-extrabold text-slate-900">
                        {(selectedCandidate.probability * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {/* Plain Language Reasoning Narrative */}
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                      Plain-Language Decision Narrative
                    </span>
                    <p className="text-xs text-slate-700 leading-relaxed font-medium">
                      "{selectedCandidate.plain_narrative}"
                    </p>
                  </div>

                  {/* Positive & Negative Drivers Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    {/* Positive Factors */}
                    <div className="p-3.5 rounded-xl bg-emerald-50/70 border border-emerald-200/80">
                      <span className="text-[11px] font-bold text-emerald-800 flex items-center space-x-1 mb-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Positive Drivers (+ Score)</span>
                      </span>
                      <div className="space-y-1.5">
                        {selectedCandidate.top_positive_features.length > 0 ? (
                          selectedCandidate.top_positive_features.map((feat, i) => (
                            <div key={i} className="flex items-center justify-between text-[11px]">
                              <span className="text-slate-700 font-medium">{feat.feature}: <b>{feat.value}</b></span>
                              <span className="font-bold text-emerald-700">+{feat.impact.toFixed(3)}</span>
                            </div>
                          ))
                        ) : (
                          <span className="text-slate-400 text-[11px]">No significant positive drivers.</span>
                        )}
                      </div>
                    </div>

                    {/* Negative Factors */}
                    <div className="p-3.5 rounded-xl bg-rose-50/70 border border-rose-200/80">
                      <span className="text-[11px] font-bold text-rose-800 flex items-center space-x-1 mb-2">
                        <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                        <span>Limiting / Negative Factors (- Score)</span>
                      </span>
                      <div className="space-y-1.5">
                        {selectedCandidate.top_negative_features.length > 0 ? (
                          selectedCandidate.top_negative_features.map((feat, i) => (
                            <div key={i} className="flex items-center justify-between text-[11px]">
                              <span className="text-slate-700 font-medium">{feat.feature}: <b>{feat.value}</b></span>
                              <span className="font-bold text-rose-700">{feat.impact.toFixed(3)}</span>
                            </div>
                          ))
                        ) : (
                          <span className="text-slate-400 text-[11px]">No significant limiting factors.</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Raw Input Features Inspector */}
                  <div className="mt-3">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
                      Input Features Ingested for Audit Sample
                    </span>
                    <div className="flex flex-wrap gap-2 text-[11px]">
                      {Object.entries(selectedCandidate.features).map(([k, v]) => (
                        <span key={k} className="px-2 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200/60 font-mono">
                          {k}: <span className="font-bold text-indigo-700">{String(v)}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                  Select a record from the list to view its decision breakdown.
                </div>
              )}
            </div>
          </div>

          {/* Epistemological Causality Caveat Banner */}
          <div className="p-4 rounded-xl bg-amber-50/80 border border-amber-200 text-amber-900 text-[11px] leading-relaxed flex items-start space-x-3">
            <Info className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <b>Epistemological Correlation vs Causation Guardrail:</b> {results.correlation_causation_caveat}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import {
  ClipboardCheck,
  Scale,
  Eye,
  Lock,
  Leaf,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Save,
  ArrowRight,
  Info,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Sparkles,
  RefreshCw,
  Building2,
  Cpu,
  Layers,
  FileCheck
} from 'lucide-react';
import { api, QuestionDefinition, AssessmentResult } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const AssessmentPage: React.FC = () => {
  const { business, application } = useAuth();
  const [questions, setQuestions] = useState<QuestionDefinition[]>([]);
  const [answers, setAnswers] = useState<Record<string, { answer: string; notes: string }>>({});
  const [activeTab, setActiveTab] = useState<'all' | 'fairness' | 'transparency' | 'privacy' | 'sustainability'>('fairness');
  const [expandedGuidance, setExpandedGuidance] = useState<Record<string, boolean>>({});
  const [submitting, setSubmitting] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [savedResult, setSavedResult] = useState<AssessmentResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [engineSource, setEngineSource] = useState<string>('curated_domain_engine');

  useEffect(() => {
    loadQuestions();
  }, [application?.id]);

  const loadQuestions = async () => {
    try {
      setLoading(true);
      const targetAppId = application?.id;
      const data = await api.getAssessmentQuestions(targetAppId);
      setQuestions(data);

      // Initialize default answers
      const initial: Record<string, { answer: string; notes: string }> = {};
      data.forEach((q) => {
        initial[q.id] = { answer: 'No', notes: '' };
      });

      // Fetch latest assessment strictly for the active AI application to keep workspaces separate
      const existing = targetAppId ? await api.getAssessments(targetAppId) : [];
      if (existing.length > 0) {
        const latest = await api.getAssessment(existing[0].id);
        if (latest.responses) {
          latest.responses.forEach((r) => {
            initial[r.question_id] = { answer: r.answer, notes: r.notes || '' };
          });
        }
      }
      setAnswers(initial);
    } catch (err) {
      console.error("Failed to load assessment data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerateQuestions = async (forceLlm: boolean = false) => {
    if (!application?.id) return;
    try {
      setRegenerating(true);
      const res = await api.generateQuestions(application.id, forceLlm);
      setQuestions(res.questions);
      setEngineSource(res.generation_source);

      // Update question answers keeping existing user entries
      setAnswers((prev) => {
        const updated = { ...prev };
        res.questions.forEach((q) => {
          if (!updated[q.id]) {
            updated[q.id] = { answer: 'No', notes: '' };
          }
        });
        return updated;
      });
    } catch (err) {
      console.error("Failed to regenerate questions:", err);
      alert("Could not regenerate questions. Check server logs.");
    } finally {
      setRegenerating(false);
    }
  };

  const handleAnswerChange = (qId: string, answer: string) => {
    setAnswers((prev) => ({
      ...prev,
      [qId]: { ...prev[qId], answer }
    }));
  };

  const handleNotesChange = (qId: string, notes: string) => {
    setAnswers((prev) => ({
      ...prev,
      [qId]: { ...prev[qId], notes }
    }));
  };

  const toggleGuidance = (qId: string) => {
    setExpandedGuidance((prev) => ({ ...prev, [qId]: !prev[qId] }));
  };

  // Real-time score calculator
  const calculateLiveScore = () => {
    const catScores: Record<string, number[]> = {
      fairness: [],
      transparency: [],
      privacy: [],
      sustainability: []
    };

    questions.forEach((q) => {
      const entry = answers[q.id];
      if (entry) {
        if (entry.answer === 'Yes') catScores[q.category]?.push(100);
        else if (entry.answer === 'Partially') catScores[q.category]?.push(50);
        else if (entry.answer === 'No') catScores[q.category]?.push(0);
        // N/A is excluded from denominator
      }
    });

    const dimScores: Record<string, number> = {};
    for (const cat of ['fairness', 'transparency', 'privacy', 'sustainability']) {
      const arr = catScores[cat] || [];
      dimScores[cat] = arr.length > 0 ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
    }

    const overall = Object.values(dimScores).reduce((a, b) => a + b, 0) / 4.0;
    return { dimScores, overall };
  };

  const live = calculateLiveScore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      const responsesPayload = Object.entries(answers).map(([qId, val]) => {
        const qDef = questions.find((q) => q.id === qId);
        return {
          question_id: qId,
          category: qDef?.category || 'fairness',
          question_text: qDef?.question_text || `Question ${qId}`,
          guidance: qDef?.guidance,
          evidence_required: qDef?.evidence_required,
          risk_severity: qDef?.risk_severity,
          recommendation_text: qDef?.recommendation,
          answer: val.answer,
          notes: val.notes
        };
      });

      const res = await api.submitAssessment({
        business_id: business?.id || 1,
        application_id: application?.id || 1,
        name: `${business?.name || 'SME'} RAI Audit (${new Date().toLocaleDateString()})`,
        notes: `Self-reported assessment submitted for ${application?.name || 'AI System'} in ${business?.industry || 'Enterprise'}.`,
        responses: responsesPayload
      });

      setSavedResult(res);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      alert("Error saving assessment. Check console.");
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const filteredQuestions = activeTab === 'all'
    ? questions
    : questions.filter((q) => q.category === activeTab);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500 space-x-2">
        <div className="w-5 h-5 border-2 border-teal-600 border-t-transparent rounded-full animate-spin"></div>
        <span>Loading Dynamic Industry Assessment...</span>
      </div>
    );
  }

  const activeIndustry = business?.industry || 'General SME';
  const activeApp = application?.name || 'Production AI System';

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header with Dynamic Engine Context Banner */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-50 text-teal-700 border border-teal-200">
                DYNAMIC ASSESSMENT ENGINE
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-50 text-sky-700 border border-sky-200 flex items-center gap-1">
                <Building2 className="w-3 h-3" />
                {activeIndustry}
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center gap-1">
                <Cpu className="w-3 h-3" />
                {activeApp}
              </span>
              <span className="text-xs text-slate-400 font-medium">20 Criteria • 4 Dimensions</span>
            </div>
            <h1 className="text-xl font-bold text-slate-900">
              Responsible AI Assessment: <span className="text-teal-700">{business?.name || 'Enterprise'}</span>
            </h1>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
              Tailored governance questionnaire evaluating operational controls, algorithmic bias, model transparency, data protection, and green compute metrics for <b>{activeApp}</b> in the <b>{activeIndustry}</b> sector.
            </p>
          </div>

          {/* Real-time score indicator */}
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 flex items-center space-x-4 flex-shrink-0">
            <div>
              <span className="text-[10px] font-medium text-slate-500 uppercase tracking-wider block">Live Governance Index</span>
              <div className="flex items-baseline space-x-1">
                <span className={`text-2xl font-extrabold ${live.overall >= 80 ? 'text-emerald-600' : live.overall >= 60 ? 'text-amber-600' : 'text-rose-600'}`}>
                  {live.overall.toFixed(1)}
                </span>
                <span className="text-xs text-slate-400 font-semibold">/ 100</span>
              </div>
            </div>
            <div className="text-right pl-3 border-l border-slate-200 text-[11px] text-slate-500 space-y-0.5">
              <div>Fairness: <b>{live.dimScores.fairness.toFixed(0)}</b></div>
              <div>Transparency: <b>{live.dimScores.transparency.toFixed(0)}</b></div>
              <div>Privacy: <b>{live.dimScores.privacy.toFixed(0)}</b></div>
              <div>Sustainability: <b>{live.dimScores.sustainability.toFixed(0)}</b></div>
            </div>
          </div>
        </div>

        {/* Dynamic Controls Bar */}
        <div className="mt-4 pt-3.5 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center space-x-2 text-slate-500 text-[11px]">
            <Sparkles className="w-3.5 h-3.5 text-teal-600" />
            <span>Questions dynamically synthesized for <b>{activeIndustry}</b>. Engine: <code className="bg-slate-100 px-1 py-0.5 rounded font-mono text-[10px]">{engineSource}</code></span>
          </div>
          <div className="flex items-center space-x-2">
            <button
              type="button"
              disabled={regenerating}
              onClick={() => handleRegenerateQuestions(false)}
              className="px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-semibold flex items-center space-x-1.5 transition"
              title="Re-synthesize question suite based on current business profile"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin text-teal-600' : ''}`} />
              <span>{regenerating ? 'Regenerating...' : 'Refresh Dynamic Questions'}</span>
            </button>
          </div>
        </div>

        {/* Disclaimer Warning */}
        <div className="mt-3.5 p-3 rounded-xl bg-amber-50/70 border border-amber-200 text-amber-800 text-[11px] flex items-start space-x-2 leading-relaxed">
          <Info className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
          <span>
            <b>Self-Reported Governance Notice:</b> This tool provides self-reported governance assessment and internal benchmark scoring. It does NOT constitute statutory certification, legal warranty, or regulatory attestation.
          </span>
        </div>
      </div>

      {/* Success Notification if just saved */}
      {savedResult && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <div>
              <span className="font-bold">Assessment Successfully Recorded for {business?.name}!</span> Overall Score: <b>{savedResult.overall_score.toFixed(1)}/100</b>. Central Risk Center and Recommendations updated with domain findings.
            </div>
          </div>
          <button
            onClick={() => setSavedResult(null)}
            className="text-xs text-emerald-700 font-bold hover:underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Category Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-200 pb-2 text-xs font-semibold overflow-x-auto">
        {[
          { id: 'fairness', label: '1. Fairness & Equity', icon: Scale, count: 5, score: live.dimScores.fairness },
          { id: 'transparency', label: '2. Transparency', icon: Eye, count: 5, score: live.dimScores.transparency },
          { id: 'privacy', label: '3. Data Privacy', icon: Lock, count: 5, score: live.dimScores.privacy },
          { id: 'sustainability', label: '4. Green AI', icon: Leaf, count: 5, score: live.dimScores.sustainability },
          { id: 'all', label: 'View All (20)', icon: ClipboardCheck, count: 20, score: live.overall },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl transition ${
                isActive
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'bg-white hover:bg-slate-100 text-slate-600 border border-slate-200/80'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${isActive ? 'bg-slate-800 text-teal-300' : 'bg-slate-100 text-slate-500'}`}>
                {tab.score.toFixed(0)}%
              </span>
            </button>
          );
        })}
      </div>

      {/* Questions Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {filteredQuestions.map((q) => {
          const current = answers[q.id] || { answer: 'No', notes: '' };
          const isGuidanceOpen = expandedGuidance[q.id];

          // Determine severity color
          const sev = q.risk_severity || 'High';
          const sevColor =
            sev === 'Critical' ? 'bg-rose-100 text-rose-800 border-rose-200' :
            sev === 'High' ? 'bg-amber-100 text-amber-800 border-amber-200' :
            sev === 'Medium' ? 'bg-yellow-100 text-yellow-800 border-yellow-200' :
            'bg-blue-100 text-blue-800 border-blue-200';

          return (
            <div
              key={q.id}
              className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs hover:border-slate-300 transition"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start space-x-3">
                  <span className="w-7 h-7 rounded-lg bg-slate-100 text-slate-700 font-bold text-xs flex items-center justify-center flex-shrink-0 mt-0.5">
                    {q.id}
                  </span>
                  <div>
                    <div className="flex flex-wrap items-center gap-1.5 mb-1">
                      <span className="text-[10px] font-bold text-teal-700 uppercase tracking-wider">
                        {q.category_title}
                      </span>
                      {q.risk_category && (
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 font-medium border border-slate-200">
                          {q.risk_category}
                        </span>
                      )}
                      <span className={`text-[9px] px-1.5 py-0.2 rounded font-bold border ${sevColor}`}>
                        {sev} Severity
                      </span>
                    </div>
                    <h3 className="text-xs font-bold text-slate-900 leading-snug">
                      {q.question_text}
                    </h3>
                  </div>
                </div>

                {/* Answer Buttons: Yes = 100, Partially = 50, No = 0, N/A */}
                <div className="flex items-center space-x-1.5 flex-shrink-0">
                  {[
                    { label: 'Yes', value: 'Yes' },
                    { label: 'Partially', value: 'Partially' },
                    { label: 'No', value: 'No' },
                    { label: 'N/A', value: 'N/A' },
                  ].map((btn) => (
                    <label
                      key={btn.value}
                      className={`cursor-pointer px-2.5 py-1 rounded-lg text-xs font-semibold border transition ${
                        current.answer === btn.value
                          ? (btn.value === 'Yes' ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs' :
                             btn.value === 'Partially' ? 'bg-amber-500 text-white border-amber-500 shadow-xs' :
                             btn.value === 'No' ? 'bg-rose-600 text-white border-rose-600 shadow-xs' :
                             'bg-slate-600 text-white border-slate-600 shadow-xs')
                          : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
                      }`}
                    >
                      <input
                        type="radio"
                        name={`q_${q.id}`}
                        value={btn.value}
                        checked={current.answer === btn.value}
                        onChange={() => handleAnswerChange(q.id, btn.value)}
                        className="hidden"
                      />
                      {btn.label}
                    </label>
                  ))}
                </div>
              </div>

              {/* Guidance Toggle & Notes Area */}
              <div className="mt-3 pt-3 border-t border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => toggleGuidance(q.id)}
                  className="text-slate-500 hover:text-teal-700 flex items-center space-x-1 text-[11px] font-medium"
                >
                  <HelpCircle className="w-3.5 h-3.5" />
                  <span>{isGuidanceOpen ? "Hide Guidance & Evidence Requirements" : "Inspection Guidance & Evidence Required"}</span>
                  {isGuidanceOpen ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </button>

                <div className="flex-1 max-w-md">
                  <input
                    type="text"
                    placeholder="Evidence / Audit Notes (optional)..."
                    value={current.notes}
                    onChange={(e) => handleNotesChange(q.id, e.target.value)}
                    className="w-full text-xs px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 focus:bg-white focus:border-teal-500 focus:outline-hidden"
                  />
                </div>
              </div>

              {/* Expanded Guidance & Evidence Box */}
              {isGuidanceOpen && (
                <div className="mt-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 space-y-2 animate-fadeIn">
                  <div>
                    <span className="font-semibold text-slate-800">Audit Guidance: </span>
                    {q.guidance}
                  </div>
                  <div>
                    <span className="font-semibold text-rose-700">Why It Matters: </span>
                    {q.why_it_matters}
                  </div>
                  {q.evidence_required && (
                    <div className="flex items-start space-x-1.5 text-slate-700">
                      <FileCheck className="w-3.5 h-3.5 text-teal-600 flex-shrink-0 mt-0.5" />
                      <span>
                        <span className="font-semibold text-teal-800">Required Evidence: </span>
                        {q.evidence_required}
                      </span>
                    </div>
                  )}
                  {q.recommendation && (
                    <div className="text-[11px] text-slate-500 pt-1 border-t border-slate-200/60">
                      <span className="font-semibold text-slate-700">Recommended Action if Deficient: </span>
                      {q.recommendation}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {/* Submit Bar */}
        <div className="p-4 bg-white rounded-2xl border border-slate-200/80 shadow-md flex items-center justify-between sticky bottom-4 z-10">
          <div className="text-xs text-slate-600">
            Current Score: <span className="font-bold text-slate-900">{live.overall.toFixed(1)}/100</span> • Submitting updates the Central Risk Center & Recommendations.
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="px-6 py-2.5 bg-gradient-to-r from-teal-600 to-sky-700 hover:from-teal-700 hover:to-sky-800 text-white rounded-xl text-xs font-bold shadow-md shadow-teal-900/20 transition flex items-center space-x-2"
          >
            <Save className="w-4 h-4" />
            <span>{submitting ? 'Recording Assessment...' : 'Save & Update Governance Audit'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};

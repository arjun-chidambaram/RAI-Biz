import React, { useState } from 'react';
import {
  Settings,
  Database,
  Key,
  Shield,
  RefreshCw,
  ExternalLink,
  CheckCircle2,
  Info,
  Server,
  FileCode2
} from 'lucide-react';
import { api } from '../api/client';

export const SettingsPage: React.FC = () => {
  const [seeding, setSeeding] = useState(false);
  const [seedSuccess, setSeedSuccess] = useState(false);

  const handleSeed = async () => {
    try {
      setSeeding(true);
      await api.seedDemo();
      setSeedSuccess(true);
      setTimeout(() => setSeedSuccess(false), 5000);
    } catch (err) {
      alert("Failed to seed demo data");
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <div className="flex items-center space-x-2 mb-1">
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
            SYSTEM SETTINGS
          </span>
          <span className="text-xs text-slate-400 font-medium">Platform Diagnostics & Integrations</span>
        </div>
        <h1 className="text-xl font-bold text-slate-900">Governance Settings & Integrations</h1>
        <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
          Manage API connectivity, synthetic benchmark data seeds, database adapters, and LLM governance advisor configurations.
        </p>
      </div>

      {seedSuccess && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <span>SmartHire Solutions benchmark scenario re-seeded successfully! All modules refreshed.</span>
        </div>
      )}

      {/* Demo Scenario Control */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Synthetic Demo Scenario Seeder</h2>
            <p className="text-xs text-slate-500">
              Reloads the SmartHire Solutions recruitment AI demo dataset, baseline assessment with detected bias, unredacted PII samples, and carbon modeling.
            </p>
          </div>
          <button
            onClick={handleSeed}
            disabled={seeding}
            className="px-4 py-2 bg-gradient-to-r from-teal-600 to-sky-700 hover:from-teal-700 hover:to-sky-800 text-white rounded-xl text-xs font-bold transition flex items-center space-x-1.5 shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${seeding ? 'animate-spin' : ''}`} />
            <span>{seeding ? 'Seeding Demo Data...' : 'Re-Seed SmartHire Demo'}</span>
          </button>
        </div>
      </div>

      {/* Engine & Database Architecture */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
        <h2 className="text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">
          Architecture & Operational Environment
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <span className="font-bold text-slate-800 flex items-center space-x-1.5">
              <Database className="w-4 h-4 text-sky-600" />
              <span>Persistence Layer</span>
            </span>
            <p className="text-slate-600 text-[11px] leading-relaxed">
              Active: <b>SQLite (MVP Local Mode)</b>. Built with standard SQLAlchemy ORM schemas; 100% PostgreSQL-compatible without code changes.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <span className="font-bold text-slate-800 flex items-center space-x-1.5">
              <Server className="w-4 h-4 text-teal-600" />
              <span>AI & Analytical Engines</span>
            </span>
            <p className="text-slate-600 text-[11px] leading-relaxed">
              Powered by <b>scikit-learn 1.8.0</b>, <b>Fairlearn 0.15.0</b>, <b>SHAP 0.54.1</b>, <b>Pandas 3.0.1</b>, and <b>ReportLab 5.1.0</b>.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <span className="font-bold text-slate-800 flex items-center space-x-1.5">
              <Key className="w-4 h-4 text-indigo-600" />
              <span>Recommendation Engine Mode</span>
            </span>
            <p className="text-slate-600 text-[11px] leading-relaxed">
              Deterministic SME Heuristic Rule Engine with automatic fallback. Gemini 2.5 Flash active if <code className="bg-slate-200 px-1 rounded text-[10px]">GEMINI_API_KEY</code> environment variable is set.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <span className="font-bold text-slate-800 flex items-center space-x-1.5">
              <FileCode2 className="w-4 h-4 text-slate-700" />
              <span>FastAPI Documentation</span>
            </span>
            <p className="text-slate-600 text-[11px] leading-relaxed">
              Interactive OpenAPI documentation available at <a href={api.getDocsUrl()} target="_blank" rel="noreferrer" className="text-teal-700 font-bold underline">/docs</a> with auto-generated schema validation.
            </p>
          </div>
        </div>
      </div>

      {/* Disclaimers & Governance Notice */}
      <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 text-slate-500 text-[11px] leading-relaxed flex items-start space-x-3">
        <Info className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
        <div>
          <b>Security & Compliance Assurance:</b> RAI-Biz operates with zero involuntary external telemetry. Sensitive uploaded records are shielded by localized heuristic masking algorithms, preventing unconsented training data leaks or third-party compliance exposure.
        </div>
      </div>
    </div>
  );
};

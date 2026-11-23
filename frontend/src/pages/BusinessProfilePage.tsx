import React, { useState, useEffect } from 'react';
import {
  Building2,
  Cpu,
  Save,
  CheckCircle2,
  AlertTriangle,
  Info,
  Shield,
  Layers
} from 'lucide-react';
import { api, Business, AIApplication } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const BusinessProfilePage: React.FC = () => {
  const { refreshUser } = useAuth();
  const [business, setBusiness] = useState<Business | null>(null);
  const [applications, setApplications] = useState<AIApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Form states
  const [bizName, setBizName] = useState('');
  const [industry, setIndustry] = useState('');
  const [size, setSize] = useState('11-50');
  const [location, setLocation] = useState('');
  const [desc, setDesc] = useState('');
  const [contactEmail, setContactEmail] = useState('');

  // AI Application state
  const [appName, setAppName] = useState('');
  const [purpose, setPurpose] = useState('');
  const [bizFunction, setBizFunction] = useState('');
  const [dataTypes, setDataTypes] = useState('');
  const [decisionImpact, setDecisionImpact] = useState('High');
  const [oversight, setOversight] = useState('None');

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      // Attempt unified profile fetch first
      try {
        const prof = await api.getBusinessProfile();
        if (prof.business) {
          const b = prof.business;
          setBusiness(b);
          setBizName(b.name || '');
          setIndustry(b.industry || '');
          setSize(b.size || '11-50');
          setLocation(b.location || '');
          setDesc(b.description || '');
          setContactEmail(b.contact_email || '');

          if (prof.application) {
            const a = prof.application;
            setApplications([a]);
            setAppName(a.name || '');
            setPurpose(a.purpose || '');
            setBizFunction(a.business_function || '');
            setDataTypes(a.data_types || '');
            setDecisionImpact(a.automated_decision_impact || 'High');
            setOversight(a.human_oversight || 'None');
          }
          return;
        }
      } catch {
        // Fall back to listing businesses
      }

      const bizList = await api.getBusinesses();
      if (bizList.length > 0) {
        const b = bizList[0];
        setBusiness(b);
        setBizName(b.name);
        setIndustry(b.industry);
        setSize(b.size);
        setLocation(b.location);
        setDesc(b.description || '');
        setContactEmail(b.contact_email || '');

        const apps = await api.getApplications(b.id);
        setApplications(apps);
        if (apps.length > 0) {
          const a = apps[0];
          setAppName(a.name);
          setPurpose(a.purpose);
          setBizFunction(a.business_function);
          setDataTypes(a.data_types);
          setDecisionImpact(a.automated_decision_impact);
          setOversight(a.human_oversight);
        }
      }
    } catch (err) {
      console.error("Failed to load business profile:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      const res = await api.updateBusinessProfile({
        name: bizName,
        industry,
        size,
        location,
        description: desc,
        contact_email: contactEmail,
        app_name: appName,
        purpose,
        business_function: bizFunction,
        data_types: dataTypes,
        automated_decision_impact: decisionImpact,
        human_oversight: oversight
      });

      setBusiness(res.business);
      if (res.application) {
        setApplications([res.application]);
      }
      await refreshUser();

      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 4000);
    } catch (err: any) {
      console.error("Failed to save profile:", err);
      alert("Failed to save profile: " + (err.message || 'Unknown error'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                ORGANIZATIONAL GOVERNANCE
              </span>
              <span className="text-xs text-slate-400 font-medium">SME Registration & AI Application Catalog</span>
            </div>
            <h1 className="text-xl font-bold text-slate-900">Business Profile & AI Systems</h1>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
              Define SME organizational scale, operational sector, and register production AI applications with decision impact and human oversight tiers.
            </p>
          </div>

          {savedSuccess && (
            <div className="flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold animate-fadeIn">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Profile Updated</span>
            </div>
          )}
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Section 1: Business Details */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-100">
            <Building2 className="w-5 h-5 text-slate-700" />
            <h2 className="text-sm font-bold text-slate-900">SME Business Information</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div>
              <label className="font-bold text-slate-700 block mb-1">Business Name</label>
              <input
                type="text"
                required
                value={bizName}
                onChange={(e) => setBizName(e.target.value)}
                placeholder="e.g. Suntech Enterprise"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white"
              />
            </div>

            <div>
              <label className="font-bold text-slate-700 block mb-1">Industry Sector</label>
              <input
                type="text"
                required
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                placeholder="e.g. Automotive Services"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white"
              />
            </div>

            <div>
              <label className="font-bold text-slate-700 block mb-1">Company Size (Employees)</label>
              <select
                value={size}
                onChange={(e) => setSize(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white font-semibold"
              >
                <option value="1-10">Micro (1 - 10 employees)</option>
                <option value="11-50">Small (11 - 50 employees)</option>
                <option value="51-250">Medium (51 - 250 employees)</option>
                <option value="250+">Mid-Market (250+ employees)</option>
              </select>
            </div>

            <div>
              <label className="font-bold text-slate-700 block mb-1">Jurisdiction / Location</label>
              <input
                type="text"
                required
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. India"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white"
              />
            </div>

            <div>
              <label className="font-bold text-slate-700 block mb-1">Governance Contact Email</label>
              <input
                type="email"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                placeholder="contact@suntechenterprise.com"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white"
              />
            </div>

            <div className="md:col-span-3">
              <label className="font-bold text-slate-700 block mb-1">Business Description</label>
              <textarea
                rows={2}
                value={desc}
                onChange={(e) => setDesc(e.target.value)}
                placeholder="Brief summary of company operations and automated AI deployment context..."
                className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white"
              />
            </div>
          </div>
        </div>

        {/* Section 2: AI Application System */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-100">
            <Cpu className="w-5 h-5 text-teal-600" />
            <h2 className="text-sm font-bold text-slate-900">Target AI Application Specification</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div>
              <label className="font-bold text-slate-700 block mb-1">Application Name</label>
              <input
                type="text"
                required
                value={appName}
                onChange={(e) => setAppName(e.target.value)}
                placeholder="e.g. Smart Car Detailing Assistant"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white"
              />
            </div>

            <div>
              <label className="font-bold text-slate-700 block mb-1">Business Function</label>
              <input
                type="text"
                required
                value={bizFunction}
                onChange={(e) => setBizFunction(e.target.value)}
                placeholder="e.g. Talent Acquisition & Screening"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white"
              />
            </div>

            <div>
              <label className="font-bold text-slate-700 block mb-1">Processed Data Types</label>
              <input
                type="text"
                required
                value={dataTypes}
                onChange={(e) => setDataTypes(e.target.value)}
                placeholder="e.g. Resumes, Test Scores, Ratings"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white"
              />
            </div>

            <div>
              <label className="font-bold text-slate-700 block mb-1">Automated Decision Impact</label>
              <select
                value={decisionImpact}
                onChange={(e) => setDecisionImpact(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white font-semibold"
              >
                <option value="High">High (Direct employment, credit, or legal effect)</option>
                <option value="Medium">Medium (Recommendation with substantial weight)</option>
                <option value="Low">Low (Informational triage / non-binding)</option>
              </select>
            </div>

            <div>
              <label className="font-bold text-slate-700 block mb-1">Human Oversight Tier</label>
              <select
                value={oversight}
                onChange={(e) => setOversight(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white font-semibold"
              >
                <option value="None">None (Fully Autonomous Automated Execution)</option>
                <option value="Partial">Partial (Human review on appeal/dispute)</option>
                <option value="Full">Full (Mandatory human reviewer sign-off)</option>
              </select>
            </div>

            <div className="md:col-span-3">
              <label className="font-bold text-slate-700 block mb-1">System Purpose & Operating Model</label>
              <textarea
                rows={2}
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                placeholder="Describe intended automated use, operational workflow, and user-facing impact..."
                className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white"
              />
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2.5 bg-gradient-to-r from-teal-600 to-sky-700 hover:from-teal-700 hover:to-sky-800 text-white rounded-xl text-xs font-bold transition flex items-center space-x-2 shadow-md shadow-teal-900/20"
            >
              <Save className="w-4 h-4" />
              <span>{saving ? 'Updating...' : 'Save Profile & Catalog'}</span>
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

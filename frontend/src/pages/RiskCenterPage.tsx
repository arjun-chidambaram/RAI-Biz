import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  ShieldAlert,
  CheckCircle2,
  Clock,
  Filter,
  Plus,
  Info,
  Scale,
  Eye,
  Lock,
  Leaf,
  ClipboardCheck,
  Search,
  Check,
  ChevronDown,
  ChevronUp,
  History,
  Calendar,
  User,
  FileCheck,
  Activity,
  Save
} from 'lucide-react';
import { api, RiskItem } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const RiskCenterPage: React.FC = () => {
  const { application, business } = useAuth();
  const [allRisks, setAllRisks] = useState<RiskItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedModule, setSelectedModule] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [expandedRemediation, setExpandedRemediation] = useState<Record<number, boolean>>({});
  const [editingRisk, setEditingRisk] = useState<Record<number, { notes: string; owner: string; date: string }>>({});

  // New risk state
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newModule, setNewModule] = useState('governance');
  const [newSeverity, setNewSeverity] = useState<'Critical' | 'High' | 'Medium' | 'Low'>('High');
  const [newEvidence, setNewEvidence] = useState('');
  const [newImpact, setNewImpact] = useState('');
  const [newAction, setNewAction] = useState('');

  useEffect(() => {
    loadRisks();
  }, [application?.id]);

  const loadRisks = async () => {
    try {
      setLoading(true);
      const data = await api.getRisks({
        application_id: application?.id || 1
      });
      setAllRisks(data);

      const editState: Record<number, { notes: string; owner: string; date: string }> = {};
      data.forEach((r) => {
        editState[r.id] = {
          notes: r.completion_notes || '',
          owner: r.responsible_owner || 'Engineering',
          date: r.target_date || ''
        };
      });
      setEditingRisk(editState);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (id: number, newStatus: 'Open' | 'In progress' | 'Resolved') => {
    try {
      const current = editingRisk[id] || { notes: '', owner: 'Engineering', date: '' };
      const updated = await api.updateRisk(id, {
        status: newStatus,
        completion_notes: current.notes,
        responsible_owner: current.owner,
        target_date: current.date
      });
      setAllRisks((prev) =>
        prev.map((r) => (r.id === id ? { ...r, ...updated, status: newStatus } : r))
      );
    } catch (err) {
      alert("Failed to update status");
    }
  };

  const handleSaveRemediation = async (id: number) => {
    try {
      const current = editingRisk[id];
      if (!current) return;
      const updated = await api.updateRisk(id, {
        completion_notes: current.notes,
        responsible_owner: current.owner,
        target_date: current.date
      });
      setAllRisks((prev) =>
        prev.map((r) => (r.id === id ? { ...r, ...updated } : r))
      );
      alert("Remediation plan updated in audit register.");
    } catch (err) {
      alert("Failed to save remediation details");
    }
  };

  const toggleRemediationPanel = (id: number) => {
    setExpandedRemediation((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleCreateRisk = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createRisk({
        application_id: application?.id || 1,
        title: newTitle,
        description: newDesc,
        source_module: newModule,
        severity: newSeverity,
        evidence: newEvidence,
        business_impact: newImpact,
        recommended_action: newAction,
        status: 'Open'
      });
      setShowAddModal(false);
      setNewTitle('');
      setNewDesc('');
      setNewEvidence('');
      setNewImpact('');
      setNewAction('');
      await loadRisks();
    } catch (err) {
      alert("Failed to create risk");
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

  const getLifecycleBadge = (lifecycle?: string) => {
    switch ((lifecycle || 'New').toLowerCase()) {
      case 'new':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'repeated':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'improved':
        return 'bg-teal-50 text-teal-700 border-teal-200';
      case 'resolved':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'reopened':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  const getModuleIcon = (mod: string) => {
    switch (mod.toLowerCase()) {
      case 'fairness':
        return Scale;
      case 'transparency':
      case 'xai':
        return Eye;
      case 'privacy':
        return Lock;
      case 'sustainability':
      case 'green_ai':
        return Leaf;
      default:
        return ClipboardCheck;
    }
  };

  const criticalCount = allRisks.filter((r) => r.severity === 'Critical' && r.status !== 'Resolved').length;
  const highCount = allRisks.filter((r) => r.severity === 'High' && r.status !== 'Resolved').length;
  const mediumCount = allRisks.filter((r) => r.severity === 'Medium' && r.status !== 'Resolved').length;
  const lowCount = allRisks.filter((r) => r.severity === 'Low' && r.status !== 'Resolved').length;
  const inProgressCount = allRisks.filter((r) => r.status === 'In progress').length;
  const resolvedCount = allRisks.filter((r) => r.status === 'Resolved').length;

  const filteredRisks = allRisks.filter((r) => {
    if (selectedSeverity !== 'all' && r.severity !== selectedSeverity) return false;
    if (selectedModule !== 'all' && r.source_module.toLowerCase() !== selectedModule.toLowerCase()) return false;
    if (selectedStatus !== 'all' && r.status !== selectedStatus) return false;
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.title.toLowerCase().includes(q) ||
      r.description.toLowerCase().includes(q) ||
      r.evidence.toLowerCase().includes(q) ||
      (r.risk_key && r.risk_key.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-50 text-teal-700 border border-teal-200">
                UNIVERSAL RISK INTELLIGENCE
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                {business?.industry || 'All Industries'}
              </span>
              <span className="text-xs text-slate-400 font-medium">Standardized Likelihood × Impact Scoring</span>
            </div>
            <h1 className="text-xl font-bold text-slate-900">
              Risk Center: <span className="text-teal-700">{business?.name || 'Enterprise'}</span>
            </h1>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
              Consolidated enterprise risk register across Fairness, Transparency, Privacy, and Sustainability. Automatically synchronized with evidence attribution, lifecycle status, and remediation tracking.
            </p>
          </div>

          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition flex items-center space-x-2 shadow-xs"
          >
            <Plus className="w-4 h-4" />
            <span>Log Custom Risk</span>
          </button>
        </div>

        {/* Quick Severity & Status Strip (6 synchronized cards) */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 mt-5 pt-4 border-t border-slate-100 text-xs">
          <div className="p-3 rounded-xl bg-rose-50/70 border border-rose-200 flex items-center justify-between">
            <div>
              <span className="text-[10px] font-bold text-rose-700 uppercase block">Critical</span>
              <span className="text-xl font-extrabold text-rose-800">{criticalCount}</span>
            </div>
            <ShieldAlert className="w-4 h-4 text-rose-500" />
          </div>

          <div className="p-3 rounded-xl bg-orange-50/70 border border-orange-200 flex items-center justify-between">
            <div>
              <span className="text-[10px] font-bold text-orange-700 uppercase block">High</span>
              <span className="text-xl font-extrabold text-orange-800">{highCount}</span>
            </div>
            <AlertTriangle className="w-4 h-4 text-orange-500" />
          </div>

          <div className="p-3 rounded-xl bg-amber-50/70 border border-amber-200 flex items-center justify-between">
            <div>
              <span className="text-[10px] font-bold text-amber-700 uppercase block">Medium</span>
              <span className="text-xl font-extrabold text-amber-800">{mediumCount}</span>
            </div>
            <Info className="w-4 h-4 text-amber-500" />
          </div>

          <div className="p-3 rounded-xl bg-emerald-50/70 border border-emerald-200 flex items-center justify-between">
            <div>
              <span className="text-[10px] font-bold text-emerald-700 uppercase block">Low</span>
              <span className="text-xl font-extrabold text-emerald-800">{lowCount}</span>
            </div>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>

          <div className="p-3 rounded-xl bg-sky-50/70 border border-sky-200 flex items-center justify-between">
            <div>
              <span className="text-[10px] font-bold text-sky-700 uppercase block">In Progress</span>
              <span className="text-xl font-extrabold text-sky-800">{inProgressCount}</span>
            </div>
            <Clock className="w-4 h-4 text-sky-500" />
          </div>

          <div className="p-3 rounded-xl bg-teal-50/70 border border-teal-200 flex items-center justify-between">
            <div>
              <span className="text-[10px] font-bold text-teal-700 uppercase block">Resolved</span>
              <span className="text-xl font-extrabold text-teal-800">{resolvedCount}</span>
            </div>
            <Check className="w-4 h-4 text-teal-600" />
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col md:flex-row items-center justify-between gap-3 text-xs">
        <div className="flex-1 w-full md:max-w-xs relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search risks, evidence, impact..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-hidden"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          {/* Severity Filter */}
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-slate-200 bg-slate-50 font-semibold"
          >
            <option value="all">All Severities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>

          {/* Module Filter */}
          <select
            value={selectedModule}
            onChange={(e) => setSelectedModule(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-slate-200 bg-slate-50 font-semibold"
          >
            <option value="all">All Modules</option>
            <option value="fairness">Fairness & Bias</option>
            <option value="transparency">Transparency</option>
            <option value="privacy">Data Privacy</option>
            <option value="sustainability">Green AI</option>
          </select>

          {/* Status Filter */}
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-slate-200 bg-slate-50 font-semibold"
          >
            <option value="all">All Statuses</option>
            <option value="Open">Open</option>
            <option value="In progress">In Progress</option>
            <option value="Resolved">Resolved</option>
          </select>
        </div>
      </div>

      {/* Risks List */}
      <div className="space-y-4">
        {loading ? (
          <div className="py-12 text-center text-slate-400 text-xs">
            Loading standardized risk registry...
          </div>
        ) : filteredRisks.length > 0 ? (
          filteredRisks.map((risk) => {
            const ModIcon = getModuleIcon(risk.source_module);
            const isExpanded = expandedRemediation[risk.id];
            const edit = editingRisk[risk.id] || { notes: risk.completion_notes || '', owner: risk.responsible_owner || 'Engineering', date: risk.target_date || '' };

            // Parse history
            let historyEvents: any[] = [];
            if (risk.remediation_history_json) {
              try {
                historyEvents = JSON.parse(risk.remediation_history_json);
              } catch {}
            }

            return (
              <div
                key={risk.id}
                className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs hover:border-slate-300 transition space-y-3.5"
              >
                {/* Top Strip */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold border ${getSeverityBadge(risk.severity)}`}>
                      {risk.severity.toUpperCase()}
                    </span>
                    {risk.risk_score && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-800 border border-slate-200 flex items-center space-x-1">
                        <Activity className="w-3 h-3 text-slate-500" />
                        <span>Score: {risk.risk_score.toFixed(0)}/100</span>
                      </span>
                    )}
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getLifecycleBadge(risk.lifecycle_status)}`}>
                      {risk.lifecycle_status || 'New'}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700 flex items-center space-x-1">
                      <ModIcon className="w-3 h-3 text-slate-500" />
                      <span className="capitalize">{risk.source_module}</span>
                    </span>
                    <span className="text-[10px] text-slate-400">
                      ID: #{risk.id} • Logged {new Date(risk.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  {/* Status Dropdown */}
                  <div className="flex items-center space-x-2">
                    <span className="text-[11px] text-slate-400 font-medium">Status:</span>
                    <select
                      value={risk.status}
                      onChange={(e) => handleStatusChange(risk.id, e.target.value as any)}
                      className={`text-xs font-bold px-2.5 py-1 rounded-lg border transition ${
                        risk.status === 'Resolved'
                          ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                          : risk.status === 'In progress'
                          ? 'bg-sky-50 text-sky-800 border-sky-200'
                          : 'bg-rose-50 text-rose-800 border-rose-200'
                      }`}
                    >
                      <option value="Open">Open</option>
                      <option value="In progress">In progress</option>
                      <option value="Resolved">Resolved</option>
                    </select>
                  </div>
                </div>

                {/* Title & Description */}
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{risk.title}</h3>
                  <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                    {risk.description}
                  </p>
                </div>

                {/* Evidence & Business Impact Strip */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                        Evidence Source: {risk.evidence_source || 'Self-reported assessment'}
                      </span>
                      <span className={`text-[9px] px-1.5 py-0.2 rounded font-bold ${risk.is_verified ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-600'}`}>
                        {risk.is_verified ? 'Verified' : 'Unverified'}
                      </span>
                    </div>
                    <p className="text-[11px] font-mono text-slate-700 leading-relaxed">
                      {risk.evidence}
                    </p>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                    <span className="text-[10px] font-bold text-rose-700 uppercase tracking-wider block mb-1">
                      Business & Legal Impact
                    </span>
                    <p className="text-[11px] text-slate-700 leading-relaxed">
                      {risk.business_impact}
                    </p>
                  </div>
                </div>

                {/* Context-Aware Recommended Action */}
                <div className="p-3 rounded-xl bg-teal-50/70 border border-teal-200/80 text-xs flex items-start space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-teal-700 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-teal-900">Context-Aware Recommended Remediation: </span>
                    <span className="text-teal-800">{risk.recommended_action}</span>
                  </div>
                </div>

                {/* Remediation Management Toggle */}
                <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                  <button
                    type="button"
                    onClick={() => toggleRemediationPanel(risk.id)}
                    className="text-slate-500 hover:text-teal-700 font-semibold flex items-center space-x-1.5"
                  >
                    <History className="w-3.5 h-3.5" />
                    <span>{isExpanded ? "Hide Remediation Plan & Audit Log" : "Manage Remediation & View Audit Trail"}</span>
                    {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  </button>

                  <div className="flex items-center space-x-3 text-[11px] text-slate-500">
                    <span className="flex items-center space-x-1">
                      <User className="w-3 h-3 text-slate-400" />
                      <span>Owner: <b>{risk.responsible_owner || 'Engineering'}</b></span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Calendar className="w-3 h-3 text-slate-400" />
                      <span>Target: <b>{risk.target_date || 'Not set'}</b></span>
                    </span>
                  </div>
                </div>

                {/* Expanded Remediation Panel */}
                {isExpanded && (
                  <div className="mt-3 p-4 rounded-xl bg-slate-50/80 border border-slate-200 space-y-3 text-xs animate-fadeIn">
                    <h4 className="font-bold text-slate-800 flex items-center space-x-1.5">
                      <FileCheck className="w-3.5 h-3.5 text-teal-600" />
                      <span>Remediation Workflow & Ownership</span>
                    </h4>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="text-[11px] font-semibold text-slate-600 block mb-1">Responsible Owner / Team</label>
                        <input
                          type="text"
                          value={edit.owner}
                          onChange={(e) => setEditingRisk({ ...editingRisk, [risk.id]: { ...edit, owner: e.target.value } })}
                          placeholder="e.g. Compliance Officer, Lead ML Engineer"
                          className="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white"
                        />
                      </div>
                      <div>
                        <label className="text-[11px] font-semibold text-slate-600 block mb-1">Target Remediation Date</label>
                        <input
                          type="date"
                          value={edit.date}
                          onChange={(e) => setEditingRisk({ ...editingRisk, [risk.id]: { ...edit, date: e.target.value } })}
                          className="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="text-[11px] font-semibold text-slate-600 block mb-1">Remediation Progress Notes</label>
                      <textarea
                        rows={2}
                        value={edit.notes}
                        onChange={(e) => setEditingRisk({ ...editingRisk, [risk.id]: { ...edit, notes: e.target.value } })}
                        placeholder="Log mitigation milestones, policy updates, or verified corrective actions..."
                        className="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white"
                      />
                    </div>

                    <div className="flex items-center justify-between pt-2">
                      <button
                        type="button"
                        onClick={() => handleSaveRemediation(risk.id)}
                        className="px-3.5 py-1.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-bold transition flex items-center space-x-1.5"
                      >
                        <Save className="w-3.5 h-3.5" />
                        <span>Save Remediation Plan</span>
                      </button>
                    </div>

                    {/* Audit History Timeline */}
                    {historyEvents.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-200">
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-2">
                          Immutable Remediation Audit Trail ({historyEvents.length} Events)
                        </span>
                        <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                          {historyEvents.map((ev: any, idx: number) => (
                            <div key={idx} className="p-2 rounded-lg bg-white border border-slate-200 text-[11px] text-slate-600 flex items-center justify-between">
                              <div>
                                <span className="font-bold text-slate-800">{ev.action}</span>
                                {ev.changes && <span className="text-slate-500 ml-1">({ev.changes})</span>}
                                {ev.notes && <div className="text-slate-500 text-[10px] italic">{ev.notes}</div>}
                              </div>
                              <div className="text-right text-[10px] text-slate-400">
                                <div>{ev.user || 'system'}</div>
                                <div>{new Date(ev.timestamp).toLocaleString()}</div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="text-center py-12 bg-white rounded-2xl border border-slate-200/80 text-slate-400 text-xs">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
            <span>No risks match the current filter criteria.</span>
          </div>
        )}
      </div>

      {/* Add Custom Risk Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-2xl border border-slate-300 shadow-2xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <h2 className="text-sm font-bold text-slate-900">Log Custom Governance Risk</h2>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateRisk} className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Risk Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Unverified Vendor Sub-Processor"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Severity</label>
                  <select
                    value={newSeverity}
                    onChange={(e) => setNewSeverity(e.target.value as any)}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white font-semibold"
                  >
                    <option value="Critical">Critical</option>
                    <option value="High">High</option>
                    <option value="Medium">Medium</option>
                    <option value="Low">Low</option>
                  </select>
                </div>

                <div>
                  <label className="font-bold text-slate-700 block mb-1">Module</label>
                  <select
                    value={newModule}
                    onChange={(e) => setNewModule(e.target.value)}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white font-semibold"
                  >
                    <option value="fairness">Fairness & Bias</option>
                    <option value="transparency">Transparency</option>
                    <option value="privacy">Data Privacy</option>
                    <option value="sustainability">Green AI</option>
                    <option value="governance">Overarching Governance</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Description</label>
                <textarea
                  rows={2}
                  required
                  placeholder="Operational details and failure mode..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Evidence / Source</label>
                <input
                  type="text"
                  placeholder="e.g. Vendor contract missing DPA clause, internal audit finding"
                  value={newEvidence}
                  onChange={(e) => setNewEvidence(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Business & Legal Impact</label>
                <input
                  type="text"
                  placeholder="e.g. Breach of contractual confidentiality, GDPR fine"
                  value={newImpact}
                  onChange={(e) => setNewImpact(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Recommended Remediation Action</label>
                <input
                  type="text"
                  placeholder="e.g. Sign formal DPA addendum with vendor within 30 days"
                  value={newAction}
                  onChange={(e) => setNewAction(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white"
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3.5 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-bold"
                >
                  Log Risk
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

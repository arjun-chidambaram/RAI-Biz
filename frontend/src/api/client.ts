// API client for RAI-Biz backend with Session & CSRF Support

// Normalize API base URL from Vite environment variable (e.g. VITE_API_URL=https://rai-biz.onrender.com)
// Ensures /api is neither omitted nor duplicated, with safe fallback to '/api' for local dev proxy
const rawBase = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/+$/, '') || '';
const API_BASE = rawBase
  ? (rawBase.endsWith('/api') ? rawBase : `${rawBase}/api`)
  : '/api';

export interface User {
  id: number;
  email: string;
  full_name?: string;
  role: string;
  is_verified: boolean;
  created_at: string;
  last_login?: string;
}

export interface Business {
  id: number;
  name: string;
  industry: string;
  size: string;
  location: string;
  description?: string;
  website?: string;
  contact_email?: string;
  created_at: string;
  updated_at: string;
}

export interface AIApplication {
  id: number;
  business_id: number;
  name: string;
  purpose: string;
  business_function: string;
  data_types: string;
  automated_decision_impact: string;
  human_oversight: string;
  model_type: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface AuthStatusResponse {
  authenticated: boolean;
  user?: User;
  business?: Business;
  application?: AIApplication;
  csrf_token?: string;
  token?: string;
  message?: string;
}

export interface ProfileUpdatePayload {
  name: string;
  industry: string;
  size: string;
  location: string;
  description?: string;
  contact_email?: string;
  app_name: string;
  purpose: string;
  business_function: string;
  data_types: string;
  automated_decision_impact: string;
  human_oversight: string;
}

export interface ProfileUpdateResponse {
  success: boolean;
  business: Business;
  application: AIApplication;
  message: string;
}

export interface QuestionDefinition {
  id: string;
  category: string;
  category_title: string;
  industry?: string;
  ai_application_context?: string;
  question_text: string;
  guidance: string;
  why_it_matters: string;
  evidence_required?: string;
  risk_category?: string;
  risk_severity?: string;
  answer_options?: string[];
  recommendation?: string;
}

export interface DynamicQuestionSetResponse {
  business_id: number;
  application_id: number;
  business_name: string;
  application_name: string;
  industry: string;
  industry_key: string;
  generation_source: string;
  dimensions: string[];
  question_count: number;
  questions: QuestionDefinition[];
}

export interface SupportedIndustry {
  id: string;
  label: string;
  description: string;
}

export interface AssessmentResponseDetail {
  question_id: string;
  category: string;
  question_text: string;
  guidance?: string;
  evidence_required?: string;
  risk_severity?: string;
  recommendation_text?: string;
  answer: string;
  score: number | null;
  notes?: string;
}

export interface DimensionScore {
  dimension: string;
  score: number;
  status: string;
  answered_count: number;
  total_count: number;
}

export interface AssessmentResult {
  id: number;
  business_id: number;
  application_id: number;
  user_id?: number;
  industry?: string;
  question_version?: string;
  name: string;
  overall_score: number;
  fairness_score: number;
  transparency_score: number;
  privacy_score: number;
  sustainability_score: number;
  dimension_scores: DimensionScore[];
  completed_at: string;
  disclaimer: string;
  responses?: AssessmentResponseDetail[];
}

export interface Dataset {
  id: number;
  application_id?: number;
  filename: string;
  original_filename: string;
  file_size_bytes: number;
  row_count: number;
  column_count: number;
  checksum: string;
  schema_version: string;
  status: string;
  created_at: string;
}

export interface DatasetPreview {
  dataset_id: number;
  filename: string;
  row_count: number;
  column_count: number;
  columns: string[];
  dtypes: Record<string, string>;
  head: Record<string, any>[];
  missing_counts: Record<string, number>;
  duplicate_count: number;
}

export interface GroupMetric {
  group: string;
  total_count: number;
  positive_count: number;
  selection_rate: number;
  tpr?: number;
  fpr?: number;
  tnr?: number;
  fnr?: number;
}

export interface FairnessAnalysisResponse {
  sensitive_attribute: string;
  target_attribute: string;
  favorable_outcome: string;
  total_samples: number;
  groups: string[];
  group_metrics: GroupMetric[];
  demographic_parity_diff: number;
  demographic_parity_ratio: number;
  equal_opportunity_diff?: number;
  four_fifths_rule_passed: boolean;
  risk_level: string;
  recommendations: string[];
  limitations: string[];
}

export interface FeatureImportanceItem {
  feature: string;
  importance: number;
  description: string;
}

export interface SampleExplanation {
  sample_id: number;
  features: Record<string, any>;
  prediction: any;
  probability: number;
  model_confidence?: number;
  top_positive_features: { feature: string; value: any; impact: number; feature_display?: string }[];
  top_negative_features: { feature: string; value: any; impact: number; feature_display?: string }[];
  plain_narrative: string;
}

export interface XAIAnalysisResponse {
  model_name: string;
  task_type: string;
  model_accuracy: number;
  accuracy_warning?: string | null;
  prediction_disclaimer?: string | null;
  global_importance: FeatureImportanceItem[];
  sample_explanations: SampleExplanation[];
  methodology: string;
  correlation_causation_caveat: string;
}

export interface PIIFindingItem {
  column: string;
  pii_type: string;
  sample_masked: string;
  match_count: number;
  risk_severity: string;
}

export interface PrivacyScanResponse {
  total_records_scanned: number;
  pii_detected_count: number;
  findings: PIIFindingItem[];
  missing_summary: Record<string, number>;
  duplicate_rows: number;
  data_minimization_alerts: string[];
  governance_checklist_status: Record<string, string>;
  risk_level: string;
  disclaimer: string;
}

export interface OptimizationScenario {
  scenario_name: string;
  description: string;
  projected_energy_kwh: number;
  projected_co2e_kg: number;
  reduction_percentage: number;
  annual_cost_savings_estimate_usd: number;
}

export interface SustainabilityResponse {
  compute_duration_hours: number;
  power_draw_kw: number;
  energy_kwh: number;
  emission_factor_kg_per_kwh: number;
  region_name: string;
  estimated_co2e_kg: number;
  equivalent_car_miles: number;
  tree_seedlings_needed_10_years: number;
  scenarios: OptimizationScenario[];
  actionable_recommendations: string[];
  assumptions_disclaimer: string;
}

export interface RiskItem {
  id: number;
  application_id: number;
  assessment_id?: number;
  title: string;
  description: string;
  source_module: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  evidence: string;
  business_impact: string;
  recommended_action: string;
  status: 'Open' | 'In progress' | 'Resolved';
  risk_key?: string;
  category?: string;
  likelihood?: string;
  impact?: string;
  exposure_factor?: string;
  control_effectiveness?: string;
  risk_score?: number;
  evidence_source?: string;
  is_verified?: boolean;
  lifecycle_status?: 'New' | 'Repeated' | 'Improved' | 'Resolved' | 'Reopened';
  responsible_owner?: string;
  target_date?: string;
  completion_notes?: string;
  supporting_evidence?: string;
  remediation_history_json?: string;
  created_at: string;
  updated_at: string;
}

export interface RecommendationItem {
  id: number;
  application_id: number;
  problem: string;
  why_it_matters: string;
  action: string;
  priority: 'High' | 'Medium' | 'Low';
  expected_business_benefit: string;
  responsible_team: string;
  status: string;
  source_module: string;
  created_at: string;
}

export interface DashboardSummary {
  business?: Business;
  application?: AIApplication;
  overall_governance_score: number;
  fairness_score: number;
  transparency_score: number;
  privacy_score: number;
  sustainability_score: number;
  total_risks_count: number;
  high_critical_risks_count: number;
  resolved_risks_count: number;
  radar_data: { subject: string; score: number; fullMark: number }[];
  risk_distribution: Record<string, number>;
  recent_assessments: { id: number; name: string; overall_score: number; date: string; is_current: boolean }[];
  top_recommendations: RecommendationItem[];
  recent_alerts: { id: number; title: string; severity: string; module: string; status: string; impact: string }[];
  green_co2e_summary_kg: number;
}

function getCsrfToken(): string | null {
  const match = document.cookie.match(new RegExp('(^|;\\s*)rai_biz_csrf=([^;]*)'));
  return match ? decodeURIComponent(match[2]) : null;
}

async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  
  // Attach session Bearer token for resilient cross-domain requests
  const storedToken = typeof window !== 'undefined' ? localStorage.getItem('rai_biz_auth_token') : null;
  if (storedToken && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${storedToken}`);
  }

  // Attach CSRF token on mutation methods
  const method = (options.method || 'GET').toUpperCase();
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    const csrf = getCsrfToken();
    if (csrf && !headers.has('X-CSRF-Token')) {
      headers.set('X-CSRF-Token', csrf);
    }
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include' // Enforce HttpOnly cookie delivery
  });

  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : (errJson.detail.message || JSON.stringify(errJson.detail));
      }
    } catch {
      // Non-JSON error
    }
    const err = new Error(errorDetail) as any;
    err.status = res.status;
    throw err;
  }

  return res.json();
}

export const api = {
  // Authentication
  sendOtp: async (email: string): Promise<{ success: boolean; message: string; email: string }> => {
    return apiFetch('/auth/send-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
  },

  verifyOtp: async (email: string, otp: string): Promise<AuthStatusResponse> => {
    const res = await apiFetch<AuthStatusResponse>('/auth/verify-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, otp })
    });
    if (res.token && typeof window !== 'undefined') {
      localStorage.setItem('rai_biz_auth_token', res.token);
    }
    return res;
  },

  resendOtp: async (email: string): Promise<{ success: boolean; message: string; email: string }> => {
    return apiFetch('/auth/resend-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
  },

  demoLogin: async (email: string): Promise<AuthStatusResponse> => {
    const res = await apiFetch<AuthStatusResponse>('/auth/demo-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    if (res.token && typeof window !== 'undefined') {
      localStorage.setItem('rai_biz_auth_token', res.token);
    }
    return res;
  },

  getMe: async (): Promise<AuthStatusResponse> => {
    return apiFetch('/auth/me');
  },

  logout: async (): Promise<{ success: boolean; message: string }> => {
    try {
      return await apiFetch('/auth/logout', {
        method: 'POST'
      });
    } finally {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('rai_biz_auth_token');
      }
    }
  },

  // Business & Applications
  getBusinessProfile: async (): Promise<ProfileUpdateResponse> => {
    return apiFetch('/businesses/profile');
  },
  updateBusinessProfile: async (data: ProfileUpdatePayload): Promise<ProfileUpdateResponse> => {
    return apiFetch('/businesses/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  },
  getBusinesses: async (): Promise<Business[]> => {
    return apiFetch('/businesses');
  },
  createBusiness: async (data: Partial<Business>): Promise<Business> => {
    return apiFetch('/businesses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  },
  getApplications: async (businessId?: number): Promise<AIApplication[]> => {
    const url = businessId ? `/applications?business_id=${businessId}` : '/applications';
    return apiFetch(url);
  },
  createApplication: async (data: Partial<AIApplication>): Promise<AIApplication> => {
    return apiFetch('/applications', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  },

  // Assessment
  getAssessmentQuestions: async (appId?: number): Promise<QuestionDefinition[]> => {
    const url = appId ? `/assessments/questions?application_id=${appId}` : '/assessments/questions';
    return apiFetch(url);
  },
  generateQuestions: async (appId?: number, forceLlm?: boolean): Promise<DynamicQuestionSetResponse> => {
    return apiFetch('/assessments/generate-questions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ application_id: appId, force_llm: forceLlm || false })
    });
  },
  getSupportedIndustries: async (): Promise<SupportedIndustry[]> => {
    return apiFetch('/assessments/industries');
  },
  submitAssessment: async (payload: any): Promise<AssessmentResult> => {
    return apiFetch('/assessments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  },
  getAssessments: async (appId?: number): Promise<AssessmentResult[]> => {
    const url = appId ? `/assessments?application_id=${appId}` : '/assessments';
    return apiFetch(url);
  },
  getAssessment: async (id: number): Promise<AssessmentResult> => {
    return apiFetch(`/assessments/${id}`);
  },

  // Datasets
  getDatasets: async (appId?: number): Promise<Dataset[]> => {
    const url = appId ? `/datasets?application_id=${appId}` : '/datasets';
    return apiFetch(url);
  },
  uploadDataset: async (file: File, appId?: number): Promise<Dataset> => {
    const formData = new FormData();
    formData.append('file', file);
    if (appId) formData.append('application_id', appId.toString());
    return apiFetch('/datasets/upload', {
      method: 'POST',
      body: formData
    });
  },
  getDatasetPreview: async (id: number): Promise<DatasetPreview> => {
    return apiFetch(`/datasets/${id}/preview`);
  },
  cleanDataset: async (id: number, opts: any): Promise<Dataset> => {
    return apiFetch(`/datasets/${id}/clean`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(opts)
    });
  },
  exportRejectedRecords: async (id: number): Promise<{ rejected_count: number; records: any[] }> => {
    return apiFetch(`/datasets/${id}/export-rejected`);
  },

  // Fairness
  analyzeFairness: async (payload: { application_id: number; dataset_id?: number; sensitive_attribute: string; target_attribute: string; favorable_outcome: any }): Promise<FairnessAnalysisResponse> => {
    return apiFetch('/fairness/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  },

  // Explainability
  analyzeExplainability: async (payload: { application_id: number; dataset_id?: number; target_attribute?: string; model_type?: string }): Promise<XAIAnalysisResponse> => {
    return apiFetch('/explainability/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  },

  // Privacy Guard
  scanPrivacy: async (payload: { application_id: number; dataset_id?: number }): Promise<PrivacyScanResponse> => {
    return apiFetch('/privacy/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  },

  // Green AI
  calculateSustainability: async (payload: { application_id: number; compute_duration_hours: number; power_draw_kw: number; emission_factor_kg_per_kwh?: number; region_preset?: string }): Promise<SustainabilityResponse> => {
    return apiFetch('/sustainability/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  },
  getEmissionRegions: async (): Promise<{ id: string; name: string; factor: number; description: string }[]> => {
    return apiFetch('/sustainability/regions');
  },

  // Risks
  getRisks: async (params?: { application_id?: number; severity?: string; status?: string; source_module?: string }): Promise<RiskItem[]> => {
    const searchParams = new URLSearchParams();
    if (params?.application_id) searchParams.append('application_id', params.application_id.toString());
    if (params?.severity) searchParams.append('severity', params.severity);
    if (params?.status) searchParams.append('status', params.status);
    if (params?.source_module) searchParams.append('source_module', params.source_module);
    const queryStr = searchParams.toString();
    return apiFetch(queryStr ? `/risks?${queryStr}` : '/risks');
  },
  createRisk: async (data: Partial<RiskItem>): Promise<RiskItem> => {
    return apiFetch('/risks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  },
  updateRisk: async (id: number, data: Partial<RiskItem>): Promise<RiskItem> => {
    return apiFetch(`/risks/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  },

  // Recommendations
  getRecommendations: async (appId?: number): Promise<RecommendationItem[]> => {
    const url = appId ? `/recommendations?application_id=${appId}` : '/recommendations';
    return apiFetch(url);
  },
  generateRecommendations: async (appId: number, assessmentId?: number): Promise<RecommendationItem[]> => {
    const url = assessmentId 
      ? `/recommendations/generate?application_id=${appId}&assessment_id=${assessmentId}`
      : `/recommendations/generate?application_id=${appId}`;
    return apiFetch(url, { method: 'POST' });
  },

  // Dashboard
  getDashboardSummary: async (appId?: number): Promise<DashboardSummary> => {
    const url = appId ? `/dashboard?application_id=${appId}` : '/dashboard';
    return apiFetch(url);
  },

  // PDF Report
  getPdfReportUrl: (assessmentId: number): string => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('rai_biz_auth_token') : null;
    return token
      ? `${API_BASE}/reports/${assessmentId}?token=${encodeURIComponent(token)}`
      : `${API_BASE}/reports/${assessmentId}`;
  },

  // Interactive Swagger Docs URL resolver
  getDocsUrl: (): string => {
    const rawBase = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/+$/, '') || '';
    if (rawBase) {
      const root = rawBase.replace(/\/api$/, '');
      return `${root}/docs`;
    }
    return 'http://127.0.0.1:8000/docs';
  },

  // Demo Seeder
  seedDemo: async (): Promise<any> => {
    return apiFetch('/demo/seed', { method: 'POST' });
  }
};

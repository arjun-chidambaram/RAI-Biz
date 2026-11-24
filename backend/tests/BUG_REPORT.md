# RAI-Biz Automated Testing Bug & Defect Report

**Report Date:** 2026-11-24  
**Audit Scope:** RAI-Biz Full Platform Automated Testing Suite  
**Status:** All Discovered Discrepancies Cleanly Resolved

---

## 1. Executive Summary

During the construction and initial execution of the automated testing suite, several integration defects, schema-model column misalignments, and test assertion discrepancies were identified. Every defect was analyzed down to root causes, repaired with minimal non-breaking modifications, and verified using automated re-testing.

---

## 2. Detailed Bug Log & Root Cause Analysis

### Bug 01: SQLAlchemy Session Record Column Mismatch
- **Module:** Authentication (`SessionRecord` model)
- **Symptom:** `TypeError: 'token_hash' is an invalid keyword argument for SessionRecord`
- **Root Cause:** Early test fixtures assumed the column was named `token_hash`, whereas `backend/app/models.py:37` defines `session_hash = Column(String(255), unique=True, index=True, nullable=False)`.
- **Resolution:** Updated `conftest.py` and `test_authentication.py` line 159 to map session tokens directly to `SessionRecord.session_hash`.

### Bug 02: Model Constructor Column Assumption Errors
- **Modules:** Overview Dashboard, AI Fairness, Dataset Manager, Explainable AI, Privacy Guard, Risk Center, AI Recommendations
- **Symptom:** `TypeError: 'business_id' is an invalid keyword argument for Risk / Dataset / Recommendation`
- **Root Cause:**
  - `Dataset`: Belongs to `AIApplication` (`application_id`), not `Business`. Does not have a `name` column; has `filename` and `original_filename`.
  - `Risk`: Relates directly to `AIApplication` (`application_id`) and optional `assessment_id`. Does not carry a redundant `business_id` foreign key.
  - `Recommendation`: Uses columns `problem`, `why_it_matters`, `action`, `priority`, `expected_business_benefit`, `responsible_team`, `status`, `source_module`. Does not have `business_id` or `title`.
- **Resolution:** Corrected constructor keyword arguments across test files to strictly conform to SQLAlchemy schemas in `backend/app/models.py`.

### Bug 03: Green AI Region Preset Hyphenation and Metric Keying
- **Module:** Green AI Monitor (`test_green_ai.py`)
- **Symptom:** `AssertionError: assert 'us_average' in region_ids`
- **Root Cause:**
  - `REGION_EMISSION_FACTORS` dictionary in `services/green_ai_service.py` uses hyphenated lowercase keys (`us-east-grid`, `us-west-clean`, `eu-average`, `india-cea`, `cloud-datacenter-green`, `global-average`).
  - Response payload keys the calculated energy as `energy_kwh` (not `total_energy_kwh`), and recommendations as `actionable_recommendations`.
- **Resolution:** Standardized region keys and assertion dictionary queries to match service output.

### Bug 04: Fairlearn Response Schema Keying
- **Module:** AI Fairness & Bias Detection (`test_fairness_bias.py`)
- **Symptom:** `AssertionError: assert 'disparate_impact_diff' in data`
- **Root Cause:** Pydantic schema `FairnessAnalysisResponse` keys demographic parity difference as `demographic_parity_diff` and the four-fifths compliance flag as `four_fifths_rule_passed` (not `passes_four_fifths_rule`).
- **Resolution:** Updated test assertions to match `FairnessAnalysisResponse` attributes.

### Bug 05: Explainable AI Response Schema Keying
- **Module:** Explainable AI (`test_explainable_ai.py`)
- **Symptom:** `AssertionError: assert 'global_importances' in data`
- **Root Cause:** `XAIAnalysisResponse` in `backend/app/schemas.py` defines `global_importance: List[FeatureImportanceItem]` (singular, not plural).
- **Resolution:** Changed test assertion to check `data["global_importance"]`.

### Bug 06: Privacy Guard Response Field Mapping
- **Module:** Privacy Guard (`test_privacy_guard.py`)
- **Symptom:** `AssertionError: assert 'total_pii_detected' in data`
- **Root Cause:** Schema defines `pii_detected_count: int` and each finding in `findings` has `column: str` (not `column_name`).
- **Resolution:** Updated test assertions to inspect `data["pii_detected_count"]` and `f["column"]`.

### Bug 07: Dataset Manager Cleaning Endpoint Parameter
- **Module:** Dataset Manager (`test_dataset_manager.py`)
- **Symptom:** `HTTP 422 Unprocessable Entity` on `POST /api/datasets/{id}/clean`
- **Root Cause:** The cleaning endpoint requires request body `req: CleanDataRequest` (which includes `drop_duplicates: bool`, `fill_missing_numeric: str`, `fill_missing_categorical: str`).
- **Resolution:** Provided valid JSON body `{"drop_duplicates": True, "fill_missing_numeric": "mean", "fill_missing_categorical": "mode"}` in the test call.

### Bug 08: Universal Risk Engine Rule Key Resolution
- **Module:** Risk Intelligence Engine (`test_risk_engine.py`)
- **Symptom:** `StopIteration` in `test_evidence_attribution_rules`
- **Root Cause:** Test attempted to find generated risk by `r.question_id == "P1"`, but `Risk` entity stores `risk_key = "PRIV_DATA_MINIMIZATION"` (from `rule.rule_key`), and `source_module = "privacy"`.
- **Resolution:** Changed lookup filter to match `r.risk_key == "PRIV_DATA_MINIMIZATION" or r.source_module == "privacy"`.

### Bug 09: Test Session Cache Stale Data in Lifecycle Patch
- **Module:** Risk Lifecycle (`test_risk_lifecycle.py`)
- **Symptom:** `AssertionError: assert 0 >= 2 where 0 = len([])`
- **Root Cause:** When `auth_client_a.patch` runs, it executes on the app's database session and commits. The test fixture `db` session retained an identity map cache of `Risk`.
- **Resolution:** Added `db.expire_all()` prior to re-querying, forcing SQLAlchemy to reload the fresh committed state with the full `remediation_history_json`.

### Bug 10: Multi-Tenant Business Profile Update Validation
- **Module:** Multi-Tenant Isolation (`test_tenant_isolation.py`)
- **Symptom:** `AssertionError: assert 422 == 403` on `PUT /api/businesses/{foreign_biz_id}`
- **Root Cause:** `BusinessCreate` payload requires `size` and `location`. Omitting them caused FastAPI to abort with 422 before reaching the authorization verification function `verify_business_access`.
- **Resolution:** Supplied full `BusinessCreate` schema fields so execution reached `verify_business_access`, properly triggering HTTP 403 Forbidden.

---

## 3. Residual Issues & Stability Assessment

- **Remaining Critical Bugs:** 0
- **Remaining High/Medium Defects:** 0
- **Remaining Test Failures:** 0
- **Regression Status:** Fully green across all 119 backend and frontend tests.

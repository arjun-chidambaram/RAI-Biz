# RAI-Biz Automated Test Cases Specification

This document details all test cases implemented across the backend test suite (86 test cases across 20 files) and frontend test suite (29 test cases across 7 suites).

---

## Part 1: Backend Pytest Test Cases (86 Tests)

### Module 01: Email OTP Authentication (`test_authentication.py`)
1. `test_send_otp_success`: Valid email receives 6-digit OTP code and HTTP 200.
2. `test_send_otp_invalid_email_format`: Malformed email formats rejected with HTTP 422.
3. `test_send_otp_cooldown_enforcement`: Immediate resend within 60s cooldown triggers HTTP 429.
4. `test_verify_otp_success_creates_session`: Valid OTP returns session cookie and Bearer token.
5. `test_verify_otp_invalid_code`: Incorrect 6-digit code returns HTTP 400.
6. `test_verify_otp_expired_code`: OTP past expiration window returns HTTP 400.
7. `test_verify_otp_reused_code`: Already-consumed OTP code cannot be reused (HTTP 400).
8. `test_verify_otp_max_attempts_lockout`: 5 consecutive wrong attempts locks the code (HTTP 400).
9. `test_auth_me_authenticated_vs_unauthenticated`: `/api/auth/me` validates session presence (200 vs 401).
10. `test_logout_invalidates_session`: Logout clears cookies and marks DB session invalid.

### Module 02: Business Management (`test_business_management.py`)
11. `test_create_business_success`: Creates business profile with industry, size, and location.
12. `test_create_business_missing_name_rejected`: Missing required fields triggers HTTP 422.
13. `test_update_business`: PUT `/api/businesses/{id}` updates attributes cleanly.
14. `test_list_businesses_scoped_to_user`: Listing businesses returns only authorized memberships.
15. `test_create_ai_application_success`: Registers target AI system under business.
16. `test_update_ai_application`: Modifies business function and oversight level.
17. `test_list_applications_for_business`: Lists applications filtered by business ID.
18. `test_business_profile_sync_endpoint`: Multi-tier profile update synchronizes primary entities.

### Module 03: Overview Dashboard (`test_dashboard.py`)
19. `test_dashboard_empty_state_returns_zeroes`: Unassessed application returns clean zero metrics.
20. `test_dashboard_populated_metrics_synchronization`: Radar scores and risk counts synchronize with DB.
21. `test_dashboard_top_recommendations_and_alerts`: Aggregates top priority action items.

### Module 04: SME Responsible AI Assessment (`test_assessments.py`)
22. `test_load_standard_questions`: Retrieves standard baseline question catalog.
23. `test_submit_assessment_mixed_scores`: Mixed Yes/Partially/No responses compute correct weighted scores.
24. `test_submit_assessment_perfect_score`: All "Yes" answers result in 100.0 across all dimensions.
25. `test_submit_assessment_zero_score`: All "No" answers result in 0.0 across all dimensions.
26. `test_retrieve_assessment_detail_by_id`: Fetches complete response details for historical audits.

### Module 05: Dynamic Questions Engine (`test_dynamic_questions.py`)
27. `test_supported_industries_directory`: Returns 12 supported industry domains.
28. `test_dynamic_questions_for_healthcare`: Generates clinical and HIPAA-tailored governance questions.
29. `test_dynamic_questions_for_banking`: Generates credit scoring and FCRA-tailored questions.
30. `test_dynamic_questions_for_education`: Generates student grading and COPPA-tailored questions.
31. `test_dynamic_questions_for_retail`: Generates dynamic pricing and consumer-tailored questions.
32. `test_dynamic_questions_incomplete_profile_safe_fallback`: Missing business context falls back safely.

### Module 06: Fairness & Bias Detection (`test_fairness_bias.py`)
33. `test_fairness_analysis_valid_dataset`: Evaluates demographic parity and four-fifths rule.
34. `test_fairness_analysis_missing_column_rejected`: Missing sensitive attribute returns HTTP 400.
35. `test_fairness_cross_application_dataset_rejected`: Foreign dataset access rejected with HTTP 400.
36. `test_fairness_non_existent_dataset_returns_404`: Non-existent dataset ID returns HTTP 404.

### Module 07: Dataset Manager (`test_dataset_manager.py`)
37. `test_upload_csv_dataset_success`: Ingests CSV, computes SHA-256 checksum and schema.
38. `test_upload_unsupported_format_rejected`: Non-tabular files (.txt) rejected with HTTP 400.
39. `test_list_datasets_scoped_to_application`: Lists datasets filtered by application ID.
40. `test_dataset_preview_endpoint`: Returns column headers, data types, and head sample records.
41. `test_dataset_cleaning_and_deduplication`: Automatically drops duplicate records and imputes missing values.
42. `test_export_rejected_records_audit`: Returns rejected row log with failure rationales.

### Module 08: Explainable AI (`test_explainable_ai.py`)
43. `test_explainability_analysis_success`: Trains RandomForest and calculates global feature importances.
44. `test_explainability_foreign_dataset_rejected`: Prevents cross-application dataset model training.

### Module 09: Privacy Guard (`test_privacy_guard.py`)
45. `test_privacy_scan_detects_pii_entities`: Flags email, phone, and national ID patterns.
46. `test_privacy_scan_foreign_dataset_rejected`: Cross-application privacy scans blocked with HTTP 400.

### Module 10: Green AI Monitor (`test_green_ai.py`)
47. `test_list_emission_regions_directory`: Returns regional carbon grid factors.
48. `test_sustainability_calculation_standard_grid`: Computes power draw $\times$ runtime $\times$ grid factor.
49. `test_sustainability_calculation_custom_override`: Custom emission factor override is respected.

### Module 11: Universal Risk Intelligence Engine (`test_risk_engine.py`)
50. `test_risk_scoring_contextual_scaling`: Proves contextual severity scaling (Automotive Medium vs Health Critical).
51. `test_evidence_attribution_rules`: Verifies evidence attribution labels adhere to verification status.
52. `test_duplicate_risk_prevention`: Duplicate assessment answers do not create duplicate risk entries.
53. `test_list_risks_endpoint`: Scopes risk retrieval to active application.
54. `test_manual_risk_registration`: Enables manual risk logging with multi-factor risk scoring.

### Module 12: Risk Lifecycle Management (`test_risk_lifecycle.py`)
55. `test_risk_lifecycle_transitions_and_audit_history`: State machine transitions with immutable history log.
56. `test_risk_regression_reopens_resolved_risk`: New assessment failure reopens previously resolved risk.

### Module 13: AI Recommendations (`test_recommendations.py`)
57. `test_recommendation_context_aware_and_technology_neutral`: Enforces technology neutrality (no Redis/K8s/AWS).
58. `test_recommendation_incomplete_profile_explicit_missing_context`: Incomplete context explicitly stated.
59. `test_list_recommendations_endpoint`: Scoped listing of action recommendations.

### Module 14: Reports & PDF Generation (`test_reports.py`)
60. `test_generate_pdf_report_success`: Compiles ReportLab PDF with executive score cards.
61. `test_generate_pdf_with_query_token_fallback`: Supports download query token authentication.
62. `test_cross_tenant_pdf_access_rejected`: Cross-tenant report download attempts rejected with HTTP 403.
63. `test_non_existent_assessment_pdf_returns_404`: Non-existent assessment report returns HTTP 404.

### Module 15: Assessment History (`test_assessment_history.py`)
64. `test_assessment_history_listing_and_order`: Chronological listing of historical assessment scores.
65. `test_assessment_history_tenant_isolation`: Historical records isolated between distinct tenants.

### Module 16: Settings & Demo Workspace (`test_settings.py`)
66. `test_health_check_endpoints`: Health check verifies database connectivity and returns healthy status.
67. `test_demo_workspace_seeding_creates_primary_records`: Seeds isolated baseline demo workspace.
68. `test_settings_profile_update`: Modifies business profile metadata.

### System & Security Suites (18 Tests)
69. `test_tenant_cannot_read_foreign_business_profile`: Proves tenant boundary on business profile.
70. `test_tenant_cannot_list_foreign_applications`: Prevents enumeration of foreign AI applications.
71. `test_tenant_cannot_access_foreign_assessment`: Cross-tenant assessment access blocked.
72. `test_tenant_cannot_access_foreign_dataset`: Cross-tenant dataset access blocked.
73. `test_tenant_cannot_download_foreign_pdf_report`: Cross-tenant PDF download blocked.
74. `test_shared_demo_workspace_coexistence`: Both tenants can access demo workspace without data leakage.
75. `test_records_persist_across_fresh_database_session`: Relational persistence across separate sessions.
76. `test_relational_hierarchy_persistence`: Multi-tier relational cascade integrity.
77. `test_transaction_rollback_on_failure`: Integrity error rolls back cleanly.
78. `test_missing_body_in_post_returns_422`: Schema validation on missing body.
79. `test_invalid_type_in_path_parameter_returns_422`: Type validation on path parameters.
80. `test_non_existent_resource_returns_404`: 404 on missing endpoints.
81. `test_out_of_scope_modules_return_404`: Prohibited BI/growth endpoints return 404.
82. `test_sql_injection_defense_in_route_parameters`: SQL injection payloads safely escaped.
83. `test_xss_sanitization_in_user_inputs`: XSS script tags stored without script execution.
84. `test_csrf_token_verification_on_mutations`: State-changing requests enforce CSRF tokens.
85. `test_rate_limiting_enforcement_on_sensitive_routes`: Rate limiting triggers 429 on abuse.
86. `test_unauthenticated_requests_rejected`: Unauthenticated requests to protected endpoints return 401.

---

## Part 2: Frontend Node.js Test Cases (29 Tests)

- **Suite 1: File Inventory (2 tests)**: Verifies all 15 page files and 5 core infrastructure files exist and export components.
- **Suite 2: Router Configuration (3 tests)**: Verifies all 16 governance paths are mounted in `App.tsx`, confirms zero BI routes exist, and tests wildcard fallback.
- **Suite 3: Navigation Bar (2 tests)**: Verifies 13 sidebar links match governance modules and checks dynamic risk badge count.
- **Suite 4: API URL Normalization (5 tests)**: Verifies `/api` trailing slash, missing slash, and duplicate handling.
- **Suite 5: Form Validation (5 tests)**: Verifies RFC 5322 email regex, 6-digit OTP regex, and CSV/JSON extension filters.
- **Suite 6: Analytical Formulas (2 tests)**: Verifies Green AI $E = P \times t$, $CO_2e$, car miles, and 80% four-fifths rule.
- **Suite 7: Security Transport (3 tests)**: Verifies `credentials: "include"`, CSRF header injection, and Bearer token fallback.

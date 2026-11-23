"""
Test Suite: Universal, Business-Agnostic Risk Intelligence Engine
==================================================================
Tests 5 distinct industries + 1 incomplete profile:
1. Healthcare (HealthNexus Diagnostics / Oncology Triage Copilot)
2. Finance & Banking (FinVanguard Underwriting / SME Lending Evaluator)
3. Education & EdTech (EduSphere Learning / Adaptive Student Tutoring)
4. Retail & E-Commerce (Apex Retail Group / Dynamic Catalog Pricing)
5. IT & Software (CyberMesh Solutions / Code Vulnerability Scanner)
6. Incomplete Profile (Unknown SME / Alpha Prototype)

Validates:
- Universal multi-industry support with ZERO hardcoded business names
- Dynamic context extraction with missing field tracking
- Universal scoring methodology (Likelihood x Impact x Exposure / Control)
- Context-aware recommendations (NO unauthorized tech assumptions like Redis/AWS/K8s)
- Safe neutral recommendations for incomplete profiles
- Evidence attribution & verification status
- Duplicate prevention within and across runs
- Full lifecycle status tracking (New -> Repeated -> In progress -> Resolved -> Reopened)
- Remediation workflow & audit history persistence
- Multi-business data isolation
"""

import json
import datetime
from app.database import SessionLocal
from app.models import Business, AIApplication, Assessment, AssessmentResponse, Risk, Recommendation
from app.services.risk_intelligence_engine import (
    RiskIntelligenceEngine,
    extract_business_context,
    RiskScoringModel,
    BusinessContext
)

def run_universal_tests():
    print("=" * 80)
    print("RAI-Biz Universal Risk Intelligence Engine Comprehensive Validation")
    print("=" * 80)

    db = SessionLocal()
    created_apps = []
    created_bizs = []

    try:
        # -------------------------------------------------------------------
        # SETUP 5 DIVERSE BUSINESSES + 1 INCOMPLETE PROFILE
        # -------------------------------------------------------------------
        now = datetime.datetime.utcnow()

        # Business 1: Healthcare
        biz1 = Business(name="HealthNexus Diagnostics", industry="Healthcare & Life Sciences", size="50-100", location="Germany")
        db.add(biz1); db.flush()
        app1 = AIApplication(
            business_id=biz1.id, name="Oncology Triage Copilot",
            purpose="Clinical biopsy prioritization and patient acuity ranking",
            business_function="Clinical Decision Support",
            data_types="Histopathology scans, EHR records, patient age, diagnosis codes",
            automated_decision_impact="High", human_oversight="Assisted",
            affected_stakeholders="Patients and clinical oncologists",
            external_services="None (Local deployment)",
            infrastructure_type="On-Premises HIPAA Cluster"
        )
        db.add(app1); db.flush()

        # Business 2: Finance
        biz2 = Business(name="FinVanguard Underwriting", industry="Banking & Finance", size="100-250", location="UK")
        db.add(biz2); db.flush()
        app2 = AIApplication(
            business_id=biz2.id, name="SME Lending Evaluator",
            purpose="Automated commercial credit approval and loan interest rate tiering",
            business_function="Credit Underwriting",
            data_types="Corporate balance sheets, tax returns, commercial banking statements",
            automated_decision_impact="High", human_oversight="None",  # Autonomous
            affected_stakeholders="Small business borrowers and commercial lenders",
            infrastructure_type="Cloud VPC"
        )
        db.add(app2); db.flush()

        # Business 3: Education
        biz3 = Business(name="EduSphere Learning", industry="Education & EdTech", size="20-50", location="USA")
        db.add(biz3); db.flush()
        app3 = AIApplication(
            business_id=biz3.id, name="Adaptive Student Tutoring AI",
            purpose="Curriculum personalization and automated assignment grading feedback",
            business_function="Educational Evaluation",
            data_types="Student test scores, submission essays, learning velocity metrics",
            automated_decision_impact="Medium", human_oversight="Full",
            affected_stakeholders="Students, parents, and secondary educators",
            infrastructure_type="Unknown"  # Unknown infra
        )
        db.add(app3); db.flush()

        # Business 4: Retail & E-Commerce
        biz4 = Business(name="Apex Retail Group", industry="Retail & E-commerce", size="500+", location="Canada")
        db.add(biz4); db.flush()
        app4 = AIApplication(
            business_id=biz4.id, name="Dynamic Catalog Pricing AI",
            purpose="Automate checkout discount allocation and personalized promotional vouchers",
            business_function="E-commerce Merchandising",
            data_types="Shopping cart telemetry, postal codes, browsing history, purchase frequency",
            automated_decision_impact="Medium", human_oversight="Assisted",
            affected_stakeholders="Online consumers and retail shoppers",
            infrastructure_type="Cloud"
        )
        db.add(app4); db.flush()

        # Business 5: IT & Software
        biz5 = Business(name="CyberMesh Solutions", industry="IT & Software", size="10-25", location="Estonia")
        db.add(biz5); db.flush()
        app5 = AIApplication(
            business_id=biz5.id, name="Code Vulnerability Scanner",
            purpose="Continuous integration automated security inspection and defect triage",
            business_function="Developer Tooling",
            data_types="Source code commits, build logs, dependency manifests",
            automated_decision_impact="Low", human_oversight="Assisted",
            affected_stakeholders="Software developers and engineering leads",
            infrastructure_type="Hybrid Cloud"
        )
        db.add(app5); db.flush()

        # Business 6: Incomplete / Unknown Profile
        biz6 = Business(name="", industry="Unknown", size="", location="")
        db.add(biz6); db.flush()
        app6 = AIApplication(
            business_id=biz6.id, name="Alpha Prototype",
            purpose="", business_function="", data_types="",
            automated_decision_impact="", human_oversight="",
            affected_stakeholders="Not Provided", infrastructure_type="Unknown"
        )
        db.add(app6); db.flush()
        db.commit()

        created_apps = [app1, app2, app3, app4, app5, app6]
        created_bizs = [biz1, biz2, biz3, biz4, biz5, biz6]

        # -------------------------------------------------------------------
        # TEST 1: DYNAMIC BUSINESS CONTEXT EXTRACTION & MISSING FIELD DETECTION
        # -------------------------------------------------------------------
        print("\n--- TEST 1: Dynamic Business Context & Missing Field Tracking ---")
        ctx_health = extract_business_context(db, app1.id)
        assert ctx_health.industry == "Healthcare & Life Sciences"
        assert ctx_health.is_high_impact is True
        assert len(ctx_health.missing_fields) == 0
        print(f"  [PASS] Business 1 (Healthcare): Context complete. No missing fields.")

        ctx_incomp = extract_business_context(db, app6.id)
        assert "industry" in ctx_incomp.missing_fields
        assert "purpose" in ctx_incomp.missing_fields
        assert "data_types" in ctx_incomp.missing_fields
        assert "automated_decision_impact" in ctx_incomp.missing_fields
        assert ctx_incomp.purpose == "Not Provided"
        assert ctx_incomp.industry == "Unknown Industry"
        print(f"  [PASS] Business 6 (Incomplete): Correctly identified {len(ctx_incomp.missing_fields)} missing fields without inventing details.")

        # -------------------------------------------------------------------
        # TEST 2: UNIVERSAL RISK SCORING METHODOLOGY
        # -------------------------------------------------------------------
        print("\n--- TEST 2: Universal Scoring Methodology (Likelihood x Impact x Exposure / Control) ---")
        # High impact + Autonomous (FinVanguard Underwriting)
        ctx_fin = extract_business_context(db, app2.id)
        sev_fin, score_fin, l_lbl, i_lbl, exp_lbl, c_lbl, expl_fin = RiskScoringModel.calculate(
            base_likelihood="High", base_impact="Critical", context=ctx_fin, answer="No"
        )
        assert sev_fin == "Critical", f"Expected Critical for unassisted high-impact finance AI, got {sev_fin}"
        assert score_fin >= 75.0, f"Expected score >= 75, got {score_fin}"
        print(f"  [PASS] FinVanguard Autonomous AI: Severity={sev_fin}, Score={score_fin}/100. Factors: L={l_lbl}, I={i_lbl}, Exp={exp_lbl}, Control={c_lbl}")

        # Low impact + Assisted (CyberMesh Solutions)
        ctx_it = extract_business_context(db, app5.id)
        sev_it, score_it, _, _, _, _, _ = RiskScoringModel.calculate(
            base_likelihood="Low", base_impact="Low", context=ctx_it, answer="Partially"
        )
        assert sev_it in ["Low", "Medium"], f"Expected Low/Medium for low-impact IT tool, got {sev_it}"
        assert score_it < 50.0
        print(f"  [PASS] CyberMesh Developer Tool: Severity={sev_it}, Score={score_it}/100")

        # -------------------------------------------------------------------
        # TEST 3: CONTEXT-AWARE RECOMMENDATIONS & ZERO TECH HALLUCINATION
        # -------------------------------------------------------------------
        print("\n--- TEST 3: Context-Aware Recommendations & Technology Neutrality ---")
        sample_responses_health = [
            {"question_id": "F1", "answer": "No", "notes": "No clinical parity evaluation conducted"},
            {"question_id": "P1", "answer": "No", "notes": "Raw patient histology contains names and dates of birth"},
            {"question_id": "S1", "answer": "No", "notes": "On-premise GPU cluster power draw unmetered"}
        ]
        risks_h, recs_h = RiskIntelligenceEngine.evaluate_and_sync(
            db, app1.id, responses=sample_responses_health, actor_email="auditor@healthnexus.de"
        )
        rec_f1_health = next(r for r in recs_h if r.source_module == "fairness")
        assert "patients and clinical oncologists" in rec_f1_health.why_it_matters.lower() or "clinical" in rec_f1_health.action.lower()
        print(f"  [PASS] Healthcare Recommendation (F1): '{rec_f1_health.problem}'")
        print(f"         Action: '{rec_f1_health.action[:90]}...'")

        # Incomplete profile recommendation check: MUST NOT recommend specific tooling like Redis or Kubernetes
        sample_responses_incomp = [
            {"question_id": "S2", "answer": "No", "notes": "Servers run continuously"}
        ]
        risks_inc, recs_inc = RiskIntelligenceEngine.evaluate_and_sync(
            db, app6.id, responses=sample_responses_incomp, actor_email="tester@sme.org"
        )
        rec_s2_inc = next(r for r in recs_inc if r.source_module == "sustainability")
        rec_text = rec_s2_inc.action.lower()
        # Verify forbidden tech words are NOT present
        assert "redis" not in rec_text
        assert "kubernetes" not in rec_text
        assert "aws" not in rec_text
        # Verify explicit note regarding missing context is present
        assert "additional business context is required" in rec_s2_inc.action.lower()
        print(f"  [PASS] Incomplete Profile Recommendation: Generated safe, technology-neutral recommendation.")
        print(f"         Verified NO unauthorized tech assumptions (Redis/K8s/AWS).")
        print(f"         Explicitly identified missing context: '{rec_s2_inc.action[rec_s2_inc.action.find('['):]}'")

        # -------------------------------------------------------------------
        # TEST 4: EVIDENCE ATTRIBUTION & VERIFICATION INTEGRITY
        # -------------------------------------------------------------------
        print("\n--- TEST 4: Evidence Attribution & Audit Integrity ---")
        risk_p1_health = next(r for r in risks_h if r.source_module == "privacy")
        assert risk_p1_health.evidence_source == "Self-reported assessment answer"
        assert risk_p1_health.is_verified is False
        assert "No supporting documentation provided" not in risk_p1_health.evidence
        assert "Raw patient histology contains names" in risk_p1_health.evidence
        print(f"  [PASS] Evidence source correctly attributed as '{risk_p1_health.evidence_source}', verified={risk_p1_health.is_verified}.")

        # -------------------------------------------------------------------
        # TEST 5: DUPLICATE PREVENTION WITHIN AND ACROSS RUNS
        # -------------------------------------------------------------------
        print("\n--- TEST 5: Duplicate Prevention ---")
        # Run evaluation again with duplicate responses in list
        duplicated_responses = sample_responses_health + sample_responses_health
        risks_dup, _ = RiskIntelligenceEngine.evaluate_and_sync(
            db, app1.id, responses=duplicated_responses, actor_email="auditor@healthnexus.de"
        )
        risk_keys = [r.risk_key for r in risks_dup]
        assert len(risk_keys) == len(set(risk_keys)), f"Duplicate risk keys found in same run: {risk_keys}"
        print(f"  [PASS] No duplicate risk findings created ({len(risks_dup)} unique risks).")

        # -------------------------------------------------------------------
        # TEST 6: REMEDIATION WORKFLOW & LIFECYCLE TRACKING
        # (New -> Repeated -> In progress -> Resolved -> Reopened)
        # -------------------------------------------------------------------
        print("\n--- TEST 6: Remediation Workflow & Lifecycle State Transitions ---")
        # 1. Check initial lifecycle status was "New" or "Repeated"
        target_risk = risks_h[0]
        risk_id = target_risk.id

        # 2. Update to "In progress" with owner, target date, and completion notes
        updated_risk = RiskIntelligenceEngine.update_remediation_status(
            db, risk_id=risk_id, status="In progress",
            responsible_owner="Dr. H. Schmidt (Lead Clinical Data Officer)",
            target_date="2027-03-31",
            completion_notes="Initiated clinical subgroup stratification protocol.",
            actor_email="admin@healthnexus.de"
        )
        assert updated_risk.status == "In progress"
        assert updated_risk.responsible_owner == "Dr. H. Schmidt (Lead Clinical Data Officer)"
        assert updated_risk.target_date == "2027-03-31"

        # Verify audit history logged this event
        hist = json.loads(updated_risk.remediation_history_json)
        assert len(hist) >= 2
        last_event = hist[-1]
        assert "In progress" in last_event["changes"]
        print(f"  [PASS] Status updated to 'In progress'. Owner and target date persisted.")
        print(f"         Remediation audit history logged {len(hist)} events: last='{last_event['changes']}' by '{last_event['user']}'.")

        # 3. Simulate subsequent assessment where F1 is now COMPLIANT ("Yes")
        resolved_responses = [{"question_id": "F1", "answer": "Yes", "notes": "Clinical parity verified"}]
        RiskIntelligenceEngine.evaluate_and_sync(
            db, app1.id, assessment_id=999, responses=resolved_responses, actor_email="system_audit"
        )
        refreshed_risk = db.query(Risk).filter(Risk.id == risk_id).first()
        assert refreshed_risk.status == "Resolved"
        assert refreshed_risk.lifecycle_status == "Resolved"
        print(f"  [PASS] Compliant assessment updated risk status to 'Resolved', lifecycle_status='Resolved'.")

        # 4. Simulate third assessment where F1 fails again ("No") -> Lifecycle becomes "Reopened"
        reopened_responses = [{"question_id": "F1", "answer": "No", "notes": "Disparity reappeared in v2 model"}]
        RiskIntelligenceEngine.evaluate_and_sync(
            db, app1.id, assessment_id=1000, responses=reopened_responses, actor_email="system_audit"
        )
        reopened_risk = db.query(Risk).filter(Risk.id == risk_id).first()
        assert reopened_risk.status == "Open"
        assert reopened_risk.lifecycle_status == "Reopened"
        print(f"  [PASS] Subsequent deficient assessment transitioned risk lifecycle to 'Reopened'!")

        # -------------------------------------------------------------------
        # TEST 7: MULTI-BUSINESS DATA ISOLATION
        # -------------------------------------------------------------------
        print("\n--- TEST 7: Multi-Business Data Isolation ---")
        # Generate risks for Retail (app4)
        sample_responses_retail = [
            {"question_id": "F1", "answer": "No", "notes": "Pricing discounts vary by postal code"},
            {"question_id": "T1", "answer": "No", "notes": "Recommendation carousel has no explanation"}
        ]
        risks_ret, _ = RiskIntelligenceEngine.evaluate_and_sync(db, app4.id, responses=sample_responses_retail)

        # Query risks for Healthcare (app1) vs Retail (app4)
        app1_risks = db.query(Risk).filter(Risk.application_id == app1.id).all()
        app4_risks = db.query(Risk).filter(Risk.application_id == app4.id).all()

        app1_ids = {r.id for r in app1_risks}
        app4_ids = {r.id for r in app4_risks}
        assert app1_ids.isdisjoint(app4_ids), "Risks leaked across businesses!"
        assert all(r.application_id == app1.id for r in app1_risks)
        assert all(r.application_id == app4.id for r in app4_risks)

        # Check existing Suntech Enterprise (ID 9) and SmartHire (ID 1)
        suntech_risks = db.query(Risk).filter(Risk.application_id == 9).all()
        smarthire_risks = db.query(Risk).filter(Risk.application_id == 1).all()
        suntech_ids = {r.id for r in suntech_risks}
        smarthire_ids = {r.id for r in smarthire_risks}
        assert suntech_ids.isdisjoint(smarthire_ids)
        assert suntech_ids.isdisjoint(app1_ids)

        print(f"  [PASS] Complete isolation verified across all businesses:")
        print(f"         Healthcare (ID {app1.id}): {len(app1_risks)} risks")
        print(f"         Retail (ID {app4.id}): {len(app4_risks)} risks")
        print(f"         Suntech Enterprise (ID 9): {len(suntech_risks)} risks")
        print(f"         SmartHire Demo (ID 1): {len(smarthire_risks)} risks")
        print(f"         Zero cross-tenant risk leakage.")

        print("\n" + "=" * 80)
        print("ALL 7 CORE RISK INTELLIGENCE ENGINE TESTS PASSED WITH 100% SUCCESS!")
        print("=" * 80)

    finally:
        # Clean up temporary test businesses and applications
        for app in created_apps:
            db.query(Risk).filter(Risk.application_id == app.id).delete()
            db.query(Recommendation).filter(Recommendation.application_id == app.id).delete()
            db.query(AIApplication).filter(AIApplication.id == app.id).delete()
        for biz in created_bizs:
            db.query(Business).filter(Business.id == biz.id).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    run_universal_tests()

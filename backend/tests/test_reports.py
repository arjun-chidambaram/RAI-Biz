"""
Module 14: Reports & PDF Generation Test Suite
==============================================
Covers:
- Executive PDF governance audit report generation
- Validation of valid %PDF binary stream and content headers
- Dual-mode authentication (Bearer header + query parameter token)
- Cross-tenant PDF download prevention (HTTP 403)
- Non-existent assessment ID error handling (HTTP 404)
"""

import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Assessment

def test_generate_pdf_report_success(auth_client_a: TestClient, tenant_a, db: Session):
    """Verifies generating an executive PDF returns application/pdf with %PDF magic header."""
    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id
    now = datetime.datetime.utcnow()

    assessment = Assessment(
        business_id=biz_id,
        application_id=app_id,
        name="Executive Audit PDF Target",
        overall_score=92.5,
        fairness_score=95.0,
        transparency_score=90.0,
        privacy_score=90.0,
        sustainability_score=95.0,
        is_current=True,
        completed_at=now
    )
    db.add(assessment)
    db.commit()

    res = auth_client_a.get(f"/api/reports/{assessment.id}")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "attachment" in res.headers["content-disposition"]
    # Check %PDF binary magic bytes
    assert res.content.startswith(b"%PDF")
    assert len(res.content) > 1000

def test_generate_pdf_with_query_token_fallback(client: TestClient, tenant_a, db: Session):
    """Verifies browser tab download via ?token=<token> fallback authenticates successfully."""
    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id

    assessment = Assessment(
        business_id=biz_id,
        application_id=app_id,
        name="Browser Tab Query Token Target",
        overall_score=88.0,
        fairness_score=90.0,
        transparency_score=85.0,
        privacy_score=85.0,
        sustainability_score=92.0,
        is_current=True,
        completed_at=datetime.datetime.utcnow()
    )
    db.add(assessment)
    db.commit()

    # Request without headers or cookies, but with ?token=
    res = client.get(f"/api/reports/{assessment.id}?token={tenant_a['token']}")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")

def test_cross_tenant_pdf_access_rejected(auth_client_b: TestClient, tenant_a, db: Session):
    """Verifies Tenant B cannot download Tenant A's private assessment report (HTTP 403)."""
    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id

    private_assessment = Assessment(
        business_id=biz_id,
        application_id=app_id,
        name="Confidential Automotive Report",
        overall_score=75.0,
        fairness_score=80.0,
        transparency_score=70.0,
        privacy_score=70.0,
        sustainability_score=80.0,
        completed_at=datetime.datetime.utcnow()
    )
    db.add(private_assessment)
    db.commit()

    # Tenant B tries to access Tenant A's PDF
    res = auth_client_b.get(f"/api/reports/{private_assessment.id}")
    assert res.status_code == 403

def test_pdf_report_non_existent_assessment_returns_404(auth_client_a: TestClient):
    """Verifies requesting non-existent assessment returns HTTP 404."""
    res = auth_client_a.get("/api/reports/999999")
    assert res.status_code == 404

def test_pdf_report_no_raw_html_tags_and_text_wrapping(auth_client_a: TestClient, tenant_a, db: Session):
    """
    Verifies that PDF generation:
    1. Never renders raw HTML tags (<b>, </b>, <br/>, etc.).
    2. Wraps long recommendation actions and risk impacts cleanly across columns.
    3. Handles bare ampersands (&) and angle brackets (<, >) safely.
    4. Includes running page numbers (Page X of Y) and repeating table headers.
    """
    import io
    import pypdf
    from app.models import Risk, Recommendation, FairnessResult

    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id
    now = datetime.datetime.now(datetime.timezone.utc)

    assessment = Assessment(
        business_id=biz_id,
        application_id=app_id,
        name="Long Formatting Validation Assessment",
        overall_score=72.5,
        fairness_score=65.0,
        transparency_score=70.0,
        privacy_score=75.0,
        sustainability_score=80.0,
        is_current=True,
        completed_at=now
    )
    db.add(assessment)
    db.commit()

    fairness = FairnessResult(
        application_id=app_id,
        assessment_id=assessment.id,
        sensitive_attribute="customer_gender",
        target_attribute="service_approved",
        favorable_outcome="1",
        demographic_parity_diff=0.185,
        demographic_parity_ratio=0.742,
        equal_opportunity_diff=0.120,
        group_metrics_json='[]',
        risk_level="High"
    )
    db.add(fairness)

    # Add multiple detailed risks with long business impacts and mixed HTML/markdown
    for i in range(8):
        risk = Risk(
            application_id=app_id,
            assessment_id=assessment.id,
            title=f"Risk #{i+1}: Demographic Disparity & Statistical Bias in Model Selection (R&D Group)",
            description=f"Detailed risk analysis explaining that accuracy < 70% and threshold > 0.8 creates disparate impact.",
            source_module="fairness",
            severity="Critical" if i < 2 else ("High" if i < 5 else "Medium"),
            evidence=f"Empirical Four-Fifths ratio 0.742 < 0.80 benchmark. Calculated on {1000 + i*50} candidate samples.",
            business_impact=f"Potential class-action exposure under Title VII & NYC Local Law 144. Disproportionate exclusion rate for female applicants in technical roles with experience > 5 years.",
            recommended_action=f"Apply Fairlearn threshold optimizer constraints during model inference to eliminate selection gap.",
            status="Open" if i % 2 == 0 else "In progress",
            risk_score=88 - i * 5,
            evidence_source="Measured fairness audit dataset",
            is_verified=True,
            lifecycle_status="New"
        )
        db.add(risk)

    # Add recommendations with bold tags, line breaks, ampersands, and long text
    for j in range(6):
        rec = Recommendation(
            application_id=app_id,
            problem=f"<b>Deficiency #{j+1}:</b> Critical disparity in R&D recruitment pipeline with ratio < 0.80",
            why_it_matters=f"Regulatory non-compliance with EEOC guidelines & potential statutory fines exceeding $150,000.",
            action=f"Deploy Fairlearn threshold optimizer with <b>strict parity constraint</b>.<br/>Implement weekly automated parity drift alerts for HR & Compliance teams.",
            priority="High" if j < 3 else "Medium",
            expected_business_benefit=f"Eliminates disparate impact liability, improves workforce diversity by 25%, and ensures audit-readiness under EU AI Act.",
            responsible_team="Engineering & Legal",
            status="Open",
            source_module="fairness"
        )
        db.add(rec)

    db.commit()

    res = auth_client_a.get(f"/api/reports/{assessment.id}")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")

    reader = pypdf.PdfReader(io.BytesIO(res.content))
    total_pages = len(reader.pages)
    assert total_pages >= 2

    all_text = ""
    for p_num, page in enumerate(reader.pages):
        page_text = page.extract_text()
        all_text += "\n" + page_text

        # Verify NO raw HTML tags are drawn as literal characters
        for forbidden_tag in ["<b>", "</b>", "<br>", "<br/>", "<strong>", "</strong>", "<em>", "</em>", "</p>", "<div>"]:
            assert forbidden_tag not in page_text, f"Found raw HTML tag '{forbidden_tag}' on page {p_num + 1}!"

        # Verify running footer on each page
        assert "CONFIDENTIAL & PROPRIETARY" in page_text
        assert f"Page {p_num + 1} of {total_pages}" in page_text

    # Verify content was preserved and wrapped rather than truncated
    assert "Demographic Disparity & Bias Exposure" in all_text or "Deficiency #1" in all_text
    assert "Engineering & Legal" in all_text
    assert "Fairlearn threshold optimizer" in all_text


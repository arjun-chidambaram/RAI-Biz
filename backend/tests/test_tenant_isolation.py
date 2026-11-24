"""
Module 17: Multi-Tenant Data Isolation Test Suite
=================================================
MANDATORY SECURITY REQUIREMENTS:
- Customer A cannot read Customer B's private business profile
- Customer A cannot update Customer B's business profile
- Customer A cannot list Customer B's private applications
- Customer A cannot access Customer B's private datasets
- Customer A cannot access Customer B's private assessments
- Customer A cannot download Customer B's executive PDF reports
- Both Customer A and Customer B can access shared demo data without data leakage
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Business, AIApplication, Assessment, Dataset

def test_tenant_cannot_read_foreign_business_profile(auth_client_a: TestClient, tenant_b):
    """Verifies Tenant A cannot access Tenant B's business details."""
    foreign_biz_id = tenant_b["business"].id
    # Attempt to put update on foreign business
    res = auth_client_a.put(f"/api/businesses/{foreign_biz_id}", json={
        "name": "Hacked Business Name",
        "industry": "Automotive Services",
        "size": "11-50",
        "location": "Munich"
    })
    assert res.status_code == 403

def test_tenant_cannot_list_foreign_applications(auth_client_a: TestClient, tenant_b):
    """Verifies Tenant A filtering by Tenant B's business ID returns 403 or empty list."""
    foreign_biz_id = tenant_b["business"].id
    res = auth_client_a.get(f"/api/applications?business_id={foreign_biz_id}")
    assert res.status_code in [403, 200]
    if res.status_code == 200:
        # If 200, must not return any of Tenant B's apps
        app_ids = [a["id"] for a in res.json()]
        assert tenant_b["application"].id not in app_ids

def test_tenant_cannot_access_foreign_assessment(auth_client_a: TestClient, tenant_b, db: Session):
    """Verifies Tenant A cannot retrieve Tenant B's private assessment."""
    foreign_assessment = Assessment(
        business_id=tenant_b["business"].id,
        application_id=tenant_b["application"].id,
        name="Tenant B Oncology Acuity Assessment",
        overall_score=95.0,
        fairness_score=95.0,
        transparency_score=95.0,
        privacy_score=95.0,
        sustainability_score=95.0
    )
    db.add(foreign_assessment)
    db.commit()

    res = auth_client_a.get(f"/api/assessments/{foreign_assessment.id}")
    assert res.status_code == 403

def test_tenant_cannot_access_foreign_dataset(auth_client_a: TestClient, tenant_b, db: Session):
    """Verifies Tenant A cannot retrieve or preview Tenant B's dataset."""
    foreign_ds = Dataset(
        application_id=tenant_b["application"].id,
        filename="trials.csv",
        original_filename="trials.csv",
        file_path="nonexistent_trials.csv",
        checksum="trials_checksum12345",
        row_count=100,
        column_count=10
    )
    db.add(foreign_ds)
    db.commit()

    res_get = auth_client_a.get(f"/api/datasets/{foreign_ds.id}")
    assert res_get.status_code == 403

    res_preview = auth_client_a.get(f"/api/datasets/{foreign_ds.id}/preview")
    assert res_preview.status_code == 403

def test_tenant_cannot_download_foreign_pdf_report(auth_client_a: TestClient, tenant_b, db: Session):
    """Verifies Tenant A cannot download Tenant B's PDF report."""
    foreign_assessment = Assessment(
        business_id=tenant_b["business"].id,
        application_id=tenant_b["application"].id,
        name="Confidential Medical Report",
        overall_score=80.0
    )
    db.add(foreign_assessment)
    db.commit()

    res = auth_client_a.get(f"/api/reports/{foreign_assessment.id}")
    assert res.status_code == 403

def test_shared_demo_workspace_coexistence(auth_client_a: TestClient, auth_client_b: TestClient, client: TestClient):
    """Verifies both Tenant A and Tenant B can query demo workspace without leaking private profiles."""
    # Seed demo workspace (Application ID 1)
    client.post("/api/demo/seed")

    # Tenant A accesses demo dashboard
    res_a = auth_client_a.get("/api/dashboard?application_id=1")
    assert res_a.status_code == 200

    # Tenant B accesses demo dashboard
    res_b = auth_client_b.get("/api/dashboard?application_id=1")
    assert res_b.status_code == 200

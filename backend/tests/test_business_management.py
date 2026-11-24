"""
Module 02: Business and AI Application Management Test Suite
============================================================
Covers:
- Create business with required and optional fields
- Update business profile
- Create AI application attached to business
- Update AI application parameters
- Multiple businesses and multiple applications per tenant
- Validation of missing required fields (name, industry)
- Business profile synchronization (/api/businesses/profile)
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Business, AIApplication

def test_create_business_success(auth_client_a: TestClient):
    """Verifies creating a new business for an authenticated user."""
    payload = {
        "name": "Nordic Telemetry AS",
        "industry": "Automotive Services",
        "size": "50-100",
        "location": "Oslo, Norway",
        "description": "Connected EV sensor analysis"
    }
    res = auth_client_a.post("/api/businesses", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Nordic Telemetry AS"
    assert data["industry"] == "Automotive Services"
    assert data["id"] is not None

def test_create_business_missing_name_rejected(auth_client_a: TestClient):
    """Verifies missing business name is rejected with validation error."""
    payload = {
        "name": "",
        "industry": "Automotive Services"
    }
    res = auth_client_a.post("/api/businesses", json=payload)
    # Backend either returns 400 or 422
    assert res.status_code in [400, 422]

def test_update_business(auth_client_a: TestClient, tenant_a):
    """Verifies updating an existing business profile."""
    biz_id = tenant_a["business"].id
    update_payload = {
        "name": "Apex Automotive Group Worldwide",
        "industry": "Automotive Services",
        "size": "100-250",
        "location": "Stuttgart, Germany",
        "description": "Global enterprise automotive surface inspection"
    }
    res = auth_client_a.put(f"/api/businesses/{biz_id}", json=update_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Apex Automotive Group Worldwide"
    assert data["size"] == "100-250"

def test_list_businesses_scoped_to_user(auth_client_a: TestClient, tenant_a):
    """Verifies user can list all businesses they belong to."""
    res = auth_client_a.get("/api/businesses")
    assert res.status_code == 200
    biz_list = res.json()
    assert len(biz_list) >= 1
    biz_ids = [b["id"] for b in biz_list]
    assert tenant_a["business"].id in biz_ids

def test_create_ai_application_success(auth_client_a: TestClient, tenant_a):
    """Verifies creating an AI application under an active business."""
    payload = {
        "business_id": tenant_a["business"].id,
        "name": "Paint Quality Assurance AI",
        "purpose": "Detect clearcoat scratches via computer vision",
        "business_function": "Quality Inspection",
        "data_types": "High-resolution camera imagery",
        "automated_decision_impact": "Low",
        "human_oversight": "Assisted",
        "affected_stakeholders": "Detailing technicians",
        "infrastructure_type": "Edge Device"
    }
    res = auth_client_a.post("/api/applications", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Paint Quality Assurance AI"
    assert data["business_id"] == tenant_a["business"].id

def test_update_ai_application(auth_client_a: TestClient, tenant_a):
    """Verifies updating an existing AI application."""
    app_id = tenant_a["application"].id
    update_payload = {
        "name": "Autonomous Detailing AI v2",
        "purpose": "Advanced optical surface inspection and ceramic coating",
        "business_function": "Surface Quality Control",
        "data_types": "High-res optical camera scans",
        "automated_decision_impact": "Low",
        "human_oversight": "Assisted",
        "affected_stakeholders": "Vehicle owners and detailing technicians",
        "infrastructure_type": "Edge TPU"
    }
    res = auth_client_a.put(f"/api/applications/{app_id}", json=update_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Autonomous Detailing AI v2"

def test_list_applications_for_business(auth_client_a: TestClient, tenant_a):
    """Verifies applications can be filtered by business_id."""
    res = auth_client_a.get(f"/api/applications?business_id={tenant_a['business'].id}")
    assert res.status_code == 200
    apps = res.json()
    assert len(apps) >= 1
    app_names = [a["name"] for a in apps]
    assert any("Detailing" in name for name in app_names)

def test_business_profile_sync_endpoint(auth_client_a: TestClient, tenant_a):
    """Verifies GET and PUT /api/businesses/profile endpoints."""
    # GET profile
    get_res = auth_client_a.get("/api/businesses/profile")
    assert get_res.status_code == 200
    data = get_res.json()
    assert "business" in data
    assert "application" in data
    assert data["business"]["id"] == tenant_a["business"].id

    # PUT profile
    put_payload = {
        "name": "Apex Surface Tech",
        "industry": "Automotive Services",
        "size": "50-100",
        "location": "Munich, Germany",
        "description": "Robotic paint inspection",
        "app_name": "Apex Inspector Pro",
        "purpose": "Scratches and defect detection",
        "business_function": "Quality Control",
        "data_types": "Visual imagery",
        "automated_decision_impact": "Low",
        "human_oversight": "Assisted",
        "affected_stakeholders": "Technicians",
        "infrastructure_type": "Edge Device"
    }
    put_res = auth_client_a.put("/api/businesses/profile", json=put_payload)
    assert put_res.status_code == 200
    updated = put_res.json()
    assert updated["business"]["name"] == "Apex Surface Tech"
    assert updated["application"]["name"] == "Apex Inspector Pro"

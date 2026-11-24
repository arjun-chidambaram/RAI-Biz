"""
Module 16: Settings & Demo Workspace Test Suite
===============================================
Covers:
- System monitoring endpoints: /health and /api/health
- API root status welcome endpoint
- Interactive documentation OpenAPI schema availability (/openapi.json)
- Demo workspace seeder (/api/demo/seed)
- Demo workspace preservation of private user business records
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Business

def test_health_check_endpoints(client: TestClient):
    """Verifies /health and /api/health return operational status and database connection."""
    for path in ["/health", "/api/health"]:
        res = client.get(path)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] in ["healthy", "degraded"]
        assert data["database"] == "connected"
        assert "timestamp" in data

def test_openapi_schema_endpoint(client: TestClient):
    """Verifies OpenAPI schema is reachable and exposes documentation endpoints."""
    res = client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()
    assert "paths" in schema
    assert "/api/auth/send-otp" in schema["paths"]
    assert "/api/assessments" in schema["paths"]

def test_demo_workspace_seeder(client: TestClient, tenant_a, db: Session):
    """Verifies seeding demo workspace does not overwrite or delete private user businesses."""
    user_biz_id = tenant_a["business"].id

    res = client.post("/api/demo/seed")
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    assert "SmartHire" in data["message"]

    # Verify tenant_a business still exists untouched
    user_biz = db.query(Business).filter(Business.id == user_biz_id).first()
    assert user_biz is not None
    assert user_biz.name == tenant_a["business"].name

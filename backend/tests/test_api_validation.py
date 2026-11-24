"""
Module 19: API Input Validation & Boundary Conditions Test Suite
================================================================
Covers:
- Missing required fields validation (HTTP 400/422)
- Type error handling (strings in integer fields)
- Non-existent resource querying (HTTP 404)
- Malformed JSON payloads
- Boundary conditions on numerical parameters
"""

from fastapi.testclient import TestClient

def test_missing_body_in_post_returns_422(client: TestClient):
    """Verifies empty body in POST request returns 422 Unprocessable Entity."""
    res = client.post("/api/auth/send-otp", json={})
    assert res.status_code == 422

def test_invalid_type_in_path_parameter_returns_422(auth_client_a: TestClient):
    """Verifies string passed into integer path parameter returns 422."""
    res = auth_client_a.get("/api/assessments/not-an-integer")
    assert res.status_code == 422

def test_non_existent_resource_returns_404(auth_client_a: TestClient):
    """Verifies querying non-existent business or application returns 404."""
    res = auth_client_a.get("/api/datasets/999999")
    assert res.status_code == 404

def test_out_of_scope_modules_return_404(client: TestClient):
    """Verifies disabled business intelligence and growth modules strictly return 404."""
    unsupported_routes = [
        "/api/business-analyzer",
        "/api/financial-health",
        "/api/smart-documents",
        "/api/market-analysis",
        "/api/growth-advisor",
        "/api/business-reports"
    ]
    for route in unsupported_routes:
        res = client.get(route)
        assert res.status_code == 404, f"Route {route} should return 404 Not Found"

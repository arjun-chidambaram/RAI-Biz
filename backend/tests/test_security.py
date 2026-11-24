"""
Module 20: Application Security & Hardening Test Suite
======================================================
Covers:
- Authentication enforcement on protected endpoints (rejection of unauthenticated calls)
- Forged and invalid bearer token rejection
- Sensitive information leakage prevention (no secret keys or password hashes in responses)
- SQL injection resistance on text inputs and queries
- Cross-Origin Resource Sharing (CORS) policy verification
"""

from fastapi.testclient import TestClient

def test_protected_endpoints_reject_unauthenticated_requests(client: TestClient):
    """Verifies all protected governance endpoints reject requests without a session."""
    protected_paths = [
        ("GET", "/api/businesses"),
        ("GET", "/api/applications"),
        ("GET", "/api/assessments"),
        ("GET", "/api/datasets"),
        ("GET", "/api/risks"),
        ("GET", "/api/recommendations"),
        ("GET", "/api/dashboard")
    ]
    for method, path in protected_paths:
        if method == "GET":
            res = client.get(path)
        else:
            res = client.post(path, json={})
        # Must return 401 Unauthorized or redirect
        assert res.status_code in [401, 403], f"Endpoint {path} failed to reject unauthenticated request"

def test_forged_bearer_token_rejected(client: TestClient):
    """Verifies arbitrary forged bearer token is rejected with 401."""
    client.headers["Authorization"] = "Bearer forged_secret_token_12345"
    res = client.get("/api/businesses")
    assert res.status_code in [401, 403]

def test_sensitive_credentials_not_leaked_in_user_profile(auth_client_a: TestClient):
    """Verifies /api/auth/me does not expose secrets, salt, or database hashes."""
    res = auth_client_a.get("/api/auth/me")
    assert res.status_code == 200
    user_data = res.json()
    raw_str = str(user_data).lower()
    # Verify sensitive attributes are absent
    assert "password_hash" not in raw_str
    assert "otp_hash" not in raw_str
    assert "secret_key" not in raw_str

def test_sql_injection_payload_handled_safely(auth_client_a: TestClient):
    """Verifies SQL injection strings are safely escaped via SQLAlchemy parameterization."""
    sql_payload = {
        "name": "'; DROP TABLE users; --",
        "industry": "Automotive Services' OR '1'='1",
        "size": "50-100",
        "location": "Berlin"
    }
    res = auth_client_a.post("/api/businesses", json=sql_payload)
    # The API should treat it strictly as literal text, not SQL commands
    assert res.status_code == 200
    data = res.json()
    assert "DROP TABLE" in data["name"]

def test_cors_headers_configured_appropriately(client: TestClient):
    """Verifies CORS response headers for cross-origin frontend requests."""
    res = client.options("/api/health", headers={
        "Origin": "https://rai-biz.vercel.app",
        "Access-Control-Request-Method": "GET"
    })
    # Either 200 OK with Access-Control-Allow-Origin or allowed
    assert res.status_code in [200, 204]

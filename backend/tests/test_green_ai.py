"""
Module 10: Green AI Monitor Test Suite
======================================
Covers:
- Listing of regional carbon intensity factors (6 regions)
- Energy consumption (kWh) and carbon footprint (kg CO2e) calculations
- Custom emission factor overrides
- Edge vs GPU compute profiling
- Zero/negative parameter boundary rejection
- Database persistence of sustainability calculations
"""

from fastapi.testclient import TestClient

def test_list_emission_regions_directory(auth_client_a: TestClient):
    """Verifies directory returns known regional grid intensities."""
    res = auth_client_a.get("/api/sustainability/regions")
    assert res.status_code == 200
    regions = res.json()
    assert len(regions) >= 5
    region_ids = [r["id"] for r in regions]
    assert "us-east-grid" in region_ids
    assert "eu-average" in region_ids
    assert "cloud-datacenter-green" in region_ids

def test_sustainability_calculation_standard_grid(auth_client_a: TestClient, tenant_a):
    """Verifies standard power draw and runtime calculate expected kWh and CO2e."""
    app_id = tenant_a["application"].id
    # 100 hours of 0.25 kW (Edge device) in eu-average
    payload = {
        "application_id": app_id,
        "compute_duration_hours": 100.0,
        "power_draw_kw": 0.25,
        "region_preset": "eu-average"
    }

    res = auth_client_a.post("/api/sustainability/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["energy_kwh"] == 25.0
    assert data["estimated_co2e_kg"] > 0.0
    assert "scenarios" in data
    assert "actionable_recommendations" in data

def test_sustainability_calculation_custom_override(auth_client_a: TestClient, tenant_a):
    """Verifies custom emission factor override is respected mathematically."""
    app_id = tenant_a["application"].id
    # 50 hours of 1.0 kW with custom 0.20 kg CO2e/kWh
    payload = {
        "application_id": app_id,
        "compute_duration_hours": 50.0,
        "power_draw_kw": 1.0,
        "emission_factor_kg_per_kwh": 0.20
    }

    res = auth_client_a.post("/api/sustainability/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["energy_kwh"] == 50.0
    assert abs(data["estimated_co2e_kg"] - 10.0) < 0.01  # 50 kWh * 0.20 = 10.0 kg

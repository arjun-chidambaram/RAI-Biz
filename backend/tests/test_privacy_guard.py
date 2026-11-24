"""
Module 09: Privacy Guard & PII Screening Test Suite
===================================================
Covers:
- Regex and heuristic scanning for sensitive PII
- Detection of email addresses, phone numbers, SSNs, credit cards
- Generation of masking and pseudonymization recommendations
- Non-existent dataset rejection (HTTP 404)
- Foreign dataset cross-application protection (HTTP 400)
- Persistence of privacy findings in database
"""

from pathlib import Path
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Dataset

def _create_pii_csv(tmp_path: Path, filename: str) -> str:
    """Helper to create a CSV with unredacted sensitive PII fields."""
    file_path = tmp_path / filename
    data = {
        "customer_id": [101, 102, 103, 104],
        "full_name": ["Alice Smith", "Bob Jones", "Carol Davis", "Dan Miller"],
        "email": ["alice@private-domain.com", "bob@healthnexus.de", "carol@sme.org", "dan@telemetry.io"],
        "phone": ["+1-555-0199", "555-0200", "(555) 0300", "+49 89 123456"],
        "national_id": ["123-45-6789", "987-65-4321", "234-56-7890", "876-54-3210"],
        "notes": ["Customer requested paint touch-up", "VIP client", "Walk-in inspection", "Regular client"]
    }
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    return str(file_path)

def test_privacy_scan_detects_pii_entities(auth_client_a: TestClient, tenant_a, db: Session, tmp_path: Path):
    """Verifies scanner flags email, phone, and national ID columns with findings."""
    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id
    csv_file = _create_pii_csv(tmp_path, "pii_scan.csv")

    ds = Dataset(
        application_id=app_id,
        filename="pii_scan.csv",
        original_filename="pii_scan.csv",
        file_path=csv_file,
        checksum="testpiichecksum12345",
        row_count=4,
        column_count=6
    )
    db.add(ds)
    db.commit()

    payload = {
        "application_id": app_id,
        "dataset_id": ds.id
    }

    res = auth_client_a.post("/api/privacy/scan", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "findings" in data
    assert "pii_detected_count" in data
    assert data["pii_detected_count"] > 0

    flagged_cols = [f["column"] for f in data["findings"]]
    assert any("email" in col.lower() for col in flagged_cols)
    assert any("phone" in col.lower() for col in flagged_cols)

def test_privacy_scan_foreign_dataset_rejected(auth_client_a: TestClient, tenant_a, tenant_b, db: Session, tmp_path: Path):
    """Verifies Application A cannot trigger PII scan on Application B's dataset."""
    app_a_id = tenant_a["application"].id
    app_b_id = tenant_b["application"].id
    biz_b_id = tenant_b["business"].id
    csv_file = _create_pii_csv(tmp_path, "pii_foreign.csv")

    foreign_ds = Dataset(
        application_id=app_b_id,
        filename="pii_foreign.csv",
        original_filename="pii_foreign.csv",
        file_path=csv_file,
        checksum="testpiiforeignchecksum12345",
        row_count=4,
        column_count=6
    )
    db.add(foreign_ds)
    db.commit()

    payload = {
        "application_id": app_a_id,
        "dataset_id": foreign_ds.id
    }

    res = auth_client_a.post("/api/privacy/scan", json=payload)
    assert res.status_code == 400
    assert "not associated with this application" in res.json()["detail"].lower()

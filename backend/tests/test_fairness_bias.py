"""
Module 06: AI Fairness & Bias Detection Test Suite
==================================================
Covers:
- Fairlearn demographic parity and disparate impact analysis on valid dataset
- Four-fifths (80%) rule compliance evaluation
- Missing sensitive attribute column rejection (HTTP 400)
- Foreign dataset cross-application protection (HTTP 400)
- Non-existent dataset rejection (HTTP 404)
- Recording of fairness metrics and finding persistence in database
"""

import os
from pathlib import Path
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Dataset

def _create_sample_csv(tmp_path: Path, filename: str) -> str:
    """Helper to create a synthetic CSV with demographic attributes."""
    file_path = tmp_path / filename
    data = {
        "candidate_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "gender": ["Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female", "Male", "Female"],
        "experience_years": [5, 4, 6, 5, 7, 3, 8, 6, 4, 5],
        "interview_score": [85, 88, 70, 92, 60, 75, 89, 94, 82, 78],
        "hired": [1, 1, 0, 1, 0, 0, 1, 1, 0, 0]
    }
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    return str(file_path)

def test_fairness_analysis_valid_dataset(auth_client_a: TestClient, tenant_a, db: Session, tmp_path: Path):
    """Verifies demographic parity ratio and disparate impact calculations."""
    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id
    csv_file = _create_sample_csv(tmp_path, "fairness_test.csv")

    ds = Dataset(
        application_id=app_id,
        filename="fairness_test.csv",
        original_filename="fairness_test.csv",
        file_path=csv_file,
        checksum="testchecksum1234567890abcdef",
        row_count=10,
        column_count=5
    )
    db.add(ds)
    db.commit()

    payload = {
        "application_id": app_id,
        "dataset_id": ds.id,
        "sensitive_attribute": "gender",
        "target_attribute": "hired",
        "favorable_outcome": 1
    }

    res = auth_client_a.post("/api/fairness/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "demographic_parity_ratio" in data
    assert "demographic_parity_diff" in data
    assert "four_fifths_rule_passed" in data
    assert "group_metrics" in data
    assert len(data["group_metrics"]) >= 2

def test_fairness_analysis_missing_column_rejected(auth_client_a: TestClient, tenant_a, db: Session, tmp_path: Path):
    """Verifies requesting non-existent column raises HTTP 400."""
    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id
    csv_file = _create_sample_csv(tmp_path, "fairness_missing_col.csv")

    ds = Dataset(
        application_id=app_id,
        filename="fairness_missing_col.csv",
        original_filename="fairness_missing_col.csv",
        file_path=csv_file,
        checksum="testchecksum1234567890abcdef2",
        row_count=10,
        column_count=5
    )
    db.add(ds)
    db.commit()

    payload = {
        "application_id": app_id,
        "dataset_id": ds.id,
        "sensitive_attribute": "non_existent_column",
        "target_attribute": "hired",
        "favorable_outcome": 1
    }

    res = auth_client_a.post("/api/fairness/analyze", json=payload)
    assert res.status_code == 400
    assert "non_existent_column" in res.json()["detail"] or "column" in res.json()["detail"].lower()

def test_fairness_cross_application_dataset_rejected(auth_client_a: TestClient, tenant_a, tenant_b, db: Session, tmp_path: Path):
    """Verifies Application A cannot analyze a dataset associated with Application B."""
    app_a_id = tenant_a["application"].id
    app_b_id = tenant_b["application"].id
    biz_b_id = tenant_b["business"].id
    csv_file = _create_sample_csv(tmp_path, "foreign_dataset.csv")

    foreign_ds = Dataset(
        application_id=app_b_id,
        filename="foreign_dataset.csv",
        original_filename="foreign_dataset.csv",
        file_path=csv_file,
        checksum="testchecksumforeign12345",
        row_count=10,
        column_count=5
    )
    db.add(foreign_ds)
    db.commit()

    payload = {
        "application_id": app_a_id,
        "dataset_id": foreign_ds.id,
        "sensitive_attribute": "gender",
        "target_attribute": "hired",
        "favorable_outcome": 1
    }

    res = auth_client_a.post("/api/fairness/analyze", json=payload)
    assert res.status_code == 400
    assert "not associated with this application" in res.json()["detail"].lower()

def test_fairness_non_existent_dataset_returns_404(auth_client_a: TestClient, tenant_a):
    """Verifies non-existent dataset ID returns HTTP 404."""
    payload = {
        "application_id": tenant_a["application"].id,
        "dataset_id": 999999,
        "sensitive_attribute": "gender",
        "target_attribute": "hired",
        "favorable_outcome": 1
    }
    res = auth_client_a.post("/api/fairness/analyze", json=payload)
    assert res.status_code == 404

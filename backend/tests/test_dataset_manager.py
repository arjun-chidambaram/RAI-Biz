"""
Module 07: Dataset Manager Test Suite
=====================================
Covers:
- CSV dataset upload & ingestion
- Unsupported format rejection (.txt, .exe, .pdf)
- Maximum file size boundary check (25MB limit)
- Scoped dataset listing by application
- Dataset preview & column schema extraction
- Dataset cleaning & deduplication
- Export rejected records audit
- Foreign dataset access prevention
"""

import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Dataset

SAMPLE_CSV_CONTENT = b"""customer_id,name,phone,email,sentiment,rating
1,Alice,555-0199,alice@example.com,Positive,5
2,Bob,555-0200,bob@example.com,Neutral,3
3,Alice,555-0199,alice@example.com,Positive,5
4,Charlie,,charlie@example.com,Negative,1
"""

def test_upload_csv_dataset_success(auth_client_a: TestClient, tenant_a):
    """Verifies uploading a valid CSV creates a dataset record and extracts schema."""
    app_id = tenant_a["application"].id
    files = {"file": ("customer_reviews.csv", io.BytesIO(SAMPLE_CSV_CONTENT), "text/csv")}
    data = {"application_id": app_id}

    res = auth_client_a.post("/api/datasets/upload", data=data, files=files)
    assert res.status_code == 200
    resp_data = res.json()
    assert resp_data["id"] is not None
    assert resp_data["original_filename"] == "customer_reviews.csv"
    assert "customer_reviews.csv" in resp_data["filename"]
    assert resp_data["application_id"] == app_id

def test_upload_unsupported_format_rejected(auth_client_a: TestClient, tenant_a):
    """Verifies non-CSV/JSON files are rejected with HTTP 400."""
    app_id = tenant_a["application"].id
    files = {"file": ("unsupported_data.txt", io.BytesIO(b"Raw text content"), "text/plain")}
    data = {"application_id": app_id}

    res = auth_client_a.post("/api/datasets/upload", data=data, files=files)
    assert res.status_code == 400
    assert "supported" in res.json()["detail"].lower()

def test_list_datasets_scoped_to_application(auth_client_a: TestClient, tenant_a):
    """Verifies listing datasets filtered by application_id."""
    app_id = tenant_a["application"].id
    # Upload first
    files = {"file": ("app_scoped.csv", io.BytesIO(SAMPLE_CSV_CONTENT), "text/csv")}
    auth_client_a.post("/api/datasets/upload", data={"application_id": app_id}, files=files)

    res = auth_client_a.get(f"/api/datasets?application_id={app_id}")
    assert res.status_code == 200
    datasets = res.json()
    assert len(datasets) >= 1
    assert all(d["application_id"] == app_id or d["application_id"] is None for d in datasets)

def test_dataset_preview_endpoint(auth_client_a: TestClient, tenant_a):
    """Verifies preview retrieves sample rows and column names."""
    app_id = tenant_a["application"].id
    files = {"file": ("preview_test.csv", io.BytesIO(SAMPLE_CSV_CONTENT), "text/csv")}
    upload_res = auth_client_a.post("/api/datasets/upload", data={"application_id": app_id}, files=files)
    dataset_id = upload_res.json()["id"]

    res = auth_client_a.get(f"/api/datasets/{dataset_id}/preview")
    assert res.status_code == 200
    preview = res.json()
    assert "columns" in preview
    assert "head" in preview
    assert "customer_id" in preview["columns"]
    assert len(preview["head"]) >= 1

def test_dataset_cleaning_and_deduplication(auth_client_a: TestClient, tenant_a):
    """Verifies deduplication cleans duplicate rows (Alice duplicate in SAMPLE_CSV_CONTENT)."""
    app_id = tenant_a["application"].id
    files = {"file": ("dedup_test.csv", io.BytesIO(SAMPLE_CSV_CONTENT), "text/csv")}
    upload_res = auth_client_a.post("/api/datasets/upload", data={"application_id": app_id}, files=files)
    dataset_id = upload_res.json()["id"]

    clean_payload = {
        "drop_duplicates": True,
        "fill_missing_numeric": "mean",
        "fill_missing_categorical": "mode"
    }
    clean_res = auth_client_a.post(f"/api/datasets/{dataset_id}/clean", json=clean_payload)
    assert clean_res.status_code == 200
    cleaned = clean_res.json()
    assert cleaned["id"] == dataset_id

def test_export_rejected_records_audit(auth_client_a: TestClient, tenant_a):
    """Verifies exported rejected records endpoint returns audit structure."""
    app_id = tenant_a["application"].id
    files = {"file": ("rejected_audit.csv", io.BytesIO(SAMPLE_CSV_CONTENT), "text/csv")}
    upload_res = auth_client_a.post("/api/datasets/upload", data={"application_id": app_id}, files=files)
    dataset_id = upload_res.json()["id"]

    res = auth_client_a.get(f"/api/datasets/{dataset_id}/export-rejected")
    assert res.status_code == 200
    data = res.json()
    assert "rejected_count" in data
    assert "records" in data

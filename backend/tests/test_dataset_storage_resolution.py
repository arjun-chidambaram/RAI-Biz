"""
Tests for Dataset Storage Resolution & Ephemeral/Cross-Platform Path Handling
=============================================================================
Verifies:
1. Windows absolute path resolution on Linux/Render.
2. Linux path resolution across configurable storage directories.
3. Fallback resolution via bundled DATA_DIR.
4. Actionable 404 error returned when file is physically unavailable.
5. End-to-end XAI, Fairness, Privacy Guard, Preview, and Clean endpoints with missing files.
6. Successful upload stores relative storage keys and preserves SHA-256 checksums.
7. End-to-end XAI analysis on newly uploaded datasets.
8. Tenant isolation & application scoping preservation.
"""

import io
import hashlib
from pathlib import Path
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Dataset
from app.config import settings
from app.services.storage_service import (
    resolve_dataset_path,
    get_resolved_dataset_path,
    load_dataset_dataframe,
    extract_storage_basename,
    get_storage_key,
    DatasetFileNotFoundError
)

ML_SAMPLE_CSV = b"""mileage,vehicle_age,paint_depth_microns,prior_ceramic,approved
10000,1,120,1,1
50000,5,95,0,0
30000,3,110,1,1
80000,8,80,0,0
20000,2,115,1,1
95000,9,75,0,0
15000,1,125,1,1
60000,6,90,0,0
45000,4,105,1,1
110000,10,70,0,0
"""

def test_extract_storage_basename():
    """Verifies cross-platform basename extraction handles Windows and Linux paths."""
    assert extract_storage_basename(r"C:\Users\sethu\Desktop\data.csv") == "data.csv"
    assert extract_storage_basename(r"C:\Program Files\App\uploads\sub\data.csv") == "data.csv"
    assert extract_storage_basename("/var/data/uploads/production_data.csv") == "production_data.csv"
    assert extract_storage_basename("uploads/customer_data.csv") == "customer_data.csv"
    assert extract_storage_basename("plain_filename.csv") == "plain_filename.csv"
    assert extract_storage_basename("") == ""
    assert extract_storage_basename(None) == ""


def test_get_storage_key():
    """Verifies storage key is always a POSIX relative path under uploads/."""
    assert get_storage_key(r"C:\Users\sethu\test.csv") == "uploads/test.csv"
    assert get_storage_key("/var/data/test.csv") == "uploads/test.csv"
    assert get_storage_key("uploads/test.csv") == "uploads/test.csv"
    assert get_storage_key("test.csv") == "uploads/test.csv"


def test_windows_absolute_path_resolution(tmp_path: Path, monkeypatch):
    """
    Verifies that a database record containing a Windows absolute path
    from another environment (e.g. C:\\other_machine\\uploads\\data.csv)
    safely resolves via settings.UPLOAD_DIR on any platform (including Linux/Render).
    """
    test_upload_dir = tmp_path / "custom_uploads"
    test_upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings, "UPLOAD_DIR", test_upload_dir)

    target_file = test_upload_dir / "remote_customer_dataset.csv"
    target_file.write_bytes(ML_SAMPLE_CSV)

    win_path = r"C:\Users\remote_user\Desktop\RAI-Biz\backend\uploads\remote_customer_dataset.csv"

    resolved = resolve_dataset_path(win_path, filename="remote_customer_dataset.csv")
    assert resolved is not None
    assert resolved.is_file()
    assert resolved.resolve() == target_file.resolve()

    # Load dataframe
    df = load_dataset_dataframe(str(win_path))
    assert len(df) == 10
    assert "approved" in df.columns


def test_linux_absolute_path_resolution(tmp_path: Path, monkeypatch):
    """
    Verifies that a Linux persistent disk path (e.g. /var/data/uploads/data.csv)
    resolves safely via settings.UPLOAD_DIR.
    """
    test_upload_dir = tmp_path / "custom_uploads"
    test_upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings, "UPLOAD_DIR", test_upload_dir)

    target_file = test_upload_dir / "production_dataset.csv"
    target_file.write_bytes(ML_SAMPLE_CSV)

    linux_path = "/var/data/uploads/production_dataset.csv"

    resolved = resolve_dataset_path(linux_path, filename="production_dataset.csv")
    assert resolved is not None
    assert resolved.is_file()
    assert resolved.resolve() == target_file.resolve()

    df = load_dataset_dataframe(str(linux_path))
    assert len(df) == 10


def test_bundled_data_dir_resolution(tmp_path: Path, monkeypatch):
    """
    Verifies that seed/bundled demo datasets in DATA_DIR are resolved
    even if the file is absent from UPLOAD_DIR.
    """
    empty_upload_dir = tmp_path / "empty_uploads"
    empty_upload_dir.mkdir(parents=True, exist_ok=True)
    bundled_data_dir = tmp_path / "bundled_data"
    bundled_data_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(settings, "UPLOAD_DIR", empty_upload_dir)
    monkeypatch.setattr(settings, "DATA_DIR", bundled_data_dir)

    demo_file = bundled_data_dir / "smarthire_recruitment_demo.csv"
    demo_file.write_bytes(ML_SAMPLE_CSV)

    legacy_win_path = r"C:\Users\sethu\Desktop\backend\uploads\smarthire_recruitment_demo.csv"

    resolved = resolve_dataset_path(legacy_win_path, filename="smarthire_recruitment_demo.csv")
    assert resolved is not None
    assert resolved.resolve() == demo_file.resolve()


def test_missing_file_raises_actionable_error():
    """
    Verifies that if a dataset file does not exist on disk,
    DatasetFileNotFoundError is raised with status 404 and actionable instruction.
    """
    missing_path = r"C:\Users\sethu\Desktop\completely_missing_dataset.csv"
    with pytest.raises(DatasetFileNotFoundError) as exc_info:
        load_dataset_dataframe(missing_path)

    err = exc_info.value
    assert err.status_code == 404
    assert "completely_missing_dataset.csv" in err.detail
    assert "not available on the server" in err.detail
    assert "upload the dataset again" in err.detail


def test_xai_endpoint_returns_404_on_missing_dataset_file(
    auth_client_a: TestClient, tenant_a, db: Session
):
    """
    Verifies /api/explainability/analyze returns a clear HTTP 404 error
    when the dataset database record exists but the underlying file is missing.
    """
    app_id = tenant_a["application"].id
    ds = Dataset(
        application_id=app_id,
        filename="missing_xai_data.csv",
        original_filename="missing_xai_data.csv",
        file_path=r"C:\Users\sethu\OneDrive\Desktop\RAI-Biz\backend\uploads\missing_xai_data.csv",
        checksum="fakexaimissingchecksum123",
        row_count=100,
        column_count=5
    )
    db.add(ds)
    db.commit()

    payload = {
        "application_id": app_id,
        "dataset_id": ds.id,
        "target_attribute": "approved",
        "model_type": "RandomForest"
    }

    res = auth_client_a.post("/api/explainability/analyze", json=payload)
    assert res.status_code == 404
    detail = res.json()["detail"]
    assert "missing_xai_data.csv" in detail
    assert "not available on the server" in detail
    assert "upload the dataset again" in detail


def test_fairness_and_privacy_endpoints_return_404_on_missing_dataset_file(
    auth_client_a: TestClient, tenant_a, db: Session
):
    """
    Verifies /api/fairness/analyze and /api/privacy/scan return HTTP 404
    when the underlying dataset file is missing.
    """
    app_id = tenant_a["application"].id
    ds = Dataset(
        application_id=app_id,
        filename="missing_audit_data.csv",
        original_filename="missing_audit_data.csv",
        file_path="uploads/missing_audit_data.csv",
        checksum="fakeauditmissingchecksum456",
        row_count=50,
        column_count=4
    )
    db.add(ds)
    db.commit()

    # Fairness
    fairness_payload = {
        "application_id": app_id,
        "dataset_id": ds.id,
        "sensitive_attribute": "gender",
        "target_attribute": "approved",
        "favorable_outcome": 1
    }
    f_res = auth_client_a.post("/api/fairness/analyze", json=fairness_payload)
    assert f_res.status_code == 404
    assert "not available on the server" in f_res.json()["detail"]

    # Privacy
    privacy_payload = {
        "application_id": app_id,
        "dataset_id": ds.id
    }
    p_res = auth_client_a.post("/api/privacy/scan", json=privacy_payload)
    assert p_res.status_code == 404
    assert "not available on the server" in p_res.json()["detail"]


def test_preview_and_clean_endpoints_return_404_on_missing_dataset_file(
    auth_client_a: TestClient, tenant_a, db: Session
):
    """
    Verifies preview and clean return HTTP 404 instead of 500 when file is missing.
    """
    app_id = tenant_a["application"].id
    ds = Dataset(
        application_id=app_id,
        filename="missing_clean_data.csv",
        original_filename="missing_clean_data.csv",
        file_path="uploads/missing_clean_data.csv",
        checksum="fakecleanmissingchecksum789",
        row_count=50,
        column_count=4
    )
    db.add(ds)
    db.commit()

    # Preview
    prev_res = auth_client_a.get(f"/api/datasets/{ds.id}/preview")
    assert prev_res.status_code == 404
    assert "not available on the server" in prev_res.json()["detail"]

    # Clean
    clean_payload = {
        "drop_duplicates": True,
        "fill_missing_numeric": "median",
        "fill_missing_categorical": "mode"
    }
    clean_res = auth_client_a.post(f"/api/datasets/{ds.id}/clean", json=clean_payload)
    assert clean_res.status_code == 404
    assert "not available on the server" in clean_res.json()["detail"]


def test_dataset_upload_stores_relative_path_and_preserves_sha256(
    auth_client_a: TestClient, tenant_a, db: Session
):
    """
    Verifies that uploading a dataset stores a relative POSIX storage key
    (not a Windows absolute path), verifies SHA-256 checksum, and writes to disk.
    """
    app_id = tenant_a["application"].id
    expected_checksum = hashlib.sha256(ML_SAMPLE_CSV).hexdigest()

    files = {"file": ("upload_test_dataset.csv", io.BytesIO(ML_SAMPLE_CSV), "text/csv")}
    data = {"application_id": app_id}

    res = auth_client_a.post("/api/datasets/upload", data=data, files=files)
    assert res.status_code == 200
    resp = res.json()
    dataset_id = resp["id"]

    # Verify database record
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    assert ds is not None
    assert ds.checksum == expected_checksum
    # Must NOT contain Windows drive letter or backslashes
    assert not ds.file_path.startswith("C:")
    assert "\\" not in ds.file_path
    assert ds.file_path.startswith("uploads/")
    assert ds.original_filename == "upload_test_dataset.csv"

    # Verify physical file existence in UPLOAD_DIR
    resolved_path = resolve_dataset_path(ds.file_path, filename=ds.filename)
    assert resolved_path is not None
    assert resolved_path.is_file()
    assert resolved_path.read_bytes() == ML_SAMPLE_CSV


def test_xai_access_to_newly_uploaded_dataset(
    auth_client_a: TestClient, tenant_a
):
    """
    Verifies that a newly uploaded dataset can immediately be analyzed
    by the Explainable AI (XAI) engine.
    """
    app_id = tenant_a["application"].id
    files = {"file": ("xai_e2e_dataset.csv", io.BytesIO(ML_SAMPLE_CSV), "text/csv")}
    data = {"application_id": app_id}

    upload_res = auth_client_a.post("/api/datasets/upload", data=data, files=files)
    assert upload_res.status_code == 200
    dataset_id = upload_res.json()["id"]

    xai_payload = {
        "application_id": app_id,
        "dataset_id": dataset_id,
        "target_attribute": "approved",
        "model_type": "RandomForest"
    }

    xai_res = auth_client_a.post("/api/explainability/analyze", json=xai_payload)
    assert xai_res.status_code == 200
    xai_data = xai_res.json()
    assert "model_name" in xai_data
    assert "global_importance" in xai_data
    assert len(xai_data["global_importance"]) > 0


def test_tenant_isolation_on_uploaded_dataset(
    auth_client_a: TestClient, tenant_a, tenant_b, db: Session
):
    """
    Verifies cross-tenant isolation: Tenant A cannot access Tenant B's dataset,
    and foreign dataset ID association is rejected with HTTP 400.
    """
    app_a_id = tenant_a["application"].id
    app_b_id = tenant_b["application"].id

    # Tenant A uploads a dataset
    files = {"file": ("tenant_a_data.csv", io.BytesIO(ML_SAMPLE_CSV), "text/csv")}
    upload_res = auth_client_a.post("/api/datasets/upload", data={"application_id": app_a_id}, files=files)
    assert upload_res.status_code == 200
    dataset_a_id = upload_res.json()["id"]

    # Tenant B creates a dataset
    ds_b = Dataset(
        application_id=app_b_id,
        filename="tenant_b_data.csv",
        original_filename="tenant_b_data.csv",
        file_path="uploads/tenant_b_data.csv",
        checksum="tenantbchecksum123456",
        row_count=10,
        column_count=5
    )
    db.add(ds_b)
    db.commit()

    # Tenant A attempts to analyze Tenant A's app but passing Tenant B's dataset ID -> rejected 400
    cross_ds_payload = {
        "application_id": app_a_id,
        "dataset_id": ds_b.id,
        "target_attribute": "approved"
    }
    res_cross = auth_client_a.post("/api/explainability/analyze", json=cross_ds_payload)
    assert res_cross.status_code == 400
    assert "not associated with this application" in res_cross.json()["detail"]

    # Tenant A attempts to analyze Tenant B's application -> rejected 403
    cross_app_payload = {
        "application_id": app_b_id,
        "dataset_id": dataset_a_id,
        "target_attribute": "approved"
    }
    res_app = auth_client_a.post("/api/explainability/analyze", json=cross_app_payload)
    assert res_app.status_code == 403

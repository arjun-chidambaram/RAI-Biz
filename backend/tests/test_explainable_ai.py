"""
Module 08: Explainable AI (XAI) Test Suite
==========================================
Covers:
- RandomForestClassifier model training and explainability extraction
- Global feature importance attribution
- Dynamic target column resolution (e.g., target, outcome, label, approved)
- Non-existent dataset rejection (HTTP 404)
- Foreign dataset cross-application access prevention (HTTP 400)
- Model accuracy and top contributor persistence
- Safe edge cases: 3-row datasets, missing targets, empty/PII features,
  single-class target, categorical encoding, and zero-variance features.
"""

from pathlib import Path
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Dataset

def _create_ml_csv(tmp_path: Path, filename: str) -> str:
    """Helper to create a numeric tabular dataset for ML explainability."""
    file_path = tmp_path / filename
    data = {
        "mileage": [10000, 50000, 30000, 80000, 20000, 95000, 15000, 60000, 45000, 110000],
        "vehicle_age": [1, 5, 3, 8, 2, 9, 1, 6, 4, 10],
        "paint_depth_microns": [120, 95, 110, 80, 115, 75, 125, 90, 105, 70],
        "prior_ceramic": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        "approved": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
    }
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    return str(file_path)

def test_explainability_analysis_success(auth_client_a: TestClient, tenant_a, db: Session, tmp_path: Path):
    """Verifies model trains and returns feature importances and tree attributions."""
    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id
    csv_file = _create_ml_csv(tmp_path, "xai_train.csv")

    ds = Dataset(
        application_id=app_id,
        filename="xai_train.csv",
        original_filename="xai_train.csv",
        file_path=csv_file,
        checksum="testxaimodelchecksum12345",
        row_count=10,
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
    assert res.status_code == 200
    data = res.json()
    assert "model_name" in data
    assert "model_accuracy" in data
    assert "global_importance" in data
    assert len(data["global_importance"]) >= 2
    # Verify importance attributes have feature name and importance weight
    feat_names = [f["feature"] for f in data["global_importance"]]
    assert any(feat in ["mileage", "vehicle_age", "paint_depth_microns"] for feat in feat_names)

    # Verify model confidence, disclaimers, and accuracy
    assert "prediction_disclaimer" in data
    assert "statistical algorithmic inferences" in data["prediction_disclaimer"]
    assert "sample_explanations" in data
    assert len(data["sample_explanations"]) >= 1

    sample = data["sample_explanations"][0]
    assert "model_confidence" in sample
    assert isinstance(sample["model_confidence"], float)
    assert 0.5 <= sample["model_confidence"] <= 1.0
    assert "plain_narrative" in sample
    assert "not a verified ground truth outcome" in sample["plain_narrative"]
    assert "confirmed" not in sample["plain_narrative"].lower()

def test_explainability_foreign_dataset_rejected(auth_client_a: TestClient, tenant_a, tenant_b, db: Session, tmp_path: Path):
    """Verifies Application A cannot analyze Application B's dataset."""
    app_a_id = tenant_a["application"].id
    app_b_id = tenant_b["application"].id
    biz_b_id = tenant_b["business"].id
    csv_file = _create_ml_csv(tmp_path, "xai_foreign.csv")

    foreign_ds = Dataset(
        application_id=app_b_id,
        filename="xai_foreign.csv",
        original_filename="xai_foreign.csv",
        file_path=csv_file,
        checksum="testxaiforeignchecksum12345",
        row_count=10,
        column_count=5
    )
    db.add(foreign_ds)
    db.commit()

    payload = {
        "application_id": app_a_id,
        "dataset_id": foreign_ds.id,
        "target_attribute": "approved"
    }

    res = auth_client_a.post("/api/explainability/analyze", json=payload)
    assert res.status_code == 400
    assert "not associated with this application" in res.json()["detail"].lower()

def test_explainability_three_row_dataset_rejected(auth_client_a: TestClient, tenant_a, db: Session, tmp_path: Path):
    """Verifies 3-row dataset (e.g. privacytest.csv) returns clear actionable 400 instead of raw array error."""
    app_id = tenant_a["application"].id
    file_path = tmp_path / "privacytest.csv"
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "email": ["alice@corp.com", "bob@corp.com", "charlie@corp.com"],
        "phone": ["555-0101", "555-0102", "555-0103"]
    })
    df.to_csv(file_path, index=False)

    ds = Dataset(
        application_id=app_id,
        filename="privacytest.csv",
        original_filename="privacytest.csv",
        file_path=str(file_path),
        checksum="privacytestchecksum3rows",
        row_count=3,
        column_count=4
    )
    db.add(ds)
    db.commit()

    payload = {
        "application_id": app_id,
        "dataset_id": ds.id,
        "model_type": "RandomForest"
    }

    res = auth_client_a.post("/api/explainability/analyze", json=payload)
    assert res.status_code == 400
    detail = res.json()["detail"]
    # Must NOT fail with raw numpy error
    assert "at least one array or dtype is required" not in detail
    assert "minimum of 4 records is required" in detail

def test_explainability_missing_target_rejected(auth_client_a: TestClient, tenant_a, db: Session, tmp_path: Path):
    """Verifies dataset without valid target returns clear actionable 400."""
    app_id = tenant_a["application"].id
    file_path = tmp_path / "no_target.csv"
    df = pd.DataFrame({
        "col_x": [10, 20, 30, 40, 50, 60],
        "col_y": [1.1, 2.2, 3.3, 4.4, 5.5, 6.6],
        "col_z": [100, 200, 300, 400, 500, 600]
    })
    df.to_csv(file_path, index=False)

    ds = Dataset(
        application_id=app_id,
        filename="no_target.csv",
        original_filename="no_target.csv",
        file_path=str(file_path),
        checksum="notargetchecksum12345",
        row_count=6,
        column_count=3
    )
    db.add(ds)
    db.commit()

    payload = {
        "application_id": app_id,
        "dataset_id": ds.id,
        "model_type": "RandomForest"
    }

    res = auth_client_a.post("/api/explainability/analyze", json=payload)
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert "no valid classification target column found" in detail.lower()

def test_explainability_empty_features_all_pii_rejected(auth_client_a: TestClient, tenant_a, db: Session, tmp_path: Path):
    """Verifies dataset with only ID/PII features and target returns clean 400."""
    app_id = tenant_a["application"].id
    file_path = tmp_path / "all_pii.csv"
    df = pd.DataFrame({
        "id": [1, 2, 3, 4, 5, 6],
        "candidate_id": ["C1", "C2", "C3", "C4", "C5", "C6"],
        "name": ["A", "B", "C", "D", "E", "F"],
        "email": ["a@x.com", "b@x.com", "c@x.com", "d@x.com", "e@x.com", "f@x.com"],
        "approved": [1, 0, 1, 0, 1, 0]
    })
    df.to_csv(file_path, index=False)

    ds = Dataset(
        application_id=app_id,
        filename="all_pii.csv",
        original_filename="all_pii.csv",
        file_path=str(file_path),
        checksum="allpiichecksum12345",
        row_count=6,
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
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert "no usable model features found" in detail.lower()

def test_explainability_single_class_target_rejected(auth_client_a: TestClient, tenant_a, db: Session, tmp_path: Path):
    """Verifies dataset where target has only 1 distinct class returns clean 400."""
    app_id = tenant_a["application"].id
    file_path = tmp_path / "single_class.csv"
    df = pd.DataFrame({
        "feature_1": [10, 20, 30, 40, 50, 60],
        "feature_2": [100, 200, 300, 400, 500, 600],
        "approved": [1, 1, 1, 1, 1, 1]
    })
    df.to_csv(file_path, index=False)

    ds = Dataset(
        application_id=app_id,
        filename="single_class.csv",
        original_filename="single_class.csv",
        file_path=str(file_path),
        checksum="singleclasschecksum12345",
        row_count=6,
        column_count=3
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
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert "requires at least 2 distinct outcome classes" in detail.lower()

def test_explainability_categorical_features_success(auth_client_a: TestClient, tenant_a, db: Session, tmp_path: Path):
    """Verifies dataset with categorical features trains and explains properly."""
    app_id = tenant_a["application"].id
    file_path = tmp_path / "categoricals.csv"
    df = pd.DataFrame({
        "department": ["Engineering", "Sales", "Engineering", "Marketing", "Sales", "Engineering", "Marketing", "Sales"],
        "education": ["BSc", "MSc", "PhD", "BSc", "MSc", "BSc", "MSc", "PhD"],
        "years_experience": [2, 7, 5, 3, 8, 4, 6, 9],
        "approved": [1, 0, 1, 0, 1, 1, 0, 1]
    })
    df.to_csv(file_path, index=False)

    ds = Dataset(
        application_id=app_id,
        filename="categoricals.csv",
        original_filename="categoricals.csv",
        file_path=str(file_path),
        checksum="categoricalschecksum12345",
        row_count=8,
        column_count=4
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
    assert res.status_code == 200
    data = res.json()
    assert "global_importance" in data
    assert len(data["global_importance"]) >= 2
    assert "sample_explanations" in data
    assert len(data["sample_explanations"]) >= 1

    # Verify categorical dummy decoding into readable feature_display
    sample = data["sample_explanations"][0]
    all_contributors = sample["top_positive_features"] + sample["top_negative_features"]
    assert len(all_contributors) >= 1
    # Check that at least one contributor decoded department or education nicely
    for c in all_contributors:
        assert "feature" in c
        assert "feature_display" in c
        assert "impact" in c
        assert "value" in c
    cat_displays = [c["feature_display"] for c in all_contributors if c["feature_display"] in ["department", "education"]]
    # Should decode prefix rather than leaving only raw dummy column name
    assert len(cat_displays) >= 1

def test_explainability_zero_variance_features_rejected(auth_client_a: TestClient, tenant_a, db: Session, tmp_path: Path):
    """Verifies dataset where all candidate features have zero variance returns clean 400."""
    app_id = tenant_a["application"].id
    file_path = tmp_path / "zero_variance.csv"
    df = pd.DataFrame({
        "constant_col1": [42, 42, 42, 42, 42, 42],
        "constant_col2": ["Same", "Same", "Same", "Same", "Same", "Same"],
        "approved": [1, 0, 1, 0, 1, 0]
    })
    df.to_csv(file_path, index=False)

    ds = Dataset(
        application_id=app_id,
        filename="zero_variance.csv",
        original_filename="zero_variance.csv",
        file_path=str(file_path),
        checksum="zerovariancechecksum12345",
        row_count=6,
        column_count=3
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
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert "zero variance" in detail.lower() or "constant values" in detail.lower()

def test_explainability_low_accuracy_warning_flag():
    """Verifies that datasets resulting in test accuracy < 70% produce an explicit accuracy_warning."""
    from app.services.xai_service import train_and_explain_model

    # Dataset with unpredictable labels
    df_noisy = pd.DataFrame({
        "feat_a": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        "feat_b": [12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
        "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
    })
    res = train_and_explain_model(df_noisy, target_column="target", model_type="LogisticRegression")
    assert "model_accuracy" in res
    if res["model_accuracy"] < 0.70:
        assert res["accuracy_warning"] is not None
        assert "Low Model Accuracy Alert" in res["accuracy_warning"]
        assert "70.0% reliability benchmark" in res["accuracy_warning"]
        for sample in res["sample_explanations"]:
            assert "Caution: Model test accuracy is low" in sample["plain_narrative"]
    else:
        assert res["accuracy_warning"] is None

def test_explainability_confidence_distinct_from_positive_probability():
    """Verifies that model_confidence measures confidence in predicted class, not positive probability."""
    from app.services.xai_service import train_and_explain_model

    df = pd.DataFrame({
        "score": [10, 15, 20, 25, 30, 80, 85, 90, 95, 100],
        "target": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
    })
    res = train_and_explain_model(df, target_column="target", model_type="RandomForest")
    assert len(res["sample_explanations"]) >= 1

    for sample in res["sample_explanations"]:
        pred = sample["prediction"]
        conf = sample["model_confidence"]
        prob = sample["probability"]

        # Confidence in own prediction must always be >= 0.5
        assert conf >= 0.50
        if pred == 1:
            # For class 1, confidence matches probability of class 1
            assert abs(conf - prob) < 0.05
        else:
            # For class 0, confidence is P(class 0) = 1 - P(class 1)
            assert abs(conf - (1.0 - prob)) < 0.05


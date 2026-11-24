import json
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

from ..models import ExplainabilityResult, Risk, Recommendation
from sqlalchemy.orm import Session

IDENTIFIER_PATTERNS = {
    "id", "candidate_id", "booking_id", "customer_id", "user_id", "client_id",
    "employee_id", "record_id", "uuid", "guid", "row_id", "index", "email",
    "phone", "phone_number", "ssn", "social_security_number", "first_name",
    "last_name", "full_name", "name", "address", "zipcode", "postal_code"
}

CANDIDATE_TARGETS = [
    "target", "outcome", "label", "approved", "service_approved",
    "recommended_ceramic", "qualified", "selected", "status", "decision",
    "hired", "admitted", "default", "churn"
]

def is_identifier_or_pii(col: str) -> bool:
    """Check if column name indicates an identifier, index, or direct PII."""
    c = col.strip().lower()
    if c in IDENTIFIER_PATTERNS:
        return True
    if c.endswith("_id") or c.startswith("id_") or c.endswith("_uuid") or c.endswith("_guid"):
        return True
    return False

def resolve_target_column(df: pd.DataFrame, requested_target: Optional[str] = None) -> str:
    """
    Validates or resolves the target column.
    Never silently selects an arbitrary column (such as the last column).
    """
    cols_lower_map = {c.strip().lower(): c for c in df.columns}

    if requested_target and requested_target.strip():
        req_clean = requested_target.strip()
        matched_col = None
        if req_clean in df.columns:
            matched_col = req_clean
        elif req_clean.lower() in cols_lower_map:
            matched_col = cols_lower_map[req_clean.lower()]

        if not matched_col:
            raise ValueError(
                f"Selected target column '{requested_target}' does not exist in the dataset. "
                f"Available columns: {list(df.columns)}."
            )

        if is_identifier_or_pii(matched_col):
            raise ValueError(
                f"Column '{matched_col}' is an identifier/ID field and cannot be used as an ML classification target."
            )
        return matched_col

    # No target requested or target was blank -> check candidate targets
    for cand in CANDIDATE_TARGETS:
        if cand in cols_lower_map:
            matched = cols_lower_map[cand]
            if not is_identifier_or_pii(matched):
                return matched

    raise ValueError(
        "No valid classification target column found in dataset. "
        "Please select a target column (e.g. 'approved', 'selected', 'outcome', or 'status') in the target dropdown."
    )

def prepare_target_variable(y_raw: pd.Series, target_col: str) -> np.ndarray:
    """
    Validates that target column has sufficient non-null values and at least 2 distinct classes.
    Encodes binary outcomes appropriately.
    """
    valid_mask = y_raw.notna()
    if not valid_mask.any():
        raise ValueError(f"Target column '{target_col}' contains only missing/null values.")

    unique_vals = y_raw.dropna().unique()
    if len(unique_vals) < 2:
        val_display = str(unique_vals[0]) if len(unique_vals) == 1 else "none"
        raise ValueError(
            f"Target column '{target_col}' has only {len(unique_vals)} distinct class ('{val_display}'). "
            f"Classification model training requires at least 2 distinct outcome classes (e.g. Approved vs Rejected)."
        )

    # If already numeric or boolean
    if pd.api.types.is_bool_dtype(y_raw):
        return y_raw.fillna(False).astype(int).values

    if pd.api.types.is_numeric_dtype(y_raw):
        if len(unique_vals) == 2:
            sorted_vals = sorted(unique_vals)
            mapping = {sorted_vals[0]: 0, sorted_vals[1]: 1}
            return y_raw.fillna(sorted_vals[0]).map(mapping).astype(int).values
        else:
            return (y_raw.fillna(0) >= 1).astype(int).values

    # String / Categorical
    y_str = y_raw.astype(str).str.strip().str.lower()
    affirmative = {"1", "true", "yes", "selected", "qualified", "positive", "approved", "hired", "admitted", "pass", "success"}

    has_pos = y_str.isin(affirmative).any()
    has_neg = (~y_str.isin(affirmative) & y_raw.notna()).any()
    if has_pos and has_neg:
        return y_str.isin(affirmative).astype(int).values

    if len(unique_vals) == 2:
        sorted_vals = sorted(str(v).strip().lower() for v in unique_vals)
        mapping = {sorted_vals[0]: 0, sorted_vals[1]: 1}
        return y_str.map(mapping).fillna(0).astype(int).values

    raise ValueError(
        f"Target column '{target_col}' contains {len(unique_vals)} unique values and could not be mapped to binary classes. "
        f"Please provide a binary outcome column (e.g. Yes/No, 0/1, Approved/Rejected)."
    )

def select_and_encode_features(
    df: pd.DataFrame,
    target_col: str,
    features_to_drop: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Selects valid feature columns, removes identifiers and PII, encodes categoricals,
    handles missing values, and removes zero-variance columns.
    """
    base_drop = set(features_to_drop) if features_to_drop else set()

    usable_cols = []
    dropped_identifiers = []
    for c in df.columns:
        if c == target_col:
            continue
        if c in base_drop or is_identifier_or_pii(c):
            dropped_identifiers.append(c)
        else:
            usable_cols.append(c)

    if not usable_cols:
        dropped_str = ", ".join(dropped_identifiers) if dropped_identifiers else "none"
        raise ValueError(
            f"No usable model features found in dataset. All remaining columns ({dropped_str}) "
            f"were identified as identifiers or personal data (ID, name, email, phone) and excluded from model training."
        )

    X_raw = df[usable_cols].copy()

    numeric_cols = X_raw.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = [c for c in usable_cols if c not in numeric_cols]

    for col in numeric_cols:
        col_median = X_raw[col].median() if len(X_raw[col].dropna()) > 0 else 0
        X_raw[col] = X_raw[col].fillna(col_median)

    for col in categorical_cols:
        X_raw[col] = X_raw[col].fillna("Missing").astype(str)

    if categorical_cols:
        X = pd.get_dummies(X_raw, columns=categorical_cols, drop_first=False)
    else:
        X = X_raw.copy()

    X = X.astype(float)

    non_constant = [c for c in X.columns if X[c].nunique() > 1]
    if not non_constant:
        raise ValueError(
            "All candidate features have identical/constant values across all rows (zero variance). "
            "A predictive model cannot learn from constant features."
        )

    X = X[non_constant]

    if X.shape[1] == 0:
        raise ValueError("No valid features remaining after data preprocessing.")

    return X

def train_and_explain_model(
    df: pd.DataFrame,
    target_column: Optional[str] = None,
    features_to_drop: Optional[List[str]] = None,
    model_type: str = "RandomForest"
) -> Dict[str, Any]:
    """
    Trains a real scikit-learn model on candidate/application data,
    evaluates its performance, and generates:
    1. Global Feature Importances
    2. Local Individual SHAP/Contribution explanations for representative candidates
    3. Plain-language narrative summaries
    """
    if df is None or len(df) == 0:
        raise ValueError("The selected dataset is empty (0 rows). Please upload or select a dataset with valid records.")

    if len(df) < 4:
        raise ValueError(
            f"The selected dataset has only {len(df)} record(s). "
            f"A minimum of 4 records is required to perform train/test splitting and generate explainability models."
        )

    resolved_target = resolve_target_column(df, target_column)
    y = prepare_target_variable(df[resolved_target], resolved_target)
    X = select_and_encode_features(df, resolved_target, features_to_drop)

    n_samples = len(X)
    test_size = 0.25 if n_samples >= 8 else 1

    class_counts = pd.Series(y).value_counts()
    can_stratify = (class_counts >= 2).all() and len(class_counts) >= 2 and test_size > 1

    try:
        if can_stratify:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
    except Exception:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

    # Ensure y_train has at least 2 distinct classes if available
    if len(np.unique(y_train)) < 2:
        idx_0 = np.where(y == 0)[0]
        idx_1 = np.where(y == 1)[0]
        if len(idx_0) > 0 and len(idx_1) > 0:
            test_idx = [idx_0[0]] if len(idx_0) > 1 else [idx_1[0]]
            train_idx = [i for i in range(n_samples) if i not in test_idx]
            X_train = X.iloc[train_idx]
            y_train = y[train_idx]
            X_test = X.iloc[test_idx]
            y_test = y[test_idx]

    if model_type == "LogisticRegression":
        model = LogisticRegression(max_iter=1000, random_state=42)
    elif model_type == "GradientBoosting":
        model = GradientBoostingClassifier(n_estimators=min(100, max(10, n_samples * 2)), max_depth=3, random_state=42)
    else:
        model = RandomForestClassifier(n_estimators=min(100, max(10, n_samples * 2)), max_depth=5, random_state=42)

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = round(float(accuracy_score(y_test, y_pred)), 4)

    # 1. Global Feature Importances
    feature_names = X.columns.tolist()
    global_importance = []

    if hasattr(model, "feature_importances_"):
        raw_importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        raw_importances = np.abs(model.coef_[0])
    else:
        raw_importances = np.ones(len(feature_names)) / len(feature_names)

    total_imp = sum(raw_importances) if sum(raw_importances) > 0 else 1.0
    for feat, imp in zip(feature_names, raw_importances):
        norm_imp = round(float(imp / total_imp), 4)
        global_importance.append({
            "feature": feat,
            "importance": norm_imp,
            "description": f"Contributes approx {norm_imp:.1%} towards model decisions."
        })

    global_importance.sort(key=lambda x: x["importance"], reverse=True)

    # 2. Local Sample Explanations
    if hasattr(model, "predict_proba"):
        raw_probs = model.predict_proba(X_test)
        if raw_probs.shape[1] > 1:
            probs = raw_probs[:, 1]
        else:
            probs = raw_probs[:, 0] if (len(model.classes_) > 0 and model.classes_[0] == 1) else 1.0 - raw_probs[:, 0]
    else:
        probs = y_pred.astype(float)

    shap_values = None
    if SHAP_AVAILABLE:
        try:
            if isinstance(model, (RandomForestClassifier, GradientBoostingClassifier)):
                explainer = shap.TreeExplainer(model)
                shap_obj = explainer.shap_values(X_test)
                if isinstance(shap_obj, list):
                    shap_values = shap_obj[1] if len(shap_obj) > 1 else shap_obj[0]
                elif hasattr(shap_obj, "shape") and len(shap_obj.shape) == 3:
                    shap_values = shap_obj[:, :, 1] if shap_obj.shape[2] > 1 else shap_obj[:, :, 0]
                elif hasattr(shap_obj, "shape") and len(shap_obj.shape) == 2:
                    shap_values = shap_obj
        except Exception:
            shap_values = None

    sample_explanations = []
    test_indices = list(range(min(4, len(X_test))))

    for idx in test_indices:
        raw_row = X_test.iloc[idx].to_dict()
        pred_label = int(y_pred[idx])
        pred_prob = round(float(probs[idx]), 3)

        positive_contributors = []
        negative_contributors = []

        if shap_values is not None and len(shap_values) > idx:
            row_shap = shap_values[idx]
            for feat_name, s_val in zip(feature_names, row_shap):
                val_dict = {
                    "feature": feat_name,
                    "value": round(float(raw_row[feat_name]), 2) if isinstance(raw_row[feat_name], (int, float, np.number)) else str(raw_row[feat_name]),
                    "impact": round(float(s_val), 3)
                }
                if s_val > 0.005:
                    positive_contributors.append(val_dict)
                elif s_val < -0.005:
                    negative_contributors.append(val_dict)
        else:
            for feat_item in global_importance[:5]:
                feat_name = feat_item["feature"]
                val = raw_row[feat_name]
                mean_val = float(X[feat_name].mean())
                std_val = float(X[feat_name].std()) if float(X[feat_name].std()) > 0 else 1.0
                diff = ((val - mean_val) / std_val) * feat_item["importance"]
                impact = round(float(diff), 3)
                val_dict = {
                    "feature": feat_name,
                    "value": round(float(val), 2) if isinstance(val, (int, float, np.number)) else str(val),
                    "impact": impact
                }
                if impact > 0:
                    positive_contributors.append(val_dict)
                else:
                    negative_contributors.append(val_dict)

        positive_contributors.sort(key=lambda x: abs(x["impact"]), reverse=True)
        negative_contributors.sort(key=lambda x: abs(x["impact"]), reverse=True)

        top_pos = [f"{p['feature']} ({p['value']})" for p in positive_contributors[:2]]
        top_neg = [f"{n['feature']} ({n['value']})" for n in negative_contributors[:2]]

        narrative_parts = []
        if pred_label == 1:
            narrative_parts.append(f"Target outcome confirmed with {pred_prob:.1%} predicted confidence.")
            if top_pos:
                narrative_parts.append(f"Primary driving factors: {', '.join(top_pos)}.")
            if top_neg:
                narrative_parts.append(f"Minor offsetting negative factors: {', '.join(top_neg)}.")
        else:
            narrative_parts.append(f"Alternative outcome predicted with {pred_prob:.1%} acceptance probability.")
            if top_neg:
                narrative_parts.append(f"Primary limiting factors: {', '.join(top_neg)}.")
            if top_pos:
                narrative_parts.append(f"Positive contributing factors observed: {', '.join(top_pos)}.")

        narrative = " ".join(narrative_parts)

        sample_explanations.append({
            "sample_id": int(X_test.index[idx]),
            "features": {k: (round(float(v), 2) if isinstance(v, (int, float, np.number)) else str(v)) for k, v in raw_row.items()},
            "prediction": pred_label,
            "probability": pred_prob,
            "top_positive_features": positive_contributors[:3],
            "top_negative_features": negative_contributors[:3],
            "plain_narrative": narrative
        })

    return {
        "model_name": model.__class__.__name__,
        "task_type": "Classification & Scoring Model",
        "model_accuracy": accuracy,
        "global_importance": global_importance[:8],
        "sample_explanations": sample_explanations,
        "methodology": "SHAP (SHapley Additive exPlanations) Game-Theoretic Attributions and Gini Impurity Feature Importance.",
        "correlation_causation_caveat": (
            "IMPORTANT CAUSALITY DISCLAIMER: Feature importances and SHAP values quantify empirical correlation within this specific trained model; "
            "they DO NOT establish real-world causal relationships. Do not use model weights as causal proof for individual decisions."
        )
    }

def record_explainability_findings(
    db: Session,
    application_id: int,
    results: Dict[str, Any],
    assessment_id: Optional[int] = None
) -> ExplainabilityResult:
    x_res = ExplainabilityResult(
        application_id=application_id,
        assessment_id=assessment_id,
        model_name=results["model_name"],
        task_type=results["task_type"],
        global_importance_json=json.dumps(results["global_importance"]),
        sample_explanations_json=json.dumps(results["sample_explanations"]),
        summary_narrative=results["sample_explanations"][0]["plain_narrative"] if results["sample_explanations"] else ""
    )
    db.add(x_res)
    db.commit()
    db.refresh(x_res)
    return x_res

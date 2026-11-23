import json
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

try:
    from fairlearn.metrics import (
        demographic_parity_difference,
        demographic_parity_ratio,
        equal_opportunity_difference,
        selection_rate,
        MetricFrame,
        true_positive_rate,
        false_positive_rate
    )
    FAIRLEARN_AVAILABLE = True
except ImportError:
    FAIRLEARN_AVAILABLE = False

from ..models import FairnessResult, Risk, Recommendation
from sqlalchemy.orm import Session

def analyze_fairness(
    df: pd.DataFrame,
    sensitive_column: str,
    target_column: str,
    favorable_outcome: Any,
    qualified_column: Optional[str] = "qualified"
) -> Dict[str, Any]:
    """
    Computes rigorous fairness metrics across protected demographic groups.
    Supports binary and multi-group sensitive attributes.
    """
    if sensitive_column not in df.columns:
        raise ValueError(f"Sensitive column '{sensitive_column}' not found in dataset.")
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataset.")

    # Convert target to binary indicator (1 = favorable outcome, 0 = unfavorable)
    # Handle cases where favorable_outcome is string or int or boolean
    y_true_binary = (df[target_column].astype(str).str.strip().str.lower() == str(favorable_outcome).strip().lower()).astype(int)
    sensitive_series = df[sensitive_column].astype(str).str.strip()

    total_samples = len(df)
    groups = sorted(sensitive_series.unique().tolist())

    group_metrics = []
    group_rates = {}

    # Check if a ground-truth qualification column exists (e.g., 'qualified')
    has_ground_truth = (
        qualified_column in df.columns and 
        qualified_column != target_column
    )
    y_ground_truth = None
    if has_ground_truth:
        y_ground_truth = (df[qualified_column].astype(str).str.strip().str.lower().isin(["1", "true", "yes", "qualified"])).astype(int)

    for g in groups:
        mask = (sensitive_series == g)
        sub_y = y_true_binary[mask]
        g_count = int(mask.sum())
        pos_count = int(sub_y.sum())
        rate = round(pos_count / g_count, 4) if g_count > 0 else 0.0
        group_rates[g] = rate

        metric_entry = {
            "group": g,
            "total_count": g_count,
            "positive_count": pos_count,
            "selection_rate": rate,
            "tpr": None,
            "fpr": None,
            "tnr": None,
            "fnr": None
        }

        if has_ground_truth:
            sub_gt = y_ground_truth[mask]
            # TP: GT=1, Selected=1
            # FP: GT=0, Selected=1
            # TN: GT=0, Selected=0
            # FN: GT=1, Selected=0
            tp = int(((sub_gt == 1) & (sub_y == 1)).sum())
            fp = int(((sub_gt == 0) & (sub_y == 1)).sum())
            tn = int(((sub_gt == 0) & (sub_y == 0)).sum())
            fn = int(((sub_gt == 1) & (sub_y == 0)).sum())

            actual_pos = tp + fn
            actual_neg = tn + fp
            tpr = round(tp / actual_pos, 4) if actual_pos > 0 else 0.0
            fpr = round(fp / actual_neg, 4) if actual_neg > 0 else 0.0
            tnr = round(tn / actual_neg, 4) if actual_neg > 0 else 0.0
            fnr = round(fn / actual_pos, 4) if actual_pos > 0 else 0.0

            metric_entry.update({
                "tpr": tpr,
                "fpr": fpr,
                "tnr": tnr,
                "fnr": fnr
            })

        group_metrics.append(metric_entry)

    # Compute Demographic Parity Metrics
    if FAIRLEARN_AVAILABLE:
        try:
            dp_diff = round(float(demographic_parity_difference(y_true_binary, y_true_binary, sensitive_features=sensitive_series)), 4)
            dp_ratio = round(float(demographic_parity_ratio(y_true_binary, y_true_binary, sensitive_features=sensitive_series)), 4)
        except Exception:
            dp_diff = round(max(group_rates.values()) - min(group_rates.values()), 4)
            dp_ratio = round(min(group_rates.values()) / max(group_rates.values()), 4) if max(group_rates.values()) > 0 else 1.0
    else:
        dp_diff = round(max(group_rates.values()) - min(group_rates.values()), 4)
        dp_ratio = round(min(group_rates.values()) / max(group_rates.values()), 4) if max(group_rates.values()) > 0 else 1.0

    # Compute Equal Opportunity Difference if ground truth is available
    eq_opp_diff = None
    if has_ground_truth and FAIRLEARN_AVAILABLE:
        try:
            eq_opp_diff = round(float(equal_opportunity_difference(
                y_ground_truth,
                y_true_binary,
                sensitive_features=sensitive_series
            )), 4)
        except Exception:
            # Fallback calculation
            tprs = [m["tpr"] for m in group_metrics if m["tpr"] is not None]
            if tprs:
                eq_opp_diff = round(max(tprs) - min(tprs), 4)
    elif has_ground_truth:
        tprs = [m["tpr"] for m in group_metrics if m["tpr"] is not None]
        if tprs:
            eq_opp_diff = round(max(tprs) - min(tprs), 4)

    # 4/5ths Rule Evaluation (EEOC 80% rule: ratio should be >= 0.80)
    four_fifths_passed = bool(dp_ratio >= 0.80)

    # Determine Risk Level
    if dp_ratio < 0.60 or dp_diff > 0.25:
        risk_level = "Critical"
    elif dp_ratio < 0.80 or dp_diff > 0.15:
        risk_level = "High"
    elif dp_ratio < 0.90 or dp_diff > 0.08:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # Actionable Recommendations
    recommendations = []
    if not four_fifths_passed:
        recommendations.append(
            f"Violates the EEOC 4/5ths (80%) Rule: Disparity ratio is {dp_ratio:.1%} (below the 80% threshold). Conduct root-cause inspection on qualification thresholds."
        )
    if eq_opp_diff is not None and eq_opp_diff > 0.15:
        recommendations.append(
            f"Significant Equal Opportunity disparity ({eq_opp_diff:.1%}). Qualified individuals in disadvantaged groups have a noticeably lower true positive selection rate."
        )
    recommendations.extend([
        "Perform pre-processing re-weighting or threshold adjustment on model outputs to equalize selection rates without sacrificing model utility.",
        "Audit features for indirect proxy variables that correlate with protected demographic traits (e.g. zip code, continuous career gaps).",
        "Implement human oversight for borderline candidates in historically disadvantaged groups."
    ])

    limitations = [
        "Demographic parity measures outcome equality but does not evaluate individual qualification distribution or market applicant base.",
        "Small subgroup sample sizes (n < 30) exhibit higher statistical variance and may generate unrepresentative disparity metrics.",
        "Fairness in algorithmic decision-making cannot be certified by any single metric alone; qualitative process evaluation is required.",
        "Protected attributes should never be inferred from unstructured data like candidate names, zip codes, or photos."
    ]

    return {
        "sensitive_attribute": sensitive_column,
        "target_attribute": target_column,
        "favorable_outcome": str(favorable_outcome),
        "total_samples": total_samples,
        "groups": groups,
        "group_metrics": group_metrics,
        "demographic_parity_diff": dp_diff,
        "demographic_parity_ratio": dp_ratio,
        "equal_opportunity_diff": eq_opp_diff,
        "four_fifths_rule_passed": four_fifths_passed,
        "risk_level": risk_level,
        "recommendations": recommendations,
        "limitations": limitations
    }

def record_fairness_findings(
    db: Session,
    application_id: int,
    results: Dict[str, Any],
    dataset_id: Optional[int] = None,
    assessment_id: Optional[int] = None
) -> FairnessResult:
    """Saves fairness analysis into database and creates associated Risks if severe."""
    f_res = FairnessResult(
        application_id=application_id,
        assessment_id=assessment_id,
        dataset_id=dataset_id,
        sensitive_attribute=results["sensitive_attribute"],
        target_attribute=results["target_attribute"],
        favorable_outcome=results["favorable_outcome"],
        demographic_parity_diff=results["demographic_parity_diff"],
        demographic_parity_ratio=results["demographic_parity_ratio"],
        equal_opportunity_diff=results["equal_opportunity_diff"],
        group_metrics_json=json.dumps(results["group_metrics"]),
        confusion_matrices_json=json.dumps([m for m in results["group_metrics"] if m.get("tpr") is not None]),
        risk_level=results["risk_level"],
        recommendations_json=json.dumps(results["recommendations"])
    )
    db.add(f_res)

    # If fairness disparity is High or Critical, add to central Risk Center
    if results["risk_level"] in ["High", "Critical"]:
        risk = Risk(
            application_id=application_id,
            assessment_id=assessment_id,
            title=f"Algorithmic Disparity Detected across {results['sensitive_attribute']}",
            description=(
                f"Statistical audit found demographic parity ratio of {results['demographic_parity_ratio']:.2f} "
                f"(parity difference {results['demographic_parity_diff']:.2f}) across {results['sensitive_attribute']} groups. "
                f"EEOC 4/5ths rule is {'PASSED' if results['four_fifths_rule_passed'] else 'VIOLATED'}."
            ),
            source_module="fairness",
            severity=results["risk_level"],
            evidence=f"Demographic parity ratio = {results['demographic_parity_ratio']:.2f}; Disparity diff = {results['demographic_parity_diff']:.2f}; Total audited = {results['total_samples']}.",
            business_impact="Legal exposure under anti-discrimination statutes (e.g. Title VII, NYC Local Law 144, EU AI Act) and reputational damage.",
            recommended_action="Recalibrate selection score thresholds, remove proxy bias features, and mandate human review for marginalized demographic groups.",
            status="Open"
        )
        db.add(risk)

    db.commit()
    db.refresh(f_res)
    return f_res

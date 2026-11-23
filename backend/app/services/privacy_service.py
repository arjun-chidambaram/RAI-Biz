import re
import json
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from ..models import PrivacyFinding, Risk
from sqlalchemy.orm import Session

# Robust regex patterns for preliminary PII screening
PATTERNS = {
    "Email Address": {
        "regex": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'),
        "severity": "Medium",
        "mask": lambda val: val[:2] + "***@" + val.split("@")[-1] if "@" in val else "***@***.com"
    },
    "Phone Number": {
        "regex": re.compile(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b'),
        "severity": "High",
        "mask": lambda val: "***-***-" + val.strip()[-4:] if len(val.strip()) >= 4 else "***-****"
    },
    "Social Security / National ID": {
        "regex": re.compile(r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'),
        "severity": "Critical",
        "mask": lambda val: "***-**-" + val.strip()[-4:] if len(val.strip()) >= 4 else "***-**-****"
    },
    "Credit Card Number": {
        "regex": re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
        "severity": "Critical",
        "mask": lambda val: "****-****-****-" + val.strip()[-4:] if len(val.strip()) >= 4 else "****-****"
    },
    "IPv4 Address": {
        "regex": re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'),
        "severity": "Low",
        "mask": lambda val: "xxx.xxx." + ".".join(val.split(".")[-2:]) if "." in val else "xxx.xxx.xxx.xxx"
    }
}

# Suspicious column name patterns indicative of high-risk PII
SUSPICIOUS_COLUMNS = {
    "ssn": "Social Security Number / Tax ID",
    "social": "Social Security Number",
    "national_id": "National Identification Number",
    "passport": "Passport Number",
    "card_number": "Payment Card",
    "cvv": "Card Verification Code",
    "dob": "Date of Birth",
    "birth": "Date of Birth",
    "phone": "Telephone Number",
    "mobile": "Mobile Number",
    "email": "Email Address",
    "salary": "Compensation / Salary Record",
    "medical": "Health / Medical Data",
    "health": "Health / Medical Data",
    "password": "Password / Credential",
    "secret": "Confidential Token"
}

def scan_dataframe_privacy(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Performs high-speed heuristic PII scanning without persisting raw sensitive values.
    Returns aggregated detection counts, masked samples, missing values, duplicates,
    and data minimization alerts.
    """
    total_records = len(df)
    pii_findings = []
    data_minimization_alerts = []
    
    # 1. Missing values and duplicates check
    missing_summary = df.isnull().sum().to_dict()
    duplicate_rows = int(df.duplicated().sum())

    # 2. Column-level minimization and keyword heuristics
    for col in df.columns:
        col_lower = str(col).lower().replace(" ", "_").replace("-", "_")
        for key, description in SUSPICIOUS_COLUMNS.items():
            if key in col_lower:
                data_minimization_alerts.append(
                    f"Column '{col}' matches high-sensitivity identifier pattern '{description}'. Verify whether model genuinely requires this attribute or if it breaches Data Minimization."
                )

        # High cardinality ratio check (e.g., unique ID or free-text column)
        unique_count = df[col].nunique()
        if unique_count > total_records * 0.95 and total_records > 20 and df[col].dtype == object:
            data_minimization_alerts.append(
                f"Column '{col}' exhibits near 100% unique textual cardinality ({unique_count}/{total_records}). High risk of containing unindexed direct identifiers or personal names."
            )

    # 3. Value-level regex pattern scanning (inspect up to first 250 rows for performance and privacy)
    sample_size = min(total_records, 250)
    sample_df = df.head(sample_size)
    total_pii_detected = 0

    for col in df.columns:
        # Check string or object columns
        series_str = sample_df[col].dropna().astype(str)
        if series_str.empty:
            continue

        for pii_name, meta in PATTERNS.items():
            pattern = meta["regex"]
            matches = []
            for val in series_str:
                m = pattern.search(val)
                if m:
                    matches.append((val, m.group(0)))

            if matches:
                total_pii_detected += len(matches)
                # Take first matched item and securely MASK it
                raw_match = matches[0][1]
                masked_val = meta["mask"](raw_match)
                
                pii_findings.append({
                    "column": str(col),
                    "pii_type": pii_name,
                    "sample_masked": masked_val,
                    "match_count": len(matches),
                    "risk_severity": meta["severity"]
                })

    # Determine Overall Privacy Risk Level
    severities = [f["risk_severity"] for f in pii_findings]
    if "Critical" in severities or len(data_minimization_alerts) >= 3:
        risk_level = "Critical"
    elif "High" in severities or len(pii_findings) >= 3:
        risk_level = "High"
    elif "Medium" in severities or duplicate_rows > 0 or len(data_minimization_alerts) >= 1:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    governance_checklist = {
        "Data Minimization Protocol": "At Risk" if data_minimization_alerts else "Compliant",
        "Direct PII Ingestion Screening": "Action Required" if pii_findings else "Clean",
        "Data Hygiene & Deduplication": f"{duplicate_rows} duplicate rows detected" if duplicate_rows > 0 else "Verified Clean",
        "Completeness & Missingness": f"{sum(missing_summary.values())} missing cells detected" if sum(missing_summary.values()) > 0 else "100% Complete"
    }

    disclaimer = (
        "PRELIMINARY TECHNICAL SCREENING DISCLAIMER: This automated scan provides heuristic pattern-matching and data hygiene checks. "
        "It does NOT constitute formal legal advice, statutory privacy certification, or an official GDPR/CCPA compliance audit."
    )

    return {
        "total_records_scanned": total_records,
        "pii_detected_count": total_pii_detected,
        "findings": pii_findings,
        "missing_summary": missing_summary,
        "duplicate_rows": duplicate_rows,
        "data_minimization_alerts": data_minimization_alerts,
        "governance_checklist_status": governance_checklist,
        "risk_level": risk_level,
        "disclaimer": disclaimer
    }

def record_privacy_findings(
    db: Session,
    application_id: int,
    results: Dict[str, Any],
    dataset_id: Optional[int] = None,
    assessment_id: Optional[int] = None
) -> PrivacyFinding:
    p_res = PrivacyFinding(
        application_id=application_id,
        assessment_id=assessment_id,
        dataset_id=dataset_id,
        total_records_scanned=results["total_records_scanned"],
        pii_detected_count=results["pii_detected_count"],
        findings_json=json.dumps(results["findings"]),
        missing_duplicate_stats_json=json.dumps({
            "missing_summary": results["missing_summary"],
            "duplicate_rows": results["duplicate_rows"]
        }),
        data_minimization_alerts_json=json.dumps(results["data_minimization_alerts"]),
        risk_level=results["risk_level"]
    )
    db.add(p_res)

    # Generate Risk entries in Central Risk Center if High or Critical
    if results["risk_level"] in ["High", "Critical"]:
        found_types = list(set([f["pii_type"] for f in results["findings"]]))
        risk = Risk(
            application_id=application_id,
            assessment_id=assessment_id,
            title="Unsanitized Personal Identifiable Information (PII) in AI Pipeline",
            description=(
                f"Automated screening detected direct personal identifiers ({', '.join(found_types)}) across dataset columns. "
                f"Total {results['pii_detected_count']} matches identified without de-identification or masking."
            ),
            source_module="privacy",
            severity=results["risk_level"],
            evidence=f"Masked samples: {', '.join([f['sample_masked'] for f in results['findings'][:3]])}. Total scanned: {results['total_records_scanned']}.",
            business_impact="Heightened breach liability under GDPR Article 5(1)(c) / CCPA, civil penalties, and non-compliance fines.",
            recommended_action="Execute automated PII redaction pipeline, drop non-essential identifying attributes, and encrypt remaining quasi-identifiers at rest.",
            status="Open"
        )
        db.add(risk)

    db.commit()
    db.refresh(p_res)
    return p_res

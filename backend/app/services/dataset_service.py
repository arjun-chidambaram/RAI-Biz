import os
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple
from fastapi import HTTPException
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from ..models import Dataset, DatasetRecord, IngestionLog
from ..config import settings
from .storage_service import (
    save_dataset_file,
    load_dataset_dataframe,
    get_storage_key,
    extract_storage_basename,
    DatasetFileNotFoundError
)

def calculate_checksum(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()

def save_and_ingest_dataset(
    db: Session,
    file_bytes: bytes,
    original_filename: str,
    application_id: Optional[int] = None
) -> Dataset:
    """Saves file to uploads directory, parses metadata with pandas, and records in database."""
    checksum = calculate_checksum(file_bytes)
    safe_name, storage_key, target_path = save_dataset_file(file_bytes, original_filename)

    # Load into pandas based on file extension
    ext = original_filename.lower().split(".")[-1]
    if ext == "json":
        df = pd.read_json(target_path)
    else:
        # Default CSV
        df = pd.read_csv(target_path)

    row_count = len(df)
    col_count = len(df.columns)

    schema_info = {
        "columns": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "sample_row": df.head(1).to_dict(orient="records")[0] if row_count > 0 else {}
    }

    dataset = Dataset(
        application_id=application_id,
        filename=safe_name,
        original_filename=original_filename,
        file_path=storage_key,
        file_size_bytes=len(file_bytes),
        row_count=row_count,
        column_count=col_count,
        checksum=checksum,
        schema_json=json.dumps(schema_info),
        schema_version="1.0",
        status="Uploaded"
    )
    db.add(dataset)
    db.flush()

    # Save sample records (first 5 rows)
    for idx, row in df.head(5).iterrows():
        rec = DatasetRecord(
            dataset_id=dataset.id,
            record_type="sample",
            row_index=int(idx),
            raw_data_json=json.dumps(row.to_dict(), default=str)
        )
        db.add(rec)

    # Log ingestion audit
    log = IngestionLog(
        dataset_id=dataset.id,
        event_type="DATASET_UPLOADED",
        details_json=json.dumps({
            "rows": row_count,
            "columns": col_count,
            "filename": original_filename,
            "checksum": checksum
        })
    )
    db.add(log)
    db.commit()
    db.refresh(dataset)
    return dataset

def get_dataset_preview(db: Session, dataset_id: int) -> Dict[str, Any]:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = load_dataset_dataframe(dataset)
    
    missing_counts = df.isnull().sum().to_dict()
    duplicate_count = int(df.duplicated().sum())

    # Replace NaN with None for clean JSON serialization
    clean_head = df.head(15).replace({np.nan: None}).to_dict(orient="records")

    return {
        "dataset_id": dataset.id,
        "filename": dataset.original_filename,
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "head": clean_head,
        "missing_counts": missing_counts,
        "duplicate_count": duplicate_count
    }

def clean_dataset(
    db: Session,
    dataset_id: int,
    drop_duplicates: bool = True,
    fill_missing_numeric: str = "median",
    fill_missing_categorical: str = "mode"
) -> Tuple[Dataset, int, int]:
    """
    Cleans dataset using specified options, quarantines rejected records,
    and updates the dataset status.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = load_dataset_dataframe(dataset)
    initial_rows = len(df)
    rejected_records = []

    # 1. Duplicates
    if drop_duplicates:
        dups_mask = df.duplicated()
        dup_rows = df[dups_mask]
        for idx, row in dup_rows.iterrows():
            rejected_records.append({
                "index": int(idx),
                "data": row.to_dict(),
                "reason": "Duplicate row removed during deduplication"
            })
        df = df[~dups_mask].reset_index(drop=True)

    # 2. Missing numeric values
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        if df[col].isnull().sum() > 0:
            if fill_missing_numeric == "mean":
                df[col] = df[col].fillna(df[col].mean())
            elif fill_missing_numeric == "median":
                df[col] = df[col].fillna(df[col].median())
            elif fill_missing_numeric == "drop":
                null_mask = df[col].isnull()
                for idx, row in df[null_mask].iterrows():
                    rejected_records.append({
                        "index": int(idx),
                        "data": row.to_dict(),
                        "reason": f"Missing numeric value in column '{col}'"
                    })
                df = df[~null_mask].reset_index(drop=True)

    # 3. Missing categorical values
    cat_cols = df.select_dtypes(exclude=[np.number]).columns
    for col in cat_cols:
        if df[col].isnull().sum() > 0:
            if fill_missing_categorical == "mode":
                mode_val = df[col].mode()[0] if not df[col].mode().empty else "Unknown"
                df[col] = df[col].fillna(mode_val)
            elif fill_missing_categorical == "unknown":
                df[col] = df[col].fillna("Unknown")
            elif fill_missing_categorical == "drop":
                null_mask = df[col].isnull()
                for idx, row in df[null_mask].iterrows():
                    rejected_records.append({
                        "index": int(idx),
                        "data": row.to_dict(),
                        "reason": f"Missing categorical value in column '{col}'"
                    })
                df = df[~null_mask].reset_index(drop=True)

    # Save cleaned file back
    clean_base = extract_storage_basename(dataset.filename)
    cleaned_filename = f"cleaned_{clean_base}"
    cleaned_path = settings.UPLOAD_DIR / cleaned_filename
    df.to_csv(cleaned_path, index=False)

    # Save rejected records in db
    for rec in rejected_records:
        r_obj = DatasetRecord(
            dataset_id=dataset.id,
            record_type="rejected",
            row_index=rec["index"],
            raw_data_json=json.dumps(rec["data"], default=str),
            rejection_reason=rec["reason"]
        )
        db.add(r_obj)

    # Update dataset
    dataset.file_path = get_storage_key(cleaned_filename)
    dataset.row_count = len(df)
    dataset.status = "Cleaned"
    
    # Audit log
    log = IngestionLog(
        dataset_id=dataset.id,
        event_type="DATASET_CLEANED",
        details_json=json.dumps({
            "initial_rows": initial_rows,
            "cleaned_rows": len(df),
            "rejected_count": len(rejected_records)
        })
    )
    db.add(log)
    db.commit()
    db.refresh(dataset)

    return dataset, len(df), len(rejected_records)

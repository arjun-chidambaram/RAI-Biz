import os
import hashlib
from pathlib import Path
from typing import Optional, Union, Any, Tuple
import pandas as pd
from fastapi import HTTPException
from ..config import settings


class DatasetFileNotFoundError(HTTPException):
    """
    Raised when a dataset's underlying physical file cannot be found on the server.
    Inherits from HTTPException(404) so FastAPI automatically returns an actionable JSON error.
    """
    def __init__(self, display_name: str, raw_path: Optional[str] = None):
        message = (
            f"Dataset file '{display_name}' is not available on the server. "
            "Please upload the dataset again through the deployed application."
        )
        super().__init__(status_code=404, detail=message)
        self.display_name = display_name
        self.raw_path = raw_path


def extract_storage_basename(raw_path: Optional[str]) -> str:
    """
    Extracts the filename/basename from any path string (Windows absolute,
    Windows relative, POSIX absolute, POSIX relative, or plain filename).
    Handles Windows paths safely even when executing in a Linux container (e.g. Render).
    """
    if not raw_path:
        return ""
    normalized = str(raw_path).replace("\\", "/").rstrip("/")
    return normalized.split("/")[-1]


def get_storage_key(filename: str) -> str:
    """
    Returns a normalized, relative storage key for database storage (e.g. 'uploads/data.csv').
    """
    clean_name = extract_storage_basename(filename)
    return f"uploads/{clean_name}"


def resolve_dataset_path(
    raw_path: Optional[str],
    filename: Optional[str] = None
) -> Optional[Path]:
    """
    Resolves a dataset file path safely across environments (Windows local, Linux/Render).

    Candidate search order:
    1. Direct file existence check (if raw_path is valid on the current operating system).
    2. settings.UPLOAD_DIR / basename
    3. settings.UPLOAD_DIR / stripped relative path
    4. settings.BASE_DIR / raw_path (if raw_path is relative to backend root)
    5. settings.DATA_DIR / basename (bundled app data / seed datasets)
    6. settings.BASE_DIR / "uploads" / basename

    Returns resolved Path if the file exists on disk, else None.
    """
    candidates = []

    # 1. Direct check if path exists on this OS
    if raw_path:
        try:
            p = Path(raw_path)
            if p.is_file():
                return p.resolve()
        except Exception:
            pass

    # Extract clean basename
    basename = extract_storage_basename(filename) if filename else ""
    if not basename and raw_path:
        basename = extract_storage_basename(raw_path)

    if not basename:
        return None

    # 2. Configurable UPLOAD_DIR / basename
    candidates.append(settings.UPLOAD_DIR / basename)

    # 3. If raw_path has relative path e.g. "uploads/foo.csv"
    if raw_path:
        norm_raw = str(raw_path).replace("\\", "/").lstrip("/")
        if norm_raw.startswith("uploads/"):
            subname = norm_raw[len("uploads/"):]
            candidates.append(settings.UPLOAD_DIR / subname)
        candidates.append(settings.BASE_DIR / norm_raw)

    # 4. DATA_DIR / basename (bundled seed data for production / Render)
    candidates.append(settings.DATA_DIR / basename)

    # 5. Default backend/uploads / basename fallback
    candidates.append(settings.BASE_DIR / "uploads" / basename)

    # Search candidates in order
    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate.resolve()
        except Exception:
            continue

    return None


def get_resolved_dataset_path(dataset: Any) -> Path:
    """
    Resolves dataset file path. Raises DatasetFileNotFoundError (404) if the file
    cannot be located on the server filesystem.
    """
    raw_path = getattr(dataset, "file_path", str(dataset) if dataset else None)
    filename = getattr(dataset, "filename", None)
    resolved = resolve_dataset_path(raw_path, filename=filename)

    if not resolved or not resolved.is_file():
        display_name = (
            getattr(dataset, "original_filename", None)
            or getattr(dataset, "filename", None)
            or extract_storage_basename(raw_path)
            or "dataset"
        )
        raise DatasetFileNotFoundError(display_name=display_name, raw_path=raw_path)

    return resolved


def load_dataset_dataframe(dataset: Any) -> pd.DataFrame:
    """
    Loads dataset into a pandas DataFrame from resolved storage path.
    Supports CSV and JSON formats.
    Raises DatasetFileNotFoundError if file is not found.
    """
    if isinstance(dataset, pd.DataFrame):
        return dataset

    resolved_path = get_resolved_dataset_path(dataset)
    ext = resolved_path.suffix.lower()
    if ext == ".json":
        return pd.read_json(resolved_path)
    return pd.read_csv(resolved_path)


def save_dataset_file(
    file_bytes: bytes,
    original_filename: str
) -> Tuple[str, str, Path]:
    """
    Saves uploaded file bytes to settings.UPLOAD_DIR with SHA-256 prefix for immutability.
    Returns (safe_name, storage_key, target_path).
    """
    checksum = hashlib.sha256(file_bytes).hexdigest()
    clean_original = extract_storage_basename(original_filename).replace(" ", "_")
    safe_name = f"{checksum[:12]}_{clean_original}"
    target_path = settings.UPLOAD_DIR / safe_name

    with open(target_path, "wb") as f:
        f.write(file_bytes)

    storage_key = get_storage_key(safe_name)
    return safe_name, storage_key, target_path

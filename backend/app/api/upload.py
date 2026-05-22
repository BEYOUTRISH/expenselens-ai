"""
File Upload API - Handles CSV/XLSX upload, parsing, preview
"""

import os
import uuid
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
import pandas as pd
import chardet

from app.core.config import settings
from app.core.session_store import get_session, set_session, session_exists

logger = logging.getLogger(__name__)
router = APIRouter()


def detect_encoding(file_path: str) -> str:
    with open(file_path, "rb") as f:
        raw = f.read(min(100000, Path(file_path).stat().st_size))
    result = chardet.detect(raw)
    return result.get("encoding", "utf-8")


def detect_delimiter(file_path: str, encoding: str = "utf-8") -> str:
    with open(file_path, "r", encoding=encoding, errors="ignore") as f:
        first_line = f.readline()
    if "\t" in first_line:
        return "\t"
    if ";" in first_line:
        return ";"
    return ","


def parse_file(file_path: str) -> pd.DataFrame:
    ext = Path(file_path).suffix.lower()
    if ext == ".csv":
        enc = detect_encoding(file_path)
        delim = detect_delimiter(file_path, enc)
        try:
            df = pd.read_csv(file_path, encoding=enc, delimiter=delim, dtype=str, keep_default_na=False)
        except Exception:
            df = pd.read_csv(file_path, encoding="utf-8", delimiter=delim, dtype=str, keep_default_na=False, errors="replace")
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path, dtype=str, keep_default_na=False)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
    df.columns = df.columns.str.strip()
    return df


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix.lower()

    if ext not in settings.allowed_extensions:
        raise HTTPException(400, f"Unsupported format: {ext}. Allowed: {settings.allowed_extensions}")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(exist_ok=True)
    file_path = str(upload_dir / f"{session_id}{ext}")

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        df = parse_file(file_path)
    except Exception as e:
        raise HTTPException(400, f"Failed to parse file: {str(e)}")

    set_session(session_id, {
        "file_path": file_path,
        "original_name": file.filename,
        "rows": len(df),
        "columns": list(df.columns),
        "df": df,
    })

    preview = df.head(50).to_dict(orient="records")

    return {
        "session_id": session_id,
        "filename": file.filename,
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
        "preview": preview,
    }


@router.get("/upload/{session_id}/preview")
async def get_preview(session_id: str, rows: int = Query(50, le=200)):
    session = get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    df = session["df"]
    preview = df.head(rows).to_dict(orient="records")
    return {
        "session_id": session_id,
        "total_rows": len(df),
        "columns": list(df.columns),
        "preview": preview,
    }

"""
Cleaning API - Run cleaning pipeline, get quality report, apply fixes
"""

import logging
import math
import pandas as pd
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.session_store import get_session, set_session
from app.services.cleaning.engine import ExpenseCleaner

logger = logging.getLogger(__name__)
router = APIRouter()


def _sanitize(records: list[dict]) -> list[dict]:
    for rec in records:
        for k, v in rec.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                rec[k] = None
    return records


class FixRequest(BaseModel):
    txn_ref: str
    field: str
    new_value: str


@router.post("/cleaning/run/{session_id}")
async def run_cleaning(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    df = session.get("df")
    if df is None:
        raise HTTPException(400, "No data in session")

    cleaner = ExpenseCleaner()
    cleaned_df = cleaner.clean_dataframe(df)

    session["cleaned_df"] = cleaned_df
    session["quality_report"] = cleaner.get_report()
    set_session(session_id, session)

    return {
        "session_id": session_id,
        "total_rows_in_source": len(df),
        "rows_loaded": cleaner.quality_report["rows_loaded"],
        "rows_excluded": cleaner.quality_report["rows_excluded"],
        "summary": cleaner.quality_report["summary"],
        "cleaned_preview": _sanitize(cleaned_df.head(50).to_dict(orient="records")),
    }


@router.get("/cleaning/quality-report/{session_id}")
async def get_quality_report(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    report = session.get("quality_report")
    if not report:
        raise HTTPException(400, "Run cleaning first")
    return report


@router.post("/cleaning/fix/{session_id}")
async def apply_fix(session_id: str, fix: FixRequest):
    session = get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    cleaned_df = session.get("cleaned_df")
    if cleaned_df is None:
        raise HTTPException(400, "Run cleaning first")

    mask = cleaned_df["txn_ref"] == fix.txn_ref
    if not mask.any():
        raise HTTPException(404, f"Transaction {fix.txn_ref} not found")

    cleaned_df.loc[mask, fix.field] = fix.new_value

    report = session.get("quality_report", {})
    report["issues"] = [
        i for i in report.get("issues", [])
        if not (i["txn_id"] == fix.txn_ref and i["field"] == fix.field)
    ]
    session["quality_report"] = report
    set_session(session_id, session)

    return {"status": "fixed", "txn_ref": fix.txn_ref, "field": fix.field, "new_value": fix.new_value}


@router.post("/cleaning/detect-duplicates/{session_id}")
async def detect_duplicates_endpoint(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    from app.services.cleaning.deduplicator import detect_duplicates

    cleaned_df = session.get("cleaned_df")
    if cleaned_df is None:
        raise HTTPException(400, "Run cleaning first")

    deduped_df = detect_duplicates(cleaned_df)
    session["cleaned_df"] = deduped_df
    set_session(session_id, session)

    duplicates = _sanitize(deduped_df[deduped_df["is_duplicate"] == True].to_dict(orient="records"))
    return {"duplicate_count": len(duplicates), "duplicates": duplicates}

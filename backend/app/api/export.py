"""
Export API - CSV, XLSX, PDF export
"""

import logging
import io
import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.core.session_store import get_session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/export/{session_id}/{format}")
async def export_data(session_id: str, format: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    df = session.get("cleaned_df")
    if df is None:
        df = session.get("df")
    if df is None:
        raise HTTPException(400, "No data")

    if format == "csv":
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=expenses_{session_id[:8]}.csv"},
        )

    elif format == "xlsx":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Expenses", index=False)
            workbook = writer.book
            worksheet = writer.sheets["Expenses"]
            header_fmt = workbook.add_format({"bold": True, "bg_color": "#1a1a2e", "font_color": "white"})
            for col_num, col_name in enumerate(df.columns):
                worksheet.write(0, col_num, col_name, header_fmt)
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=expenses_{session_id[:8]}.xlsx"},
        )

    elif format == "json":
        data = df.to_dict(orient="records")
        import json
        return {"data": data, "count": len(data)}

    else:
        raise HTTPException(400, f"Unsupported format: {format}. Use csv, xlsx, or json.")

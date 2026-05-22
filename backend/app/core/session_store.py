"""
Persistent session store — saves upload sessions to disk so they survive
backend restarts. DataFrames are stored as Parquet, metadata as JSON.
"""

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Optional
import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)

SESSIONS_DIR = Path(settings.upload_dir) / ".sessions"


def _session_dir(session_id: str) -> Path:
    return SESSIONS_DIR / session_id


def _metadata_path(session_id: str) -> Path:
    return _session_dir(session_id) / "metadata.json"


def _df_path(session_id: str, name: str) -> Path:
    return _session_dir(session_id) / f"{name}.parquet"


def save_session(session_id: str, metadata: dict):
    """
    Persist session metadata + DataFrames to disk.
    Strips DataFrames from metadata dict and saves them separately.
    """
    sdir = _session_dir(session_id)
    sdir.mkdir(parents=True, exist_ok=True)

    meta = {}
    df_keys = []
    for k, v in metadata.items():
        if isinstance(v, pd.DataFrame):
            path = _df_path(session_id, k)
            v.to_parquet(path, index=False)
            meta[k] = {"type": "dataframe", "path": str(path), "rows": len(v), "cols": list(v.columns)}
            df_keys.append(k)
        else:
            meta[k] = v

    meta["_df_keys"] = df_keys
    meta["_session_id"] = session_id

    with open(_metadata_path(session_id), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)

    logger.info(f"Session {session_id[:8]} saved ({len(metadata.get('df', []))} rows)")


def load_session(session_id: str) -> Optional[dict]:
    """Load session from disk. Returns None if not found."""
    meta_path = _metadata_path(session_id)
    if not meta_path.exists():
        return None

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        session = {}
        df_keys = meta.pop("_df_keys", [])
        session["_session_id"] = meta.pop("_session_id", session_id)

        for k, v in meta.items():
            if isinstance(v, dict) and v.get("type") == "dataframe":
                path = Path(v["path"])
                if path.exists():
                    session[k] = pd.read_parquet(path)
                else:
                    logger.warning(f"DataFrame file missing for {k} in session {session_id[:8]}")
                    session[k] = None
            else:
                session[k] = v

        return session
    except Exception as e:
        logger.error(f"Failed to load session {session_id[:8]}: {e}")
        return None


def session_exists(session_id: str) -> bool:
    return _metadata_path(session_id).exists()


def delete_session(session_id: str):
    sdir = _session_dir(session_id)
    if sdir.exists():
        shutil.rmtree(sdir)
        logger.info(f"Session {session_id[:8]} deleted")


def list_sessions() -> list[str]:
    if not SESSIONS_DIR.exists():
        return []
    return [d.name for d in SESSIONS_DIR.iterdir() if d.is_dir() and (d / "metadata.json").exists()]


def get_session(session_id: str) -> Optional[dict]:
    """Get session from in-memory cache or load from disk."""
    if session_id in _cache:
        return _cache[session_id]
    session = load_session(session_id)
    if session:
        _cache[session_id] = session
    return session


def set_session(session_id: str, session: dict):
    """Store session in memory + persist to disk."""
    _cache[session_id] = session
    save_session(session_id, session)


_cache: dict[str, dict] = {}

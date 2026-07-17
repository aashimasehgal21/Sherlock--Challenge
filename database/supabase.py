"""
database/supabase.py
--------------------

This file handles all Supabase database operations.

It stores prediction history, confidence scores, and explanations so they
can be reviewed later. If Supabase is not configured, the application
continues to work normally; only the prediction history won't be saved.
"""

import json
import time
from config import USE_SUPABASE, SUPABASE_URL, SUPABASE_KEY
from utils.logger import get_logger

log = get_logger("supabase")

_client = None
if USE_SUPABASE:
    try:
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:  # pragma: no cover
        log.warning(f"Could not init Supabase client, running without persistence: {e}")
        _client = None


def save_prediction_log(meeting_id: str, result: dict) -> None:
    """Insert one row into the `prediction_logs` table. No-op if Supabase isn't configured."""
    if not _client:
        return
    try:
        _client.table("prediction_logs").insert({
            "meeting_id": meeting_id,
            "status": result.get("status"),
            "top_candidate": json.dumps(result.get("top_candidate")),
            "ranked": json.dumps(result.get("ranked")),
            "explanation": result.get("explanation"),
            "created_at_unix": time.time(),
        }).execute()
    except Exception as e:
        log.warning(f"Failed to save prediction log to Supabase: {e}")


def fetch_recent_logs(meeting_id: str, limit: int = 20):
    """Fetch recent prediction history for a meeting (used to plot confidence over time)."""
    if not _client:
        return []
    try:
        resp = (
            _client.table("prediction_logs")
            .select("*")
            .eq("meeting_id", meeting_id)
            .order("created_at_unix", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        log.warning(f"Failed to fetch prediction logs from Supabase: {e}")
        return []

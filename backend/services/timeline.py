"""
backend/services/timeline.py
-------------------------------
Tracks confidence PROGRESSION over a call, e.g.:
    10s  -> 35%
    30s  -> 62%
    1min -> 81%
    2min -> 94%

Every time predict_candidate() runs for a meeting (triggered by an
event, not a manual click), we record one timeline point: elapsed
seconds since the first event, the top candidate, and their confidence.
This is what the "Confidence Timeline" feature and the frontend line
chart are built on.

In-memory per meeting_id - for persistence across restarts, this would
also be written to Supabase's prediction_logs table (already happening
via database/supabase.py in parallel).
"""

import time
from typing import Any, Dict, List


class ConfidenceTimeline:
    def __init__(self):
        self._start_times: Dict[str, float] = {}
        self._points: Dict[str, List[Dict[str, Any]]] = {}

    def record(self, meeting_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        now = time.time()
        if meeting_id not in self._start_times:
            self._start_times[meeting_id] = now
            self._points[meeting_id] = []

        elapsed_sec = round(now - self._start_times[meeting_id], 1)
        top = result.get("top_candidate")

        point = {
            "elapsed_sec": elapsed_sec,
            "status": result.get("status"),
            "top_candidate": top.get("display_name") if top else None,
            "confidence": top.get("confidence") if top else 0,
        }
        self._points[meeting_id].append(point)
        return point

    def get_timeline(self, meeting_id: str) -> List[Dict[str, Any]]:
        return self._points.get(meeting_id, [])

    def reset(self, meeting_id: str) -> None:
        self._start_times.pop(meeting_id, None)
        self._points.pop(meeting_id, None)


# One shared instance for the whole app
confidence_timeline = ConfidenceTimeline()

"""
backend/services/live_state.py
---------------------------------
Holds the CURRENT state of each live meeting in memory: participants,
meeting metadata, transcript-so-far. Incoming events (from
backend/routes.py's /events endpoint - which is what a real meeting bot
would call) mutate this state incrementally, instead of the client
re-sending the entire meeting every time.

This is what lets the system react to ONE new transcript line or ONE
speaking-time update without recomputing from scratch off a full JSON
file - the same pattern any event-driven system uses (append the delta,
recompute derived state).

In-memory only (a plain dict) - fine for a single-process prototype.
For production, this would move to Redis so state survives a restart
and multiple backend instances can share it (see README scaling note).
"""

from typing import Any, Dict, Optional


class LiveMeetingState:
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def _ensure(self, meeting_id: str) -> Dict[str, Any]:
        if meeting_id not in self._store:
            self._store[meeting_id] = {"participants": {}, "meeting": {}, "transcript": []}
        return self._store[meeting_id]

    def set_meeting(self, meeting_id: str, meeting: Dict[str, Any]) -> None:
        state = self._ensure(meeting_id)
        state["meeting"] = meeting

    def upsert_participant(self, meeting_id: str, participant: Dict[str, Any]) -> None:
        state = self._ensure(meeting_id)
        pid = participant["participant_id"]
        existing = state["participants"].get(pid, {})
        existing.update(participant)  # merge - partial updates are fine (e.g. just speaking_duration_sec changing)
        state["participants"][pid] = existing

    def append_transcript_line(self, meeting_id: str, line: Dict[str, Any]) -> None:
        state = self._ensure(meeting_id)
        state["transcript"].append(line)

    def get_snapshot(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        if meeting_id not in self._store:
            return None
        state = self._store[meeting_id]
        return {
            "participants": list(state["participants"].values()),
            "meeting": state["meeting"],
            "transcript": state["transcript"],
        }


# One shared instance for the whole app
live_state = LiveMeetingState()

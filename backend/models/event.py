"""
backend/models/event.py
-----------------------

Defines the schema for a live meeting event received by the backend.
Each event updates the meeting state, such as metadata, participant
information, or transcript data.
"""

from typing import Any, Dict, Literal
from pydantic import BaseModel, Field


class MeetingEvent(BaseModel):
    event_type: Literal["meeting_metadata", "participant_update", "transcript_line"] = Field(
        ..., description="What kind of event this is"
    )
    payload: Dict[str, Any] = Field(
        ..., description="Event data - shape depends on event_type (a Meeting dict, a Participant dict, or a TranscriptLine dict)"
    )

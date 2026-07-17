"""
backend/models/participant.py
-----------------------------

Defines the data model for a meeting participant. It is used to validate
participant information and ensure a consistent data structure across the
application.
"""
from typing import Optional
from pydantic import BaseModel, Field


class Participant(BaseModel):
    participant_id: str = Field(..., description="Unique ID for this participant in the call")
    display_name: str = Field(..., description="Name shown in the meeting UI (may be a nickname or device name)")
    email: Optional[str] = Field(None, description="Participant email if visible, else None")

    join_time: str = Field(..., description="ISO 8601 timestamp of when they joined")
    leave_time: Optional[str] = Field(None, description="ISO 8601 timestamp of when they left, if they left")

    webcam_on_ratio: float = Field(0.0, ge=0.0, le=1.0, description="Fraction of the call with webcam on (0.0 - 1.0)")
    speaking_duration_sec: int = Field(0, ge=0, description="Total seconds this participant spoke")
    screen_share_events: int = Field(0, ge=0, description="Number of times this participant shared their screen")

    is_interviewer_hint: bool = Field(
        False, description="Optional hint from the platform if it already flags this person as host/interviewer"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "participant_id": "p1",
                "display_name": "MacBook Pro",
                "email": None,
                "join_time": "2025-01-15T09:58:12Z",
                "leave_time": None,
                "webcam_on_ratio": 0.95,
                "speaking_duration_sec": 1380,
                "screen_share_events": 2,
                "is_interviewer_hint": False,
            }
        }

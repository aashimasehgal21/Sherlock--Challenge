"""
backend/models/meeting.py
-------------------------

Defines the data models used for meeting metadata and transcript
information throughout the application.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Meeting(BaseModel):
    meeting_id: str = Field(..., description="Unique meeting/call ID")
    platform: str = Field("Unknown", description="Google Meet / Zoom / Microsoft Teams")
    scheduled_start: str = Field(..., description="ISO 8601 scheduled start time from the calendar invite")

    candidate_name: str = Field(..., description="Candidate name as given in external metadata (calendar/ATS)")
    candidate_email: Optional[str] = Field(None, description="Candidate email as given in external metadata")

    interviewer_names: List[str] = Field(default_factory=list, description="Known interviewer names")
    interviewer_emails: List[str] = Field(default_factory=list, description="Known interviewer emails")

    calendar_invite_subject: Optional[str] = Field(None, description="Subject line of the calendar invite, if available")

    class Config:
        json_schema_extra = {
            "example": {
                "meeting_id": "meet-9182",
                "platform": "Google Meet",
                "scheduled_start": "2025-01-15T10:00:00Z",
                "candidate_name": "Rohan Sharma",
                "candidate_email": "rohan.sharma92@gmail.com",
                "interviewer_names": ["Priya Verma", "Amit Kulkarni"],
                "interviewer_emails": ["priya.verma@sherlock.sh", "amit.k@sherlock.sh"],
                "calendar_invite_subject": "Interview: Rohan Sharma - Backend Engineer",
            }
        }


class TranscriptLine(BaseModel):
    participant_id: str = Field(..., description="Which participant said this line")
    text: str = Field(..., description="What they said")
    timestamp: str = Field(..., description="ISO 8601 timestamp of this line")

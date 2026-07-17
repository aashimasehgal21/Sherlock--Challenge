"""
backend/models/prediction.py
----------------------------

Defines the request and response models used for prediction. These
schemas ensure consistent data validation and API documentation.
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

from backend.models.participant import Participant
from backend.models.meeting import Meeting, TranscriptLine


class SignalResultModel(BaseModel):
    name: str
    score: float
    weight: float
    detail: str
    passed: bool = False


class ChecklistItem(BaseModel):
    label: str
    passed: bool
    detail: str


class RankedParticipant(BaseModel):
    participant_id: str
    display_name: str
    confidence: float = Field(..., description="Final weighted confidence score, 0-100")
    signals: List[SignalResultModel]
    checklist: List[ChecklistItem] = Field(
        default_factory=list,
        description="Structured ✅/❌ explainability checklist (Better Explainability feature)",
    )


class PredictRequest(BaseModel):
    """Body for POST /predict — what a real Meet/Zoom/Teams bot would send."""
    participants: List[Participant]
    meeting: Meeting
    transcript: List[TranscriptLine] = Field(default_factory=list)


class PredictionResponse(BaseModel):
    status: str = Field(..., description="'confident' | 'ambiguous' | 'low_confidence' | 'insufficient_data'")
    top_candidate: Optional[RankedParticipant] = None
    ranked: List[RankedParticipant] = Field(default_factory=list)
    explanation: Optional[str] = None
    transcript_role_signal: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

"""
backend/agents/__init__.py
-----------------------------
Multi-agent candidate identification system.

- MetadataAgent    - calendar/name/email/interviewer signals
- TranscriptAgent  - LLM transcript role inference + self-introduction detection
- AudioAgent       - speaking ratio, voice activity, speaking rate, interruptions
- VisionAgent      - webcam/screenshare + optional face verification
- DecisionAgent    - runs all of the above and combines them into one result
"""

from backend.agents.schemas import AgentSignal
from backend.agents.base import BaseAgent
from backend.agents.metadata_agent import MetadataAgent
from backend.agents.transcript_agent import TranscriptAgent
from backend.agents.audio_agent import AudioAgent
from backend.agents.vision_agent import VisionAgent
from backend.agents.decision_agent import DecisionAgent

__all__ = [
    "AgentSignal", "BaseAgent",
    "MetadataAgent", "TranscriptAgent", "AudioAgent", "VisionAgent",
    "DecisionAgent",
]

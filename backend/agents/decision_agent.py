"""
backend/agents/decision_agent.py
--------------------------------

This agent combines the outputs from all specialist agents to generate
the final prediction.

It calculates the overall confidence score, merges all detected signals,
and creates a simple checklist explaining why a participant was selected.
The result is returned in a format that is compatible with the rest of
the application.
"""

from typing import Any, Dict, List

from backend.agents.metadata_agent import MetadataAgent
from backend.agents.transcript_agent import TranscriptAgent
from backend.agents.audio_agent import AudioAgent
from backend.agents.vision_agent import VisionAgent
from backend.agents.schemas import AgentSignal


# Human-friendly labels for the checklist (falls back to the raw signal
# name, prettified, if not listed here)
CHECKLIST_LABELS = {
    "name_match": "Name matches calendar invite",
    "email_match": "Email matches candidate record",
    "calendar_join_match": "Joined close to scheduled start time",
    "interviewer_exclusion": "Not a known interviewer",
    "transcript_role": "Answering questions in transcript",
    "self_introduction": "Introduced themselves by candidate's name",
    "speaking_ratio": "Most speaking time in the call",
    "voice_activity": "Consistently active speaker",
    "speaking_rate": "Typical conversational speaking rate",
    "interruption_behavior": "Normal interruption pattern",
    "silent_observer_penalty": "Not a silent observer",
    "webcam_consistency": "Camera on consistently",
    "screenshare_behavior": "Shared screen during the call",
    "face_match": "Face matches reference photo",
}


class DecisionAgent:
    def __init__(self):
        self.agents = [MetadataAgent(), TranscriptAgent(), AudioAgent(), VisionAgent()]

    def decide(self, participant: Dict[str, Any], meeting: Dict[str, Any],
               all_participants: List[Dict[str, Any]], transcript: List[Dict[str, Any]],
               transcript_role_result: Dict[str, Any]) -> Dict[str, Any]:

        context = {
            "meeting": meeting,
            "all_participants": all_participants,
            "transcript": transcript,
            "transcript_role_result": transcript_role_result,
        }

        all_signals: List[AgentSignal] = []
        for agent in self.agents:
            all_signals.extend(agent.analyze(participant, context))

        total_weight = sum(s.weight for s in all_signals) or 1.0
        weighted_sum = sum(s.score * s.weight for s in all_signals)
        final_score = round((weighted_sum / total_weight) * 100, 1)

        checklist = [
            {
                "label": CHECKLIST_LABELS.get(s.name, s.name.replace("_", " ").capitalize()),
                "passed": s.passed,
                "detail": s.detail,
            }
            for s in all_signals
            if s.weight > 0  # skip zero-weight signals (e.g. face_match when disabled) - nothing to show
        ]

        return {
            "participant_id": participant["participant_id"],
            "display_name": participant.get("display_name"),
            "confidence": final_score,
            "signals": [s.as_dict() for s in all_signals],
            "checklist": checklist,
        }

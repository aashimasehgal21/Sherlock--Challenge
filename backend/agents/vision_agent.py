"""
backend/agents/vision_agent.py
------------------------------

This agent analyzes video-based signals such as webcam activity and
screen sharing to contribute to the final confidence score.
"""

from typing import Any, Dict, List

from backend.agents.base import BaseAgent
from backend.agents.schemas import AgentSignal
from utils.helpers import clamp


class VisionAgent(BaseAgent):
    name = "vision_agent"

    def analyze(self, participant: Dict[str, Any], context: Dict[str, Any]) -> List[AgentSignal]:
        signals = []

        # ---- webcam_consistency ----
        ratio = participant.get("webcam_on_ratio", 0.0)
        signals.append(AgentSignal(
            name="webcam_consistency", score=round(clamp(ratio), 3), weight=0.05, passed=ratio >= 0.5,
            detail=f"Webcam on {ratio*100:.0f}% of the time",
        ))

        # ---- screenshare_behavior ----
        events = participant.get("screen_share_events", 0)
        score = clamp(events / 3.0)
        signals.append(AgentSignal(
            name="screenshare_behavior", score=round(score, 3), weight=0.05, passed=events > 0,
            detail=f"{events} screen-share events",
        ))

        return signals



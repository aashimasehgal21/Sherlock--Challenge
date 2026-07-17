"""
backend/agents/audio_agent.py
-----------------------------

This agent processes audio-related signals for each participant.

Instead of relying only on speaking time, it also considers voice activity,
speaking rate, interruptions, and silent observer detection. These signals
help improve the confidence score and make the prediction more reliable.

If any audio feature is missing, the agent simply uses neutral values so
the prediction can continue without errors.
"""
from typing import Any, Dict, List

from backend.agents.base import BaseAgent
from backend.agents.schemas import AgentSignal
from utils.helpers import clamp


NORMAL_SPEAKING_RATE_RANGE = (110, 170)  # words per minute, roughly typical conversational range


class AudioAgent(BaseAgent):
    name = "audio_agent"

    def analyze(self, participant: Dict[str, Any], context: Dict[str, Any]) -> List[AgentSignal]:
        all_participants = context["all_participants"]
        signals = []

        # ---- speaking_ratio ----
        total_speaking = sum(p.get("speaking_duration_sec", 0) for p in all_participants) or 1
        ratio = participant.get("speaking_duration_sec", 0) / total_speaking
        signals.append(AgentSignal(
            name="speaking_ratio", score=round(clamp(ratio), 3), weight=0.18, passed=ratio >= 0.4,
            detail=f"Spoke {participant.get('speaking_duration_sec',0)}s ({ratio*100:.0f}% of total talk time)",
        ))

        # ---- voice_activity_ratio ----
        vad = participant.get("voice_activity_ratio")
        if vad is None:
            signals.append(AgentSignal(
                name="voice_activity", score=0.5, weight=0.05, passed=False,
                detail="No voice-activity data available",
            ))
        else:
            signals.append(AgentSignal(
                name="voice_activity", score=round(clamp(vad), 3), weight=0.05, passed=vad >= 0.3,
                detail=f"Actively speaking {vad*100:.0f}% of the time they were on the call",
            ))

        # ---- speaking_rate_signal ----
        wpm = participant.get("speaking_rate_wpm")
        if wpm is None:
            signals.append(AgentSignal(
                name="speaking_rate", score=0.5, weight=0.03, passed=False,
                detail="No speaking-rate data available",
            ))
        else:
            lo, hi = NORMAL_SPEAKING_RATE_RANGE
            in_range = lo <= wpm <= hi
            signals.append(AgentSignal(
                name="speaking_rate", score=0.7 if in_range else 0.5, weight=0.03, passed=in_range,
                detail=f"Speaking rate ~{wpm} wpm ({'typical conversational range' if in_range else 'outside typical range - weak signal only'})",
            ))

        # ---- interruption_penalty ----
        interruptions = participant.get("interruptions_count")
        if interruptions is None:
            signals.append(AgentSignal(
                name="interruption_behavior", score=0.6, weight=0.03, passed=False,
                detail="No interruption data available",
            ))
        else:
            # 0-2 interruptions -> normal; more -> mild penalty (interviewers
            # get interrupted less often by candidates than by co-interviewers)
            score = clamp(1.0 - max(0, interruptions - 2) * 0.15)
            signals.append(AgentSignal(
                name="interruption_behavior", score=round(score, 3), weight=0.03, passed=interruptions <= 2,
                detail=f"{interruptions} interruption(s) detected",
            ))

        # ---- silent_observer_penalty ----
        spoke = participant.get("speaking_duration_sec", 0) > 0
        cam = participant.get("webcam_on_ratio", 0) > 0
        if not spoke and not cam:
            signals.append(AgentSignal(
                name="silent_observer_penalty", score=0.0, weight=0.10, passed=False,
                detail="Never spoke and never turned on camera - likely a silent observer",
            ))
        else:
            signals.append(AgentSignal(
                name="silent_observer_penalty", score=1.0, weight=0.10, passed=True,
                detail="Participated actively (spoke or used camera)",
            ))

        return signals

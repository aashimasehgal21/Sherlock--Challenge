"""
backend/agents/transcript_agent.py
----------------------------------

This agent analyzes transcript-based signals.

It checks how each participant contributes to the conversation and looks
for self-introductions. These signals help identify the most likely
candidate based on what was said during the meeting.
"""
import re
from typing import Any, Dict, List

from backend.agents.base import BaseAgent
from backend.agents.schemas import AgentSignal
from utils.helpers import normalize


class TranscriptAgent(BaseAgent):
    name = "transcript_agent"

    def analyze(self, participant: Dict[str, Any], context: Dict[str, Any]) -> List[AgentSignal]:
        signals = []
        pid = participant["participant_id"]

        # ---- transcript_role (from the shared LLM/heuristic result) ----
        role_result = context.get("transcript_role_result") or {}
        if not role_result:
            signals.append(AgentSignal(
                name="transcript_role", score=0.5, weight=0.20, passed=False,
                detail="No transcript role signal available",
            ))
        elif role_result.get("candidate_participant_id") == pid:
            conf = role_result.get("confidence", 0.5)
            signals.append(AgentSignal(
                name="transcript_role", score=conf, weight=0.20, passed=conf >= 0.5,
                detail=role_result.get("reason", "LLM identified as candidate"),
            ))
        else:
            signals.append(AgentSignal(
                name="transcript_role", score=0.1, weight=0.20, passed=False,
                detail="LLM/heuristic did not identify this participant as candidate",
            ))

        # ---- self_introduction (own-name mention) ----
        transcript = context.get("transcript", [])
        candidate_name = context.get("meeting", {}).get("candidate_name", "")
        first_name = normalize(candidate_name).split(" ")[0] if candidate_name else ""

        mentioned_own_name = False
        if first_name:
            pattern = re.compile(rf"\b(i'?m|this is|my name is)\s+{re.escape(first_name)}\b")
            for line in transcript:
                if line.get("participant_id") == pid and pattern.search(normalize(line.get("text", ""))):
                    mentioned_own_name = True
                    break

        signals.append(AgentSignal(
            name="self_introduction", score=1.0 if mentioned_own_name else 0.5, weight=0.08,
            passed=mentioned_own_name,
            detail="Introduced themselves by the candidate's name in the transcript"
                   if mentioned_own_name else "No explicit self-introduction detected",
        ))

        return signals

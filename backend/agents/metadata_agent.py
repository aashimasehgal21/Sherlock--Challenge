"""
backend/agents/metadata_agent.py
--------------------------------

This agent analyzes participant metadata such as names, email addresses,
calendar details, and interviewer information. These signals help verify
whether a participant matches the expected candidate.
"""
from datetime import datetime
from typing import Any, Dict, List

from backend.agents.base import BaseAgent
from backend.agents.schemas import AgentSignal
from ai.embeddings import semantic_similarity
from utils.helpers import name_similarity, email_local_part, looks_like_device_name, clamp


class MetadataAgent(BaseAgent):
    name = "metadata_agent"

    def analyze(self, participant: Dict[str, Any], context: Dict[str, Any]) -> List[AgentSignal]:
        meeting = context["meeting"]
        signals = []

        # ---- name_match ----
        display_name = participant.get("display_name", "")
        candidate_name = meeting.get("candidate_name", "")
        if looks_like_device_name(display_name):
            signals.append(AgentSignal(
                name="name_match", score=0.4, weight=0.25, passed=False,
                detail=f"Display name '{display_name}' looks like a device, not a person",
            ))
        else:
            score = semantic_similarity(display_name, candidate_name)
            signals.append(AgentSignal(
                name="name_match", score=score, weight=0.25, passed=score >= 0.6,
                detail=f"'{display_name}' vs candidate '{candidate_name}' -> {score}",
            ))

        # ---- email_match ----
        p_email = participant.get("email")
        c_email = meeting.get("candidate_email", "")
        if not p_email:
            signals.append(AgentSignal(
                name="email_match", score=0.3, weight=0.15, passed=False,
                detail="No email visible for this participant",
            ))
        else:
            match = email_local_part(p_email) == email_local_part(c_email)
            signals.append(AgentSignal(
                name="email_match", score=1.0 if match else 0.0, weight=0.15, passed=match,
                detail=f"'{p_email}' vs candidate email '{c_email}'",
            ))

        # ---- calendar_join_match ----
        try:
            join = datetime.fromisoformat(participant["join_time"].replace("Z", "+00:00"))
            scheduled = datetime.fromisoformat(meeting["scheduled_start"].replace("Z", "+00:00"))
            delta_min = abs((join - scheduled).total_seconds()) / 60.0
            score = clamp(1.0 - (delta_min / 15.0))
            signals.append(AgentSignal(
                name="calendar_join_match", score=round(score, 3), weight=0.10, passed=score >= 0.6,
                detail=f"Joined {delta_min:.1f} min from scheduled start",
            ))
        except Exception:
            signals.append(AgentSignal(
                name="calendar_join_match", score=0.5, weight=0.10, passed=False,
                detail="Could not compute join-time delta",
            ))

        # ---- interviewer_exclusion (strong negative signal) ----
        excluded = False
        detail = "Does not match any known interviewer"
        for iname in meeting.get("interviewer_names", []):
            if name_similarity(display_name, iname) > 0.75:
                excluded = True
                detail = f"Matches known interviewer '{iname}'"
                break
        if not excluded:
            for iemail in meeting.get("interviewer_emails", []):
                if p_email and email_local_part(p_email) == email_local_part(iemail):
                    excluded = True
                    detail = f"Email matches known interviewer '{iemail}'"
                    break

        signals.append(AgentSignal(
            name="interviewer_exclusion", score=0.0 if excluded else 1.0, weight=0.15,
            passed=not excluded, detail=detail,
        ))

        return signals

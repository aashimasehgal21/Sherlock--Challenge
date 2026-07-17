"""
backend/services/confidence.py
--------------------------------
This module now DELEGATES to the multi-agent system in backend/agents/
(MetadataAgent, TranscriptAgent, AudioAgent, VisionAgent, DecisionAgent)
instead of containing the scoring logic directly.

Kept as a thin wrapper - not deleted - so nothing that imports
`compute_confidence` from here (existing tests, older code) needs to
change. The actual signal logic now lives in backend/agents/, split by
specialist agent, which is easier to extend (add a new agent) without
touching a single giant file.
"""

from typing import Any, Dict, List, Optional

from backend.agents.decision_agent import DecisionAgent

_decision_agent = DecisionAgent()


def compute_confidence(
    participant: Dict[str, Any],
    meeting: Dict[str, Any],
    all_participants: List[Dict[str, Any]],
    transcript_role_result: Optional[Dict[str, Any]] = None,
    transcript: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Backward-compatible entry point. Internally runs all 4 specialist
    agents and combines their signals via DecisionAgent - see
    backend/agents/decision_agent.py for the actual combination logic.
    """
    return _decision_agent.decide(
        participant=participant,
        meeting=meeting,
        all_participants=all_participants,
        transcript=transcript or [],
        transcript_role_result=transcript_role_result or {},
    )

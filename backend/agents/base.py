"""
backend/agents/base.py
----------------------

Base interface for all specialist agents.

Each agent implements the `analyze()` method, which returns a list of
signals for a participant. The shared context provides any additional
meeting information an agent may need.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from backend.agents.schemas import AgentSignal


class BaseAgent(ABC):
    name: str = "base_agent"

    @abstractmethod
    def analyze(self, participant: Dict[str, Any], context: Dict[str, Any]) -> List[AgentSignal]:
        ...

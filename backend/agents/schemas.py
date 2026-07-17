"""
backend/agents/schemas.py
-------------------------

Shared data models used by all agents.

Each agent returns signals in the same format, making it easy to combine
their results and keep the rest of the application consistent. The
`passed` field indicates whether a signal supports the final prediction.
"""
from pydantic import BaseModel


class AgentSignal(BaseModel):
    name: str
    score: float          # 0.0 - 1.0
    weight: float
    detail: str
    passed: bool = False  # True if this signal meaningfully supports "this is the candidate"

    def as_dict(self):
        return self.model_dump()

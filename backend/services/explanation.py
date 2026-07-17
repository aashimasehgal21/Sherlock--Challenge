"""
backend/services/explanation.py
--------------------------------
Turns the raw signal breakdown into a human-readable explanation.

Two layers, both always available:
1. RULE-BASED summary (always works, zero API calls, fully deterministic)
   - lists the top 2-3 signals that drove the decision
2. LLM narrative (optional, nicer prose) - only used if OpenAI is configured.
   If it fails or is unavailable, we just use the rule-based summary, so
   explainability NEVER silently disappears.
"""

import json
from ai.openai_client import chat_completion
from ai.prompts import AMBIGUITY_RESOLUTION_SYSTEM_PROMPT, build_ambiguity_prompt


def _rule_based_summary(top: dict) -> str:
    # Sort this participant's own signals by contribution (score * weight)
    signals = sorted(top["signals"], key=lambda s: s["score"] * s["weight"], reverse=True)
    top_signals = [s for s in signals if s["score"] * s["weight"] > 0][:3]

    if not top_signals:
        return f"'{top['display_name']}' was selected, but no signal strongly supports it."

    reasons = "; ".join(f"{s['name'].replace('_',' ')} ({s['detail']})" for s in top_signals)
    return f"'{top['display_name']}' was selected as the likely candidate mainly because: {reasons}."


def generate_explanation(status: str, ranked: list) -> str:
    if not ranked:
        return "No participants available to evaluate."

    top = ranked[0]
    base_summary = _rule_based_summary(top)

    if status == "ambiguous" and len(ranked) > 1:
        base_summary += (
            f" However, '{ranked[1]['display_name']}' scored close behind "
            f"({ranked[1]['confidence']} vs {top['confidence']}), so this is currently "
            f"AMBIGUOUS — more data (e.g. transcript content, name confirmation) is needed."
        )
    elif status == "low_confidence":
        base_summary += " Confidence is currently LOW — treat this as provisional until more signals arrive."

    # Try to get a nicer LLM narrative on top; fall back silently if unavailable
    try:
        compact = [
            {"display_name": r["display_name"], "confidence": r["confidence"],
             "top_signals": sorted(r["signals"], key=lambda s: s["score"] * s["weight"], reverse=True)[:3]}
            for r in ranked[:4]
        ]
        llm_text = chat_completion(
            AMBIGUITY_RESOLUTION_SYSTEM_PROMPT,
            build_ambiguity_prompt(json.dumps(compact, indent=2)),
            max_tokens=180,
        )
        if llm_text:
            return llm_text
    except Exception:
        pass

    return base_summary

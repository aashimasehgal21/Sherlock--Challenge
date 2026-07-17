"""
backend/services/predictor.py
------------------------------
Orchestrates one full "who is the candidate?" prediction cycle:

1. Load current participants + meeting metadata + transcript-so-far
2. Ask the LLM (or fallback heuristic) once: "based on transcript, who
   sounds like the candidate?"
3. Run compute_confidence() for every participant (multi-signal scoring)
4. Rank participants by confidence
5. Decide: confident pick / ambiguous / insufficient data
6. Generate a human explanation

This function is called every time new meeting data comes in (new
speaking activity, new transcript lines, participant join/leave) - that
is what makes confidence "continuously update" in real time.
"""

import json
from ai.openai_client import chat_completion
from ai.prompts import TRANSCRIPT_ROLE_SYSTEM_PROMPT, build_transcript_role_prompt
from backend.services.confidence import compute_confidence
from backend.services.explanation import generate_explanation
from utils.logger import get_logger

log = get_logger("predictor", log_filename="prediction.log")

# Thresholds - tunable. See README "Trade-offs" section for reasoning.
CONFIDENT_THRESHOLD = 65.0   # top score above this -> confident pick
AMBIGUOUS_GAP = 10.0         # if top two scores are within this gap -> ambiguous


def _infer_transcript_role(transcript: list) -> dict:
    """
    Uses the LLM to guess, from the transcript alone, which participant_id
    is answering questions (candidate) vs asking them (interviewer).
    Falls back to a simple heuristic if no LLM is configured: candidate
    is assumed to be whoever has the MOST transcript lines (weak fallback,
    clearly logged as such).
    """
    if not transcript:
        return {}

    snippet_lines = "\n".join(f"{t['participant_id']}: {t['text']}" for t in transcript[-30:])
    raw = chat_completion(
        TRANSCRIPT_ROLE_SYSTEM_PROMPT,
        build_transcript_role_prompt(snippet_lines),
        max_tokens=200,
    )

    if raw:
        try:
            parsed = json.loads(raw)
            if parsed.get("candidate_participant_id"):
                return parsed
        except json.JSONDecodeError:
            log.warning("LLM transcript role response was not valid JSON, using fallback")

    # ---- Fallback heuristic (no API key / LLM failure) ----
    counts = {}
    for line in transcript:
        counts[line["participant_id"]] = counts.get(line["participant_id"], 0) + 1
    if not counts:
        return {}
    top_pid = max(counts, key=counts.get)
    return {
        "candidate_participant_id": top_pid,
        "confidence": 0.4,  # low confidence, clearly a weak fallback signal
        "reason": "Fallback heuristic: most frequent transcript speaker (no LLM available)",
    }


def predict_candidate(participants: list, meeting: dict, transcript: list) -> dict:
    if not participants:
        return {
            "status": "insufficient_data",
            "message": "No participants in the meeting yet.",
            "ranked": [],
        }

    transcript_role_result = _infer_transcript_role(transcript)

    ranked = [
        compute_confidence(p, meeting, participants, transcript_role_result, transcript)
        for p in participants
    ]
    ranked.sort(key=lambda r: r["confidence"], reverse=True)

    top = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None

    if top["confidence"] >= CONFIDENT_THRESHOLD and (
        second is None or (top["confidence"] - second["confidence"]) >= AMBIGUOUS_GAP
    ):
        status = "confident"
    elif second is not None and (top["confidence"] - second["confidence"]) < AMBIGUOUS_GAP:
        status = "ambiguous"
    else:
        status = "low_confidence"

    explanation = generate_explanation(status, ranked)

    log.info(
        f"meeting={meeting.get('meeting_id','unknown')} status={status} "
        f"top='{top['display_name']}'({top['confidence']}%) "
        f"second={'%s(%.1f%%)' % (second['display_name'], second['confidence']) if second else 'N/A'}"
    )

    return {
        "status": status,
        "top_candidate": top,
        "ranked": ranked,
        "explanation": explanation,
        "transcript_role_signal": transcript_role_result,
    }

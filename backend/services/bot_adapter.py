"""
backend/services/bot_adapter.py
---------------------------------
THIS FILE IS THE ANSWER TO "how does this connect to a real meeting?"

In production, you don't talk to Google Meet/Zoom/Teams directly. You use
a meeting-bot service (e.g. Recall.ai, Fireflies, Symbl.ai) that joins the
call as a silent participant and sends YOU webhook events with the raw
data: participants, join/leave, speaking activity, transcript lines.

This adapter's only job: take whatever shape THAT service sends, and
convert it into our internal Participant / Meeting / TranscriptLine
models - the exact same models already used by mock_data/*.json and the
/predict endpoint. Nothing else in the system needs to change.

This is a STUB with a realistic example payload shape (modeled loosely on
how bot services like Recall.ai structure their webhooks). Swap
`example_bot_payload()` and `adapt_bot_payload()` for the real field names
once you pick a specific provider - the rest of the pipeline (confidence
engine, explanation, Supabase logging) needs zero changes.
"""

from datetime import datetime, timezone
from typing import Any, Dict


def example_bot_payload() -> Dict[str, Any]:
    """
    Roughly what a meeting-bot webhook call might look like. Real
    providers differ in field names, but the SHAPE (participants list +
    events + transcript) is universal across all of them.
    """
    return {
        "bot_id": "bot_abc123",
        "meeting_url": "https://meet.google.com/xyz-abcd-efg",
        "meeting_started_at": "2025-01-15T10:00:00Z",
        "participants": [
            {
                "id": "part_1",
                "name": "MacBook Pro",
                "email": None,
                "joined_at": "2025-01-15T09:58:12Z",
                "left_at": None,
                "camera_on_seconds": 1200,
                "total_seconds": 1300,
                "talk_time_seconds": 800,
                "screen_shares": 2,
            },
            {
                "id": "part_2",
                "name": "Priya Verma",
                "email": "priya.verma@sherlock.sh",
                "joined_at": "2025-01-15T09:59:40Z",
                "left_at": None,
                "camera_on_seconds": 900,
                "total_seconds": 1200,
                "talk_time_seconds": 400,
                "screen_shares": 0,
            },
        ],
        "transcript": [
            {"speaker_id": "part_2", "words": "Tell me about your experience.", "ts": "2025-01-15T10:00:30Z"},
            {"speaker_id": "part_1", "words": "Sure, I've worked with Go and Kafka.", "ts": "2025-01-15T10:00:50Z"},
        ],
        # This part - candidate_name/email/interviewers - normally comes
        # from YOUR calendar/ATS integration (e.g. Greenhouse, Lever), not
        # from the bot itself. Bot only sees the call; your own scheduling
        # system knows who was supposed to attend.
        "external_metadata": {
            "candidate_name": "Rohan Sharma",
            "candidate_email": "rohan.sharma92@gmail.com",
            "interviewer_names": ["Priya Verma"],
            "interviewer_emails": ["priya.verma@sherlock.sh"],
        },
    }


def adapt_bot_payload(bot_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts a raw bot-webhook payload into (participants, meeting,
    transcript) in EXACTLY the shape backend.services.predictor.predict_candidate
    expects - the same shape as mock_data/*.json.
    """
    participants = []
    for p in bot_payload.get("participants", []):
        total = max(p.get("total_seconds", 1), 1)
        participants.append({
            "participant_id": p["id"],
            "display_name": p.get("name", "Unknown"),
            "email": p.get("email"),
            "join_time": p.get("joined_at"),
            "leave_time": p.get("left_at"),
            "webcam_on_ratio": round(p.get("camera_on_seconds", 0) / total, 3),
            "speaking_duration_sec": p.get("talk_time_seconds", 0),
            "screen_share_events": p.get("screen_shares", 0),
            "is_interviewer_hint": False,
        })

    meta = bot_payload.get("external_metadata", {})
    meeting = {
        "meeting_id": bot_payload.get("bot_id", "unknown"),
        "platform": "Unknown",
        "scheduled_start": bot_payload.get("meeting_started_at", datetime.now(timezone.utc).isoformat()),
        "candidate_name": meta.get("candidate_name", ""),
        "candidate_email": meta.get("candidate_email"),
        "interviewer_names": meta.get("interviewer_names", []),
        "interviewer_emails": meta.get("interviewer_emails", []),
    }

    transcript = [
        {
            "participant_id": t["speaker_id"],
            "text": t.get("words", ""),
            "timestamp": t.get("ts", ""),
        }
        for t in bot_payload.get("transcript", [])
    ]

    return {"participants": participants, "meeting": meeting, "transcript": transcript}

"""
backend/routes.py
------------------
All API endpoints live here. Kept separate from main.py so main.py stays
tiny and just wires the app together.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, Body, WebSocket, WebSocketDisconnect

from backend.models import PredictRequest, PredictionResponse, MeetingEvent
from backend.services.predictor import predict_candidate
from backend.services.bot_adapter import adapt_bot_payload, example_bot_payload
from backend.services.live_state import live_state
from backend.services.event_bus import event_bus
from backend.services.timeline import confidence_timeline
from database.supabase import save_prediction_log
from utils.logger import get_logger

log = get_logger("routes")
router = APIRouter()

MOCK_DIR = Path(__file__).resolve().parent.parent / "mock_data"


def _load_mock():
    with open(MOCK_DIR / "participants.json") as f:
        participants = json.load(f)
    with open(MOCK_DIR / "meeting.json") as f:
        meeting = json.load(f)
    with open(MOCK_DIR / "transcript.json") as f:
        transcript = json.load(f)
    return participants, meeting, transcript


@router.get("/health")
def health():
    return {"status": "ok", "time": time.time()}


@router.get("/predict", response_model=PredictionResponse)
def predict_from_mock_data():
    """
    Runs a full prediction cycle using the bundled mock_data files.
    This is what the Streamlit demo calls to show the live-updating UI.
    """
    participants, meeting, transcript = _load_mock()
    result = predict_candidate(participants, meeting, transcript)
    save_prediction_log(meeting.get("meeting_id", "unknown"), result)
    return result


@router.post("/predict", response_model=PredictionResponse)
def predict_from_payload(payload: PredictRequest):
    """
    Real integration point: a real Google Meet/Zoom/Teams bot would POST
    live participant + transcript data here instead of using mock files.
    Request body is validated automatically against backend/models/prediction.py
    (bad types / missing fields get rejected with a clear 422 error).
    """
    participants = [p.model_dump() for p in payload.participants]
    meeting = payload.meeting.model_dump()
    transcript = [t.model_dump() for t in payload.transcript]

    result = predict_candidate(participants, meeting, transcript)
    save_prediction_log(meeting.get("meeting_id", "unknown"), result)
    return result


@router.get("/mock-data")
def get_mock_data():
    """Lets the frontend show/edit the raw mock data for the demo."""
    participants, meeting, transcript = _load_mock()
    return {"participants": participants, "meeting": meeting, "transcript": transcript}


@router.post("/webhook/meeting-bot", response_model=PredictionResponse)
def meeting_bot_webhook(bot_payload: Dict[str, Any] = Body(...)):
    """
    THIS IS THE REAL-INTEGRATION ENTRY POINT.

    In production, you'd point a meeting-bot service's webhook (e.g.
    Recall.ai, Fireflies, Symbl.ai) at this URL. Whenever the bot has new
    data (participant joined, new transcript line, etc.), it POSTs here.

    We convert their payload shape into our internal models via
    backend/services/bot_adapter.py, then run the exact same prediction
    pipeline used everywhere else in this project. Nothing about the
    confidence engine changes - only this adapter function would need to
    be rewritten to match whichever bot provider you actually pick.
    """
    adapted = adapt_bot_payload(bot_payload)
    result = predict_candidate(adapted["participants"], adapted["meeting"], adapted["transcript"])
    save_prediction_log(adapted["meeting"].get("meeting_id", "unknown"), result)
    return result


@router.get("/webhook/meeting-bot/example")
def meeting_bot_webhook_example():
    """
    Returns a sample bot payload so you can see the shape a real
    integration would send, and test /webhook/meeting-bot yourself:

        curl -X POST http://127.0.0.1:8000/webhook/meeting-bot \\
             -H "Content-Type: application/json" \\
             -d @sample_payload.json
    """
    return example_bot_payload()


# =====================================================================
# EVENT-DRIVEN ENDPOINTS
# ---------------------------------------------------------------------
# These three endpoints replace "poll /predict every N seconds" with a
# genuine push model:
#   1. A real meeting bot (or scripts/simulate_live_meeting.py for a
#      demo) POSTs one small event at a time to /events/{meeting_id}
#      as things happen on the call.
#   2. We apply that event to in-memory live_state, recompute the
#      prediction ONCE, record a confidence-timeline point, and PUSH
#      the new result to every connected WebSocket client via event_bus.
#   3. Clients connected to /ws/{meeting_id} receive updates the moment
#      they happen - they never ask "anything new?" on a timer.
# =====================================================================

@router.post("/events/{meeting_id}", response_model=PredictionResponse)
async def push_meeting_event(meeting_id: str, event: MeetingEvent):
    """
    Push ONE event for a meeting (metadata set, participant update, or
    a new transcript line). Recomputes the prediction immediately and
    broadcasts it to any connected WebSocket clients - this is the
    event-driven alternative to polling /predict.
    """
    if event.event_type == "meeting_metadata":
        live_state.set_meeting(meeting_id, event.payload)
    elif event.event_type == "participant_update":
        live_state.upsert_participant(meeting_id, event.payload)
    elif event.event_type == "transcript_line":
        live_state.append_transcript_line(meeting_id, event.payload)

    snapshot = live_state.get_snapshot(meeting_id)
    if not snapshot or not snapshot["participants"]:
        result = {"status": "insufficient_data", "message": "Waiting for participants.", "ranked": []}
    else:
        result = predict_candidate(snapshot["participants"], snapshot["meeting"], snapshot["transcript"])
        save_prediction_log(meeting_id, result)

    timeline_point = confidence_timeline.record(meeting_id, result)
    log.info(f"event={event.event_type} meeting={meeting_id} -> confidence timeline point {timeline_point}")

    await event_bus.publish(meeting_id, {"type": "prediction_update", "result": result, "timeline_point": timeline_point})
    return result


@router.websocket("/ws/{meeting_id}")
async def meeting_websocket(websocket: WebSocket, meeting_id: str):
    """
    Connect here to receive prediction updates the INSTANT a new event
    is processed - true push, zero polling. Try it with the included
    static client: frontend/static/event_client.html (or any WebSocket
    test tool) pointed at ws://127.0.0.1:8000/ws/{meeting_id}.
    """
    await websocket.accept()
    queue = event_bus.subscribe(meeting_id)
    try:
        # Send current state immediately on connect, if any exists
        snapshot = live_state.get_snapshot(meeting_id)
        if snapshot and snapshot["participants"]:
            result = predict_candidate(snapshot["participants"], snapshot["meeting"], snapshot["transcript"])
            await websocket.send_json({"type": "initial_state", "result": result})

        while True:
            message = await queue.get()
            await websocket.send_json(message)
    except WebSocketDisconnect:
        log.info(f"WebSocket client disconnected from meeting {meeting_id}")
    finally:
        event_bus.unsubscribe(meeting_id, queue)


@router.get("/timeline/{meeting_id}")
def get_confidence_timeline(meeting_id: str):
    """
    Returns the confidence progression for a meeting, e.g.:
        [{"elapsed_sec": 10, "confidence": 35, ...}, {"elapsed_sec": 30, "confidence": 62, ...}]
    Populated automatically as events are pushed via /events/{meeting_id}.
    """
    return {"meeting_id": meeting_id, "timeline": confidence_timeline.get_timeline(meeting_id)}

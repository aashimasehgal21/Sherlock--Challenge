"""
scripts/simulate_live_meeting.py
--------------------------------

Simulates a live meeting by sending events to the backend one at a time.
This allows the confidence score and predictions to update gradually,
similar to a real meeting.
"""

import time
import requests

BACKEND_URL = "http://127.0.0.1:8000"
MEETING_ID = "sim-meeting-1"


def send_event(event_type: str, payload: dict):
    resp = requests.post(f"{BACKEND_URL}/events/{MEETING_ID}", json={
        "event_type": event_type,
        "payload": payload,
    })
    resp.raise_for_status()
    result = resp.json()
    top = result.get("top_candidate")
    print(f"  -> status={result['status']:16s} top={top['display_name'] if top else 'N/A':15s} "
          f"confidence={top['confidence'] if top else 0}%")


def run():
    print(f"Simulating a live meeting ({MEETING_ID}) - watch confidence build up over time...\n")

    print("[t=0s] Calendar metadata arrives")
    send_event("meeting_metadata", {
        "meeting_id": MEETING_ID,
        "platform": "Google Meet",
        "scheduled_start": "2025-01-15T10:00:00Z",
        "candidate_name": "Rohan Sharma",
        "candidate_email": "rohan.sharma92@gmail.com",
        "interviewer_names": ["Priya Verma"],
        "interviewer_emails": ["priya.verma@sherlock.sh"],
    })

    time.sleep(1)
    print("\n[t=~2s] Interviewer joins")
    send_event("participant_update", {
        "participant_id": "p2", "display_name": "Priya Verma", "email": "priya.verma@sherlock.sh",
        "join_time": "2025-01-15T09:59:40Z", "webcam_on_ratio": 0.8,
        "speaking_duration_sec": 20, "screen_share_events": 0,
    })

    time.sleep(1)
    print("\n[t=~4s] Candidate joins as a device name (classic edge case)")
    send_event("participant_update", {
        "participant_id": "p1", "display_name": "MacBook Pro", "email": None,
        "join_time": "2025-01-15T09:58:12Z", "webcam_on_ratio": 0.95,
        "speaking_duration_sec": 5, "screen_share_events": 0,
    })

    time.sleep(1)
    print("\n[t=~6s] Interviewer asks a question (transcript line)")
    send_event("transcript_line", {
        "participant_id": "p2", "text": "Tell me about your backend experience.",
        "timestamp": "2025-01-15T10:00:30Z",
    })

    time.sleep(1)
    print("\n[t=~8s] Candidate answers, speaking time growing")
    send_event("transcript_line", {
        "participant_id": "p1", "text": "Sure, I've worked with Go and Kafka for four years.",
        "timestamp": "2025-01-15T10:00:50Z",
    })
    send_event("participant_update", {"participant_id": "p1", "speaking_duration_sec": 200})

    time.sleep(1)
    print("\n[t=~10s] Candidate keeps talking, confidence should be climbing now")
    send_event("participant_update", {"participant_id": "p1", "speaking_duration_sec": 600})

    time.sleep(1)
    print("\n[t=~12s] Candidate introduces themselves by name")
    send_event("transcript_line", {
        "participant_id": "p1", "text": "By the way, I'm Rohan, nice to meet you.",
        "timestamp": "2025-01-15T10:01:20Z",
    })
    send_event("participant_update", {"participant_id": "p1", "speaking_duration_sec": 900})

    print("\nDone. Full confidence timeline:")
    resp = requests.get(f"{BACKEND_URL}/timeline/{MEETING_ID}")
    for point in resp.json()["timeline"]:
        print(f"  {point['elapsed_sec']:>6.1f}s -> {point['confidence']:>5}% "
              f"({point['top_candidate']}, status={point['status']})")


if __name__ == "__main__":
    run()

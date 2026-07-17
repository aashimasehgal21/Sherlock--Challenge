"""
tests/test_confidence.py
------------------------

Unit tests for the candidate prediction logic. These tests verify common
meeting scenarios and ensure the confidence scoring behaves as expected.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.services.confidence import compute_confidence
from backend.services.predictor import predict_candidate


BASE_MEETING = {
    "meeting_id": "test-meeting",
    "platform": "Zoom",
    "scheduled_start": "2025-01-15T10:00:00Z",
    "candidate_name": "Rohan Sharma",
    "candidate_email": "rohan.sharma92@gmail.com",
    "interviewer_names": ["Priya Verma", "Amit Kulkarni"],
    "interviewer_emails": ["priya.verma@sherlock.sh", "amit.k@sherlock.sh"],
}


def make_participant(**overrides):
    base = {
        "participant_id": "p1",
        "display_name": "Rohan Sharma",
        "email": "rohan.sharma92@gmail.com",
        "join_time": "2025-01-15T10:00:00Z",
        "leave_time": None,
        "webcam_on_ratio": 0.9,
        "speaking_duration_sec": 800,
        "screen_share_events": 1,
        "is_interviewer_hint": False,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------
# Edge case 1: candidate joins as a device name
# ---------------------------------------------------------------------
def test_device_name_does_not_get_falsely_penalized():
    p = make_participant(display_name="MacBook Pro", email=None)
    result = compute_confidence(p, BASE_MEETING, [p], {})
    name_signal = next(s for s in result["signals"] if s["name"] == "name_match")
    # Device name should be neutral (0.4), not zero
    assert name_signal["score"] == 0.4


# ---------------------------------------------------------------------
# Edge case 2: candidate joins using a nickname
# ---------------------------------------------------------------------
def test_nickname_still_matches_reasonably():
    p = make_participant(display_name="Ro Sharma")
    result = compute_confidence(p, BASE_MEETING, [p], {})
    name_signal = next(s for s in result["signals"] if s["name"] == "name_match")
    assert name_signal["score"] > 0.5, "Nickname should still fuzzy-match the full name reasonably well"


# ---------------------------------------------------------------------
# Edge case 3: interviewer is correctly excluded
# ---------------------------------------------------------------------
def test_known_interviewer_is_excluded():
    interviewer = make_participant(
        participant_id="p2", display_name="Priya Verma", email="priya.verma@sherlock.sh"
    )
    result = compute_confidence(interviewer, BASE_MEETING, [interviewer], {})
    excl_signal = next(s for s in result["signals"] if s["name"] == "interviewer_exclusion")
    assert excl_signal["score"] == 0.0, "Known interviewer must be excluded (score 0)"


# ---------------------------------------------------------------------
# Edge case 4: multiple interviewers present, candidate should still win
# ---------------------------------------------------------------------
def test_candidate_outranks_multiple_interviewers():
    candidate = make_participant(participant_id="p1", display_name="MacBook Pro", email=None,
                                  speaking_duration_sec=1200)
    interviewer1 = make_participant(participant_id="p2", display_name="Priya Verma",
                                     email="priya.verma@sherlock.sh", speaking_duration_sec=300)
    interviewer2 = make_participant(participant_id="p3", display_name="Amit Kulkarni",
                                     email="amit.k@sherlock.sh", speaking_duration_sec=200)
    all_p = [candidate, interviewer1, interviewer2]

    result = predict_candidate(all_p, BASE_MEETING, [])
    assert result["top_candidate"]["participant_id"] == "p1"


# ---------------------------------------------------------------------
# Edge case 5: silent observer should rank low
# ---------------------------------------------------------------------
def test_silent_observer_is_penalized():
    observer = make_participant(participant_id="p4", display_name="Guest 4821", email=None,
                                 webcam_on_ratio=0.0, speaking_duration_sec=0, screen_share_events=0)
    result = compute_confidence(observer, BASE_MEETING, [observer], {})
    penalty_signal = next(s for s in result["signals"] if s["name"] == "silent_observer_penalty")
    assert penalty_signal["score"] == 0.0


# ---------------------------------------------------------------------
# Edge case 6: interviewer enters the wrong candidate name entirely
# ---------------------------------------------------------------------
def test_wrong_calendar_name_does_not_break_the_system():
    wrong_meeting = dict(BASE_MEETING)
    wrong_meeting["candidate_name"] = "Totally Wrong Name"  # simulates interviewer typo
    p = make_participant(display_name="Rohan Sharma")
    all_p = [p]
    # Should not crash, and should still produce a ranked result using
    # OTHER signals (email, speaking ratio, transcript role) since name
    # match alone will now score low.
    result = predict_candidate(all_p, wrong_meeting, [])
    assert result["status"] in ("confident", "ambiguous", "low_confidence")
    assert result["top_candidate"] is not None


# ---------------------------------------------------------------------
# Edge case 7: no participants at all (missing information)
# ---------------------------------------------------------------------
def test_no_participants_returns_insufficient_data():
    result = predict_candidate([], BASE_MEETING, [])
    assert result["status"] == "insufficient_data"
    assert result["ranked"] == []


# ---------------------------------------------------------------------
# Edge case 8: two participants with near-identical scores -> ambiguous
# ---------------------------------------------------------------------
def test_close_scores_trigger_ambiguous_status():
    p1 = make_participant(participant_id="p1", display_name="MacBook Pro", email=None,
                           speaking_duration_sec=500)
    p2 = make_participant(participant_id="p2", display_name="iPhone", email=None,
                           speaking_duration_sec=500)
    result = predict_candidate([p1, p2], BASE_MEETING, [])
    assert result["status"] == "ambiguous"


# ---------------------------------------------------------------------
# Edge case 9: self-introduction by candidate's own name is detected
# ---------------------------------------------------------------------
def test_self_introduction_detected():
    p = make_participant(display_name="MacBook Pro", email=None)
    transcript = [
        {"participant_id": "p1", "text": "Hi, I'm Rohan, nice to meet you.", "timestamp": "2025-01-15T10:00:00Z"},
    ]
    result = compute_confidence(p, BASE_MEETING, [p], {}, transcript)
    intro_signal = next(s for s in result["signals"] if s["name"] == "self_introduction")
    assert intro_signal["passed"] is True


# ---------------------------------------------------------------------
# Edge case 10: result includes a structured explainability checklist
# ---------------------------------------------------------------------
def test_result_includes_checklist():
    p = make_participant()
    result = compute_confidence(p, BASE_MEETING, [p], {})
    assert "checklist" in result
    assert isinstance(result["checklist"], list)
    assert all("label" in item and "passed" in item for item in result["checklist"])


if __name__ == "__main__":
    import subprocess
    subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"])

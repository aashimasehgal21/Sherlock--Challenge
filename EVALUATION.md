# Evaluation

## How I Tested the System

I tested the project in two ways.

First, I used the automated tests available in the project (`tests/test_confidence.py`) to make sure the confidence scoring logic and prediction pipeline were working correctly.

Then I manually tested different meeting scenarios by editing the files inside the `mock_data` folder (`participants.json`, `meeting.json`, and `transcript.json`). After changing the data, I ran the application and checked whether the predicted candidate, confidence score, ranking, and explanation matched the expected result.

I also used `scripts/simulate_live_meeting.py` to simulate a live interview and observed how the confidence changed as new meeting events arrived.

---

## Edge Cases Tested

I tested the following situations:

- Candidate joins with a device name like **"MacBook Pro"** instead of their real name.
- Candidate joins using a nickname.
- Incorrect candidate name is entered in the calendar.
- Multiple interviewers are present in the meeting.
- Silent observers join but never speak.
- Missing participant information.
- Two participants have very similar scores.
- Missing email information.
- OpenAI API is unavailable (fallback logic).

In all these cases, the system continued to return a prediction instead of failing. When there wasn't enough evidence, it returned an appropriate status such as **Ambiguous** or **Insufficient Data** instead of making a random guess.

---

## Results

The prototype correctly identified the intended candidate in all the mock scenarios I tested.

Instead of relying on only one signal, it combined multiple weak signals such as:

- Display name
- Calendar information
- Speaking duration
- Transcript analysis
- Join timing
- Camera activity

As more information became available during the meeting, the confidence score increased gradually. The system also generated an explanation showing why a participant was selected.

---

## Limitations

Since this is a prototype, there are a few limitations.

- The project currently works with mock meeting data instead of real Google Meet, Zoom, or Teams meetings.
- Signal weights are manually chosen and are not learned from real interview data.
- Face verification and voice biometrics are not implemented.
- Audio analysis is limited to speaking duration and activity.
- The current Streamlit demo refreshes periodically. In a production system, this would be replaced with a fully event-driven WebSocket pipeline.
- The system has only been evaluated on manually created scenarios, so no formal accuracy metrics such as Precision or Recall are reported.

---

## Future Improvements

If I continue working on this project, I would like to:

- Connect directly with Google Meet, Microsoft Teams, and Zoom.
- Replace polling with real-time WebSocket updates.
- Add face verification using Computer Vision.
- Include more audio features like speaking rate, pauses, and interruptions.
- Learn confidence weights from historical interview data instead of manually assigning them.
- Evaluate the system on a larger real-world dataset.

---

## Summary

Overall, the prototype successfully demonstrates how multiple weak signals can be combined to identify the interview candidate with an explainable confidence score. Even in situations with incorrect names, multiple interviewers, or missing information, the system is able to reason over the available evidence and continuously update its prediction instead of relying on a single rule.
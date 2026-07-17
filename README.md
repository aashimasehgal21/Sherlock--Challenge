<div align="center">

![Sherlock](https://img.shields.io/badge/SHERLOCK-1a1a2e?style=for-the-badge)
![Candidate ID](https://img.shields.io/badge/REAL--TIME%20CANDIDATE%20IDENTIFICATION-e63946?style=for-the-badge)

# 🕵️ SHERLOCK

### Real-Time Candidate Identification for Live Interviews

> **"Sherlock"** — the detective who identifies the truth from scattered clues.
> This system does the same for interview calls: it looks at names, emails,
> speaking patterns, transcripts, and camera behavior to figure out **who in
> the meeting is actually the candidate** — even when the display name says
> "MacBook Pro."

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.38-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![OpenAI](https://img.shields.io/badge/GPT--4o--mini-OpenAI-412991?style=flat-square&logo=openai&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-optional-3ECF8E?style=flat-square&logo=supabase&logoColor=white)
![WebSockets](https://img.shields.io/badge/WebSockets-real--time-black?style=flat-square&logo=websocket&logoColor=white)

</div>

---

## 📖 Overview

Sherlock is a prototype built for the **Sherlock Internship Challenge**: a
fraud-detection platform needs to point its detectors (deepfake detection,
voice cloning, behavioral analysis) at the *right person* on a live
interview call — not the interviewer, not a silent observer, not a random
device joined under someone's laptop name.

That sounds simple until you look at what actually happens on real calls:

- Candidate joins as **"MacBook Pro"**
- Candidate joins under a **nickname**
- The interviewer typed the **wrong name** when scheduling
- **Multiple interviewers** are on the call
- The candidate **changes their display name** mid-meeting
- **Silent observers** join and never speak

Sherlock doesn't try to solve this with one clever rule. It gathers
independent weak evidence from every part of the meeting, weighs it, and
produces a single **confidence score** it can explain in plain language.

---

## 🧠 How It Works

Every participant is scored on **9 independent signals**. No single signal
decides the outcome — the final score is a weighted blend, so the system
stays right even when any one signal is missing, noisy, or wrong.

| Signal | Weight | What it checks |
|---|---|---|
| `name_match` | 25% | Display name vs. the candidate name from the calendar invite (fuzzy match) |
| `speaking_ratio` | 20% | How much this person talks — candidates usually speak the most |
| `transcript_role` | 20% | LLM reads the transcript and infers who's *answering* vs. who's *asking* |
| `email_match` | 15% | Participant email vs. candidate email |
| `interviewer_exclusion` | 15% | Matches a known interviewer name/email → strongly rejected |
| `silent_observer_penalty` | 10% | Never spoke + camera off → penalized as a likely silent observer |
| `calendar_join_match` | 10% | Join time vs. the scheduled interview start time |
| `webcam_consistency` | 5% | Whether the camera stays on consistently |
| `screenshare_behavior` | 5% | Screen-share activity pattern |

Weights live in `config.py` and can be tuned without touching the scoring
logic itself.

**No OpenAI key? The system still runs.** Every AI-dependent signal has a
safe, deterministic fallback (fuzzy string matching, most-frequent-speaker
heuristic). A key just makes the reasoning sharper — it's never required.

---

## 🏗️ Architecture

```
[Live Meeting: Google Meet / Zoom / Teams]
              │  participant events, audio, transcript (via meeting bot)
              ▼
   ┌─────────────────────────────┐
   │  FastAPI backend             │
   │  /predict  /events  /ws      │
   │  /timeline  /health          │
   └──────────────┬───────────────┘
                  ▼
        [ predictor.py ]  orchestrates one prediction cycle
                  │
   ┌──────────────┼───────────────────────────────┐
   ▼              ▼                ▼               ▼
MetadataAgent  TranscriptAgent  AudioAgent     VisionAgent
(name/email/   (LLM role        (speaking       (webcam/
calendar/      inference via    ratio, VAD,     screenshare,
exclusion)     ai/openai_client)interruptions)  optional face match)
   │              │                │               │
   └──────────────┴───────┬────────┴───────────────┘
                           ▼
                  [ DecisionAgent ]
          combines all signals → confidence + checklist
                           │
              ┌────────────┴─────────────┐
              ▼                          ▼
     [ explanation.py ]          [ database/supabase.py ]
     human-readable "why"        logs prediction history
              │                          
              ▼
     [ Streamlit dashboard ]  +  [ WebSocket live client ]
     ranking, confidence, "Why this score?" breakdown
```

A full diagram is also included as `architecture_diagram.svg`.

---

## 📁 Project Structure

```
Sherlock-AI/
├── frontend/
│   ├── app.py                    # Streamlit dashboard
│   └── static/event_client.html  # WebSocket demo client — zero polling
├── backend/
│   ├── main.py                   # FastAPI entrypoint
│   ├── routes.py                 # /predict /events /ws /timeline /health
│   ├── models/                   # Pydantic request/response schemas
│   ├── agents/                   # Multi-agent scoring system
│   │   ├── metadata_agent.py     # Name/email/calendar/interviewer-exclusion
│   │   ├── transcript_agent.py   # LLM role inference + self-introduction
│   │   ├── audio_agent.py        # Speaking ratio, VAD, interruptions
│   │   ├── vision_agent.py       # Webcam/screenshare + optional face match
│   │   └── decision_agent.py     # Combines agents → final confidence
│   └── services/
│       ├── predictor.py          # Orchestrates one prediction cycle
│       ├── explanation.py        # Turns scores into human explanation
│       ├── bot_adapter.py        # Real meeting-bot webhook → our models
│       ├── event_bus.py          # In-memory pub/sub for WebSocket push
│       ├── live_state.py         # Per-meeting state, mutated by events
│       └── timeline.py           # Confidence-over-time tracker
├── ai/                            # OpenAI wrapper, embeddings, prompts
├── database/                      # Optional Supabase logging
├── scripts/simulate_live_meeting.py
├── mock_data/                     # Messy meeting: device name, wrong name, silent observer
├── tests/
├── config.py                      # SIGNAL_WEIGHTS + all env vars, one place
├── EVALUATION.md                  # Testing approach, edge cases, accuracy
├── VIDEO_SCRIPT.md
└── architecture_diagram.svg
```

## 🔮 What I'd Improve Next

- Real face verification (reference photo vs. webcam face)
- Voice-print matching across interview rounds for the same candidate
- Learned signal weights from labeled historical data instead of fixed weights
- Real bot integration with Meet/Zoom/Teams APIs to replace mock data


"""
frontend/app.py
----------------

Streamlit dashboard for the Sherlock demo.

It fetches predictions from the FastAPI backend and displays the predicted
candidate, confidence score, participant ranking, signal breakdown, and
explanation in a simple UI. It also includes a live update option to
simulate how confidence changes during an ongoing meeting.
"""
import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Sherlock - Candidate Identification", layout="wide")

BACKEND_URL = "http://127.0.0.1:8000"

st.title("🕵️ Sherlock — Real-Time Candidate Identification")
st.caption("Identifies which meeting participant is the actual interview candidate, using multiple weak signals combined into one confidence score.")

# ---- Sidebar ----
st.sidebar.header("Controls")
st.sidebar.write("This demo uses mock meeting data (see `mock_data/`) simulating a messy real interview: a device display name, a wrong interviewer-entered name, and a silent observer.")
run_button = st.sidebar.button("🔄 Run / Refresh Prediction", type="primary", use_container_width=True)

auto_refresh = st.sidebar.toggle("⏱ Auto-refresh (simulate live call)", value=False)
refresh_seconds = st.sidebar.slider("Refresh interval (seconds)", min_value=2, max_value=15, value=5,
                                     disabled=not auto_refresh)
if auto_refresh:
    st.sidebar.caption(f"Polling the backend every {refresh_seconds}s, like a real live interview would. "
                        f"Edit `mock_data/*.json` between refreshes to see the score change.")

st.sidebar.divider()
st.sidebar.markdown(
    "**Want a truly event-driven, zero-polling demo?**\n\n"
    "Run `python scripts/simulate_live_meeting.py` and open "
    "`frontend/static/event_client.html` in a browser — predictions "
    "arrive over a WebSocket the instant an event happens, no polling "
    "loop involved (this Streamlit page still polls, since Streamlit "
    "doesn't support raw WebSockets well - the HTML client is the "
    "true push-based demo)."
)

if "history" not in st.session_state:
    st.session_state.history = []


def call_predict():
    try:
        resp = requests.get(f"{BACKEND_URL}/predict", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Could not reach backend at {BACKEND_URL}. Is `uvicorn backend.main:app --reload` running? Error: {e}")
        return None


if run_button or auto_refresh or not st.session_state.history:
    result = call_predict()
    if result:
        st.session_state.history.append(result)

if st.session_state.history:
    result = st.session_state.history[-1]

    status = result["status"]
    status_colors = {
        "confident": "🟢 CONFIDENT",
        "ambiguous": "🟡 AMBIGUOUS",
        "low_confidence": "🟠 LOW CONFIDENCE",
        "insufficient_data": "🔴 INSUFFICIENT DATA",
    }
    st.subheader(status_colors.get(status, status.upper()))

    if result.get("top_candidate"):
        top = result["top_candidate"]
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Predicted Candidate", top["display_name"], f"{top['confidence']}% confidence")
        with col2:
            st.info(result.get("explanation", "No explanation available."))

    st.markdown("### Ranked Participants")
    for r in result.get("ranked", []):
        st.write(f"**{r['display_name']}** — {r['confidence']}%")
        st.progress(min(r["confidence"] / 100, 1.0))

        with st.expander(f"Why this score? (signal breakdown for {r['display_name']})"):
            checklist = r.get("checklist", [])
            if checklist:
                st.markdown("**Explainability checklist**")
                for item in checklist:
                    mark = "✅" if item["passed"] else "❌"
                    st.markdown(f"{mark} **{item['label']}** — {item['detail']}")
                st.divider()

            st.markdown("**Full signal breakdown (multi-agent scores)**")
            df = pd.DataFrame(r["signals"])
            df["contribution"] = (df["score"] * df["weight"]).round(3)
            df = df[["name", "score", "weight", "contribution", "detail"]]
            df.columns = ["Signal", "Score (0-1)", "Weight", "Contribution", "Detail"]
            st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("### Confidence History (this session)")
    hist_rows = []
    for i, h in enumerate(st.session_state.history):
        if h.get("top_candidate"):
            hist_rows.append({
                "cycle": i + 1,
                "top_candidate": h["top_candidate"]["display_name"],
                "confidence": h["top_candidate"]["confidence"],
            })
    if hist_rows:
        hist_df = pd.DataFrame(hist_rows)
        st.line_chart(hist_df, x="cycle", y="confidence")
        st.dataframe(hist_df, use_container_width=True, hide_index=True)
else:
    st.info("Click **Run / Refresh Prediction** in the sidebar to start.")

# ---- Real polling loop ----
# This is what makes confidence "continuously update" instead of only
# updating on manual clicks - it genuinely re-queries the backend on a
# timer, the same way a live call integration would push new events.
if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()

"""
config.py
---------

Loads the application's environment variables and provides configuration
settings used throughout the project. Default values are used when
optional settings are not available.
"""
import os
from dotenv import load_dotenv

# Load variables from a .env file sitting next to this file
load_dotenv()

# ---- OpenAI ----
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

# ---- Supabase ----
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# ---- App ----
BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

# Feature flags, computed automatically — no need to edit these
USE_OPENAI = bool(OPENAI_API_KEY)
USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)

# Whether to call OpenAI embeddings for semantic name matching (e.g.
# "Bob" vs "Robert" - names with completely different spelling but the
# same meaning). Defaults to OFF because rapidfuzz (free, no API call,
# no latency) already handles the vast majority of real cases -
# nicknames like "Ro" vs "Rohan" or "Amit K" vs "Amit Kulkarni" are
# character-similar, not just meaning-similar. Turn this on only if you
# specifically need to catch classic-nickname cases (Bob/Robert,
# Bill/William, Liz/Elizabeth) that character matching alone misses.
USE_SEMANTIC_NAME_MATCHING = os.getenv("USE_SEMANTIC_NAME_MATCHING", "false").lower() == "true"

# Weights for each signal used in confidence.py (sum doesn't need to be
# exactly 1.0 — we normalize at the end). Tweak these to change behavior.
SIGNAL_WEIGHTS = {
    "name_match": 0.25,
    "email_match": 0.15,
    "calendar_join_match": 0.10,
    "speaking_ratio": 0.20,
    "transcript_role": 0.20,
    "interviewer_exclusion": 0.15,  # penalty, not bonus
    "webcam_consistency": 0.05,
    "screenshare_behavior": 0.05,
    "silent_observer_penalty": 0.10,  # penalty
}

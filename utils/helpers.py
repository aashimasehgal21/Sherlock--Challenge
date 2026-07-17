"""
utils/helpers.py
----------------

Utility functions shared across the project. These helpers handle common
tasks such as name matching, text comparison, and value processing.
"""
import re
from rapidfuzz import fuzz


def normalize(text: str) -> str:
    """Lowercase, strip punctuation/extra spaces so comparisons are fair."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9@._\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def name_similarity(a: str, b: str) -> float:
    """
    Returns 0.0 - 1.0 similarity between two names/strings using fuzzy
    token matching (handles nicknames, partial names, reordered words,
    e.g. "Rohan" vs "Rohan Sharma", or "R. Sharma" vs "Rohan Sharma").
    """
    a, b = normalize(a), normalize(b)
    if not a or not b:
        return 0.0
    # token_set_ratio ignores word order and duplicate words - good for
    # "Sharma Rohan" vs "Rohan Sharma" or partial names.
    score = fuzz.token_set_ratio(a, b) / 100.0
    return round(score, 3)


def email_local_part(email: str) -> str:
    """Return the part before @ in an email, normalized."""
    if not email or "@" not in email:
        return ""
    return normalize(email.split("@")[0])


def looks_like_device_name(display_name: str) -> bool:
    """
    Heuristic: display names like 'MacBook Pro', 'iPhone', 'DESKTOP-8X2K1'
    are device names, not human names — a weak negative signal for name
    matching (it means we should rely MORE on other signals instead).
    """
    if not display_name:
        return True
    device_keywords = [
        "macbook", "iphone", "ipad", "desktop-", "laptop", "pc-",
        "windows", "android", "galaxy", "chromebook", "unknown",
        "guest", "participant",
    ]
    name_lower = display_name.lower()
    return any(k in name_lower for k in device_keywords)


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))

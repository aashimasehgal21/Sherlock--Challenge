"""
ai/embeddings.py
----------------

Ye file basically names aur emails ko compare karne ke liye use hoti hai.

Default me ye OpenAI use nahi karti, kyunki simple name matching ke liye API call
karna unnecessary hai. Isliye rapidfuzz use kiya gaya hai, jo spelling mistakes,
short names aur thode bahut variations ko easily handle kar leta hai.

Examples:
- "Ro Sharma" → "Rohan Sharma"
- "Amit K" → "Amit Kulkarni"

Agar future me semantic matching ki zarurat ho, jahan names completely different
hon but same person ko represent karte hon (jaise Bob ↔ Robert, Bill ↔ William,
Liz ↔ Elizabeth), to `.env` me `USE_SEMANTIC_NAME_MATCHING=true` karke OpenAI
based matching enable ki ja sakti hai.

Abhi prototype me fuzzy matching hi sufficient hai, isliye by default API cost
aur latency dono avoid kiye gaye hain.
"""
import numpy as np
from config import USE_SEMANTIC_NAME_MATCHING
from ai.openai_client import get_embedding
from utils.helpers import name_similarity as fuzzy_similarity


def semantic_similarity(text_a: str, text_b: str) -> float:
    if not USE_SEMANTIC_NAME_MATCHING:
        return fuzzy_similarity(text_a, text_b)

    emb_a = get_embedding(text_a)
    emb_b = get_embedding(text_b)

    if emb_a is not None and emb_b is not None:
        a, b = np.array(emb_a), np.array(emb_b)
        cos_sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
        # cosine similarity is roughly -1..1, clamp to 0..1
        return round(max(0.0, min(1.0, (cos_sim + 1) / 2)), 3)

    # Fallback: pure string fuzzy matching, no API key needed
    return fuzzy_similarity(text_a, text_b)

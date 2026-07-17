"""
ai/openai_client.py
-------------------

Ye file OpenAI API ke saath communication handle karti hai.

Saari OpenAI related requests isi file ke through jaati hain, taaki baaki project
me baar-baar API code na likhna pade.
Agar `.env` me OPENAI_API_KEY available hai, to system LLM se reasoning aur
explanations generate karta hai.
Agar API key available na ho ya API call fail ho jaye, to project crash nahi hota.
Ye automatically fallback logic use karta hai aur prediction continue karta hai.
Bas reasoning thodi simple ho jaati hai.
Isse project bina API key ke bhi end-to-end run ho sakta hai, jo demo aur testing
ke time kaafi useful hai.
"""

from config import OPENAI_API_KEY, OPENAI_CHAT_MODEL, OPENAI_EMBED_MODEL, USE_OPENAI
from utils.logger import get_logger

log = get_logger("openai_client")

_client = None
if USE_OPENAI:
    try:
        from openai import OpenAI
        _client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:  # pragma: no cover
        log.warning(f"Could not init OpenAI client, falling back to offline mode: {e}")
        _client = None


def chat_completion(system_prompt: str, user_prompt: str, max_tokens: int = 400) -> str:
    """Calls the chat model. Returns '' on any failure so callers can fall back."""
    if not _client:
        return ""
    try:
        resp = _client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        log.warning(f"OpenAI chat_completion failed: {e}")
        return ""


def get_embedding(text: str):
    """Returns an embedding vector, or None if unavailable."""
    if not _client or not text:
        return None
    try:
        resp = _client.embeddings.create(model=OPENAI_EMBED_MODEL, input=text)
        return resp.data[0].embedding
    except Exception as e:
        log.warning(f"OpenAI get_embedding failed: {e}")
        return None

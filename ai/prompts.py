"""
ai/prompts.py
-------------

This file contains all the LLM prompt templates in one place.

The idea is to keep prompts separate from the business logic so that if I want
to improve or experiment with prompts later, I only need to update this file
instead of modifying the service code.

Below prompt is used to analyze the interview transcript. LLM transcript ko
read karta hai aur identify karta hai ki candidate kaun hai aur interviewers
kaun hain based on the conversation.

I've also instructed the model to return only a JSON response, because backend
can directly parse it without any extra text. This makes the integration cleaner
and avoids unnecessary post-processing.
"""

TRANSCRIPT_ROLE_SYSTEM_PROMPT = """You are analyzing an interview transcript to figure out which
speaker is the CANDIDATE being interviewed, versus INTERVIEWERS asking questions.

Rules:
- The candidate typically ANSWERS technical/background questions.
- Interviewers typically ASK questions and lead the conversation.
- Return ONLY a JSON object like:
  {"candidate_participant_id": "p1", "confidence": 0.0-1.0, "reason": "short reason"}
- If you cannot tell, set candidate_participant_id to null and confidence to 0.
No extra text, only the JSON object.
"""

def build_transcript_role_prompt(transcript_snippets: str) -> str:
    return f"Transcript (participant_id: text):\n{transcript_snippets}\n\nWho is the candidate?"


AMBIGUITY_RESOLUTION_SYSTEM_PROMPT = """You are a fraud-detection assistant for Sherlock,
an AI platform that must correctly identify the CANDIDATE in a live interview call.

You will be given a list of participants with multiple weak signals (name match score,
email match, speaking time, transcript role, webcam usage, etc.) and their computed
confidence scores. Two or more participants may be close in score.

Explain in 2-3 short sentences, in plain English, why the top participant is most likely
the candidate, referencing the specific signals. Be concise and concrete. If the situation
is genuinely ambiguous, say so plainly and suggest what additional info would resolve it.
"""

def build_ambiguity_prompt(ranked_participants_json: str) -> str:
    return f"Ranked participants with scores and signals:\n{ranked_participants_json}\n\nExplain the decision."
"""ChannelTrace AI assistant: zero-cost, provider-agnostic.

Tries free LLM APIs in order (Gemini free tier, then Groq free tier) and falls back to a
built-in offline answerer so the demo always works without a key or internet.
Only the computed fact sheet is sent to the LLM, never raw uploaded data.
"""
import os

import requests

SYSTEM = (
    "You are ChannelTrace's marketing analytics assistant for small businesses and students. "
    "Answer ONLY from the FACTS below. If the facts do not cover a question, say so and suggest "
    "what data would answer it. Use plain language, short paragraphs, concrete numbers from the facts. "
    "When giving recommendations, mark them as suggestions and remind that the data shows associations, "
    "not proof of cause. Keep answers under 180 words.\n\nFACTS:\n{facts}"
)


def _secret(name: str) -> str | None:
    try:
        import streamlit as st
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name)


def _gemini(key: str, system: str, history: list[dict]) -> str:
    model = _secret("GEMINI_MODEL") or "gemini-2.5-flash"
    contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                for m in history]
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        params={"key": key},
        json={"systemInstruction": {"parts": [{"text": system}]}, "contents": contents,
              "generationConfig": {"temperature": 0.3}},
        timeout=45,
    )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def _groq(key: str, system: str, history: list[dict]) -> str:
    model = _secret("GROQ_MODEL") or "llama-3.3-70b-versatile"
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": model, "temperature": 0.3,
              "messages": [{"role": "system", "content": system}] + history},
        timeout=45,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _offline(facts: str, question: str) -> str:
    """Keyword match over the fact sheet: no AI, but always available."""
    topics = {
        "VISITOR": ["new", "returning", "visitor", "loyal", "retarget"],
        "MONTH": ["month", "season", "november", "nov", "when", "time of year", "festive", "holiday"],
        "TRAFFIC": ["traffic", "source", "channel", "where"],
        "WEEKEND": ["weekend", "weekday", "day"],
        "CONVERTED": ["behaviour", "behavior", "page", "bounce", "exit", "differ", "time spent"],
        "PREDICTIVE": ["model", "predict", "accuracy", "auc"],
        "TOP DRIVERS": ["driver", "factor", "important", "matter", "improve", "increase", "boost", "suggest"],
        "CAVEATS": ["limit", "caveat", "cause", "reliable"],
        "DATASET": ["data", "dataset", "overall", "summary", "rate"],
    }
    q = question.lower()
    lines = facts.splitlines()
    line_for = lambda key: next((ln for ln in lines if ln.startswith(key)), "")
    hits = [line_for(k) for k, words in topics.items() if any(w in q for w in words)]
    if not any(hits):
        hits = [line_for("DATASET"), line_for("TOP DRIVERS")]
    hits = [h for h in hits if h][:3]
    return ("**Offline mode** (no AI key set). Here is what the analysis says:\n\n"
            + "\n\n".join(f"- {h}" for h in hits))


def backend_name() -> str:
    if _secret("GEMINI_API_KEY"):
        return "Gemini (free tier)"
    if _secret("GROQ_API_KEY"):
        return "Groq (free tier)"
    return "Offline (no API key)"


def answer(facts: str, history: list[dict]) -> str:
    system = SYSTEM.format(facts=facts)
    errors = []
    for name, fn in (("GEMINI_API_KEY", _gemini), ("GROQ_API_KEY", _groq)):
        key = _secret(name)
        if not key:
            continue
        try:
            return fn(key, system, history)
        except Exception as e:  # rate limit, network, bad model name: try the next backend
            errors.append(f"{name.split('_')[0].title()}: {e.__class__.__name__}")
    reply = _offline(facts, history[-1]["content"])
    if errors:
        reply = f"_(AI backend unavailable: {'; '.join(errors)}. Falling back.)_\n\n" + reply
    return reply

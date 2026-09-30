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


SYNONYMS = {
    "waste": "zero conversions spent", "wasted": "zero conversions spent", "budget": "spend shift budget",
    "best": "lowest cpa scale candidate", "worst": "highest cpa expensive", "cut": "expensive zero conversions pause",
    "improve": "action suggestion", "should": "action suggestion", "recommend": "action suggestion",
    "suggest": "action suggestion", "channel": "channel attribution", "credit": "attribution",
    "undervalued": "under-credits", "overvalued": "over-credits", "roi": "roas", "return": "roas",
    "audience": "age gender segment targeting", "target": "age gender segment targeting",
    "segment": "age gender", "who": "visitor age gender", "when": "month season", "summary": "dataset overall total",
    "summarise": "dataset overall total", "summarize": "dataset overall total", "limitation": "caveats",
}


def _chunks(facts: str) -> list[tuple[int, str]]:
    """(parent line number, text): one chunk per fact line, plus one per item of list-style lines."""
    out = []
    for n, line in enumerate(l for l in facts.splitlines() if l.strip()):
        out.append((n, line))
        head, _, body = line.partition(":")
        if body.count(";") >= 2:
            out += [(n, f"{head}: {item.strip()}") for item in body.split(";") if item.strip()]
    return out


def _label(head: str) -> str:
    if head.startswith("ACTION"):
        return "Suggested action · " + ("your data" if "your" in head.lower() else "research")
    if head.startswith("UPLOADED"):
        return "Your data · " + head.replace("UPLOADED", "").split("(")[0].strip().lower()
    return head.split("(")[0].strip().capitalize()


def _offline(facts: str, question: str) -> str:
    """Built-in retrieval model: TF-IDF similarity between the question and the fact sheet.
    No internet or API key needed; it only ever quotes computed facts."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    chunks = _chunks(facts)
    q = question.lower()
    q += " " + " ".join(v for k, v in SYNONYMS.items() if k in q)
    vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
    m = vec.fit_transform([c for _, c in chunks] + [q])
    sims = cosine_similarity(m[-1], m[:-1]).ravel()
    if any(c.startswith(("UPLOADED", "ACTION (suggestions for your")) for _, c in chunks):
        # When the user has loaded their own data, prefer it over general research facts.
        sims *= [1.35 if c.startswith(("UPLOADED", "ACTION (suggestions for your")) else 1.0 for _, c in chunks]
    picked, used = [], set()
    for i in sims.argsort()[::-1]:
        if sims[i] < 0.06 or len(picked) == 3:
            break
        parent, text = chunks[i]
        if text.startswith("CAVEATS") and not any(w in question.lower() for w in
                                                  ("limit", "caveat", "cause", "reliab", "trust", "accura", "weak")):
            continue
        if parent in used:  # one answer per fact line, whichever part matched best
            continue
        used.add(parent)
        picked.append(text)
    if not picked:
        return ("I couldn't match that to anything in the current results. Try asking about conversion rates, "
                "visitor types, timing, campaigns, wasted spend, audiences, attribution or limitations.")

    def pretty(c):
        head, _, body = c.partition(":")
        body = body.strip()
        return f"**{_label(head)}.** {body[:1].upper()}{body[1:]}"

    return "\n\n".join(pretty(c) for c in picked)


def backend_name() -> str:
    if _secret("GEMINI_API_KEY"):
        return "Gemini (free tier)"
    if _secret("GROQ_API_KEY"):
        return "Groq (free tier)"
    return "Built-in model (offline)"


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

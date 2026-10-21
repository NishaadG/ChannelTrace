"""RQ5: accuracy test of the ChannelTrace assistant on a fixed question set with known answers.

Each question is asked once, on its own, to both answer paths the site uses: the generative model behind
/api/chat (Gemini free tier) and the built-in TF-IDF retrieval model (run through web/scripts/retrieve.ts).
Answerable questions are correct when the reply contains every expected fact (each fact may have several
accepted spellings). Unanswerable questions are correct when the reply declines and states no number.
Every number in a reply is also checked against the fact sheet; numbers not found there are counted as
unsupported. Replies are saved so each automatic score can be read and checked by hand.

Run: python scripts/eval_assistant.py [api-url]   (writes data/processed/assistant_eval.json)
"""
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = sys.argv[1] if len(sys.argv) > 1 else "https://channeltrace.vercel.app/api/chat"
CACHE = ROOT / "data" / "processed" / "assistant_eval_cache" / "generative.json"  # gitignored
FACTS = json.loads((ROOT / "web" / "public" / "data" / "research.json").read_text(encoding="utf-8"))["facts"]

# (question, expected facts). Each expected fact is a list of accepted spellings (case-insensitive).
ANSWERABLE = [
    ("What is the overall conversion rate in the UCI store data?", [["15.6"]]),
    ("Do new or returning visitors convert better?", [["24.9"], ["14.1"]]),
    ("Which month had the highest conversion rate?", [["nov"], ["25.5"]]),
    ("Which month converted worst?", [["feb"], ["1.7"]]),
    ("Do weekend visitors convert more than weekday visitors?", [["17.5"], ["15.1"]]),
    ("How many product pages do buyers view compared with non-buyers?", [["29"], ["16"]]),
    ("How well can a purchase be predicted without PageValues?", [["0.775", "0.742"]]),
    ("Why is the model without PageValues treated as the honest one?", [["leak", "computed from pages", "before a transaction"]]),
    ("What are the strongest early signals of a purchase?", [["time on product pages"]]),
    ("What share of Criteo conversions was credited to Criteo under last click?", [["54.2", "54%"]]),
    ("How does the time since the last click affect Criteo's credit?", [["87"], ["26"]]),
    ("Does the number of clicks change whether Criteo gets the credit?", [["barely", "little", "hardly", "not much", "slight", "minimal"]]),
    ("How many impressions are in the Criteo dataset?", [["16,468,027", "16.5 million", "16.47 million"]]),
    ("Why can't the Criteo data compare channels within a journey?", [["99.3", "single campaign"]]),
    ("Which attribution model was most accurate when ads act immediately?", [["last touch"], ["4.2"]]),
    ("Which attribution model was most accurate with carry-over effects?", [["time decay"], ["5.7"]]),
    ("Which attribution model was worst in the simulation?", [["first touch"]]),
    ("What was the Markov chain model's error under carry-over?", [["7.5"]]),
    ("How many converting journeys are in the GA360 data?", [["10,022"]]),
    ("What share of GA360 converting journeys used more than one channel?", [["12%", "12 %", "12 per"]]),
    ("How many sessions does a converting GA360 journey take on average?", [["2.28"]]),
    ("In GA360 multi-channel journeys, how much credit does Referral get under last touch?", [["60"]]),
    ("Which channel most often starts a multi-channel journey in GA360?", [["direct"], ["42"]]),
    ("What is the most common multi-channel path in GA360?", [["direct > referral", "direct to referral", "direct → referral", "direct, then referral", "direct followed by referral"]]),
    ("Can I trust Referral's large share of the credit in GA360?", [["97", "no referring site"]]),
    ("Did the Criteo ads cause the conversions?", [["caus", "association"]]),
]
UNANSWERABLE = [
    "What was the return on investment of TV advertising for this store?",
    "How many conversions will the store get next month?",
    "What is the conversion rate of email campaigns in the GA360 data?",
    "Which Instagram influencer drove the most sales?",
    "What was the average order value in the Google Merchandise Store?",
    "How did TikTok ads perform in the Criteo data?",
    "Do mobile users convert better than desktop users?",
    "What is the cost per click of the Criteo campaigns?",
]
DECLINE = re.compile(r"(do(es)? not|don't|doesn't|cannot|can't|not (cover|include|contain|available|provide|have|say|show|mention|specif)|no (data|information|figure)|isn't (available|covered|included)|aren't|not possible|couldn't match|unable)", re.I)
NUM = re.compile(r"\d[\d,]*\.?\d*")


def norm(n: str) -> str:
    n = n.replace(",", "").rstrip(".")
    return n[:-2] if n.endswith(".0") else n


FACT_NUMS = {norm(n) for n in NUM.findall(FACTS)}


def unsupported(reply: str) -> list:
    """Numbers in the reply that appear nowhere in the fact sheet (rounded values like 54% for 54.2% are allowed)."""
    out = []
    for n in {norm(x) for x in NUM.findall(reply)}:
        if n in FACT_NUMS or (n.isdigit() and int(n) <= 10):  # small counts such as "seven models" or "RQ1"
            continue
        if any(f.split(".")[0] == n for f in FACT_NUMS if "." in f):  # rounded percentage
            continue
        out.append(n)
    return out


def ask_gemini(q: str) -> tuple[str, str]:
    """Returns ("", "") when the free tier stays unavailable; the question is then retried on the next run."""
    body = json.dumps({"facts": FACTS, "messages": [{"role": "user", "content": q}]}).encode()
    for attempt in range(3):
        req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                j = json.loads(r.read())
                return j["reply"], j.get("model", "")
        except Exception as e:  # free tier overloaded or over quota: wait and retry
            print("  retry", attempt + 1, e, flush=True)
            time.sleep(60)
    return "", ""


def ask_retrieval(qs: list) -> list:
    out = subprocess.run("npx tsx scripts/retrieve.ts", cwd=ROOT / "web", input=json.dumps({"facts": FACTS, "questions": qs}),
                         capture_output=True, text=True, encoding="utf-8", shell=True, check=True)
    return json.loads(out.stdout)


def score(reply: str, expected) -> bool:
    if expected is None:
        return bool(DECLINE.search(reply)) and not unsupported(reply)
    low = reply.lower()
    return all(any(a.lower() in low for a in alts) for alts in expected)


def main():
    items = [(q, e) for q, e in ANSWERABLE] + [(q, None) for q in UNANSWERABLE]
    retrieval = ask_retrieval([q for q, _ in items])
    # generative replies are kept between runs, so a run cut short by the free tier's quota can be resumed
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    for i, (q, _) in enumerate(items, 1):
        if q in cache:
            continue
        reply, model = ask_gemini(q)
        if reply:
            cache[q] = {"reply": reply, "model": model, "date": time.strftime("%Y-%m-%d")}
            CACHE.write_text(json.dumps(cache, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"{i:2d} {'ok' if reply else 'no reply'} {q}", flush=True)
        time.sleep(8)  # stay under the free tier's requests-per-minute limit
    missing = [q for q, _ in items if q not in cache]
    if missing:
        sys.exit(f"{len(missing)} questions have no generative reply yet; run again later")
    rows = []
    for (q, exp), rr in zip(items, retrieval):
        gr = cache[q]["reply"]
        rows.append({"question": q, "answerable": exp is not None, "expected": exp,
                     "generative": {"reply": gr, "model": cache[q]["model"], "correct": score(gr, exp), "unsupported": unsupported(gr)},
                     "retrieval": {"reply": rr, "correct": score(rr, exp), "unsupported": unsupported(rr)}})

    def summary(kind):
        ans = [r[kind]["correct"] for r in rows if r["answerable"]]
        una = [r[kind]["correct"] for r in rows if not r["answerable"]]
        return {"answerable_correct": sum(ans), "answerable": len(ans), "unanswerable_declined": sum(una),
                "unanswerable": len(una), "overall": (sum(ans) + sum(una)) / len(rows),
                "replies_with_unsupported_numbers": sum(bool(r[kind]["unsupported"]) for r in rows)}

    out = {"api": API, "date": max(v["date"] for v in cache.values()), "n": len(rows),
           "models_used": sorted({r["generative"]["model"] for r in rows}),
           "generative": summary("generative"), "retrieval": summary("retrieval"), "rows": rows}
    (ROOT / "data" / "processed" / "assistant_eval.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("models_used", "generative", "retrieval")}, indent=1))


if __name__ == "__main__":
    main()

import pickle
from pathlib import Path

from src import findings

CACHE = Path(__file__).resolve().parent.parent / "data" / "processed" / "research_findings.pkl"


def build_cache() -> dict:
    f = findings.build()
    f["facts"] = findings.fact_sheet(f)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_bytes(pickle.dumps(f))
    return f


def research() -> dict:
    """Load precomputed results; rebuild with `python -m src.state` after changing the analysis."""
    if CACHE.exists():
        try:
            return pickle.loads(CACHE.read_bytes())
        except Exception:  # cache written by different library versions (e.g. on a cloud host): rebuild
            pass
    return build_cache()


if __name__ == "__main__":
    build_cache()
    print(f"Saved {CACHE}")

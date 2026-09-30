import pickle
from pathlib import Path

import streamlit as st

from src import findings

CACHE = Path(__file__).resolve().parent.parent / "data" / "processed" / "research_findings.pkl"


def build_cache() -> dict:
    f = findings.build()
    f["facts"] = findings.fact_sheet(f)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_bytes(pickle.dumps(f))
    return f


@st.cache_resource(show_spinner="Running the research analysis (first load only)...")
def research() -> dict:
    """Load precomputed results; rebuild with `python -m src.state` after changing the analysis."""
    if CACHE.exists():
        return pickle.loads(CACHE.read_bytes())
    return build_cache()


if __name__ == "__main__":
    build_cache()
    print(f"Saved {CACHE}")

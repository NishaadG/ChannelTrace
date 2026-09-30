# ChannelTrace

Multi-channel digital marketing attribution & conversion analysis: research findings dashboard,
AI assistant, and (next) plug-and-play upload for Google Ads / Meta Ads / journey CSVs. Zero cost.

## Run locally
```
pip install -r requirements.txt
python -m src.state        # precompute research results (only after changing the analysis)
streamlit run app.py
```

## AI assistant (free)
Works with no key (offline mode). For real AI answers, copy `.streamlit/secrets.toml.example`
to `.streamlit/secrets.toml` and add ONE free key:
- Gemini: https://aistudio.google.com/apikey
- Groq: https://console.groq.com/keys

## Structure
- `app.py` navigation · `views/` pages · `src/uci_analysis.py` research analysis (RQ2, RQ4)
- `src/findings.py` dashboard numbers + assistant fact sheet · `src/assistant.py` LLM backends + offline fallback

## Deploy free
Push to GitHub → share.streamlit.io → New app → `app.py`; add the key under App settings → Secrets.

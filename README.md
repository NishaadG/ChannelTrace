# ChannelTrace

Multi-channel digital marketing attribution & conversion analysis (MDM Digital Marketing Capstone, PCCoE).
Research study, plug-and-play analysis of Google Ads / Meta Ads / journey CSVs, and an assistant. Zero cost.

Live site: https://channeltrace.vercel.app

## Structure
- `web/` React site (Vite + TypeScript + Tailwind + Recharts), deployed on Vercel. Uploaded files are analysed in the browser.
- `src/` Python research analysis: `uci_analysis.py` (shopper behaviour), `criteo_analysis.py` (display ads),
  `attribution.py` (7 models), `simulation.py` (known-answer validation), `findings.py` / `state.py` (results cache).
- `scripts/export_web_data.py` exports the results to `web/public/data/research.json`.
- `paper/build_paper.py` builds the draft paper from the saved results. `synopsis_doc/`, `presentation/` Review 1 material.
- `ROADMAP.md` future work.

## Rebuild
```
pip install -r requirements.txt
python -m src.state                # research cache (after changing the analysis)
python scripts/export_web_data.py  # data for the site
python paper/build_paper.py        # paper
cd web && npm install && npm run dev
```

## AI assistant (optional, free)
Works offline by default. For generative answers, add `GEMINI_API_KEY` (https://aistudio.google.com/apikey)
under Vercel → Project → Settings → Environment Variables.

# ChannelTrace roadmap

## Done (Review 1, 1 Oct 2026)
- Synopsis (`synopsis.txt`), dataset validity check and revised dataset roles
- Research findings on UCI (RQ2, RQ4)
- Web app: Overview, Findings, Assistant, Your data
- Plug-and-play ad performance dashboard (Google Ads, Meta, Kaggle Facebook formats)
- Journey attribution with 7 models (first, last, linear, time decay, position, Markov, Shapley)
- Offline TF-IDF assistant plus optional Gemini/Groq, grounded in research and uploaded data

## Next
1. **Power BI-style dashboard** (requested by the team). A proper BI dashboard in place of, or alongside,
   the web page: KPI cards, slicers/filters (campaign, date, channel, age, gender), cross-filtering visuals,
   drill-down, multiple report pages.
   - Zero-cost options to decide between:
     - Power BI Desktop: free on Windows and builds a .pbix file. Sharing online needs a paid Pro licence,
       so demo from the laptop or export to PDF.
     - Looker Studio: free and shareable by link; reads CSV or Google Sheets.
   - The Python pipeline would export clean tables (campaign metrics, attribution shares, journeys, research
     findings) as CSV for the BI tool. The web app keeps the upload and assistant features.
2. GA360 journeys and attribution (RQ1, RQ3). Needs a BigQuery sandbox login.
3. Criteo analysis: single-campaign check, credit across repeated impressions, last-click gap. Process in
   chunks because of low RAM.
4. Attribution validation: bootstrap confidence intervals, Markov held-out fit.
5. Put the web app online for free (GitHub + Streamlit Community Cloud).
6. Evaluation (RQ5): correctness check, SUS usability survey with 8-10 users, assistant accuracy on
   about 30 questions.
7. Draft research paper (target: well before late October).

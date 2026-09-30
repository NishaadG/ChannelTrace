"""Turns the research analysis into (a) numbers for the dashboard and (b) a plain-text
fact sheet the AI assistant is grounded on. The assistant never sees raw rows."""
import pandas as pd

from src import uci_analysis as uci


def build() -> dict:
    df = uci.load()
    visitor = uci.rate_by(df, "VisitorType")
    month = uci.rate_by(df, "Month")
    month["Month"] = pd.Categorical(month["Month"], uci.MONTH_ORDER, ordered=True)
    month = month.sort_values("Month")
    traffic = uci.rate_by(df, "TrafficType", min_sessions=100).sort_values("conversion_rate", ascending=False)
    weekend = uci.rate_by(df, "Weekend")
    return {
        "df": df,
        "sessions": len(df),
        "conversion_rate": df["Revenue"].mean(),
        "visitor": visitor,
        "month": month,
        "traffic": traffic,
        "weekend": weekend,
        "groups": uci.compare_groups(df),
        "p_visitor": uci.chi_square(df, "VisitorType"),
        "p_month": uci.chi_square(df, "Month"),
        "models": uci.model_results(df),
    }


def fact_sheet(f: dict) -> str:
    pct = lambda x: f"{x:.1%}"
    v = f["visitor"].set_index("VisitorType")["conversion_rate"]
    m = f["month"]
    best_m, worst_m = m.loc[m["conversion_rate"].idxmax()], m.loc[m["conversion_rate"].idxmin()]
    t = f["traffic"]
    w = f["weekend"].set_index("Weekend")["conversion_rate"]
    g = f["groups"].set_index("Behaviour")
    mw, mo = f["models"]["with_page_values"], f["models"]["without_page_values"]
    lines = [
        "DATASET: UCI Online Shoppers Purchasing Intention (Sakar & Kastro, 2018): one year of sessions "
        f"on an online store. {f['sessions']:,} sessions after removing duplicates; overall conversion rate {pct(f['conversion_rate'])}.",
        f"VISITOR TYPE: new visitors convert at {pct(v['New_Visitor'])}, returning visitors at "
        f"{pct(v['Returning_Visitor'])} (chi-square p={f['p_visitor']:.1e}). Returning visitors are "
        f"{f['visitor'].set_index('VisitorType').loc['Returning_Visitor','sessions'] / f['sessions']:.0%} of sessions.",
        "MONTH: " + ", ".join(f"{r.Month} {pct(r.conversion_rate)} ({r.sessions} sessions)" for r in m.itertuples())
        + f". Best {best_m.Month}, worst {worst_m.Month} (chi-square p={f['p_month']:.1e}). Jan and Apr are missing from the data.",
        "TRAFFIC SOURCE (anonymised numeric codes; only codes with 100+ sessions): "
        + ", ".join(f"type {r.TrafficType}: {pct(r.conversion_rate)} of {r.sessions}" for r in t.itertuples()) + ".",
        f"WEEKEND: weekend sessions convert at {pct(w[True])} vs weekdays {pct(w[False])}.",
        "CONVERTED vs NOT (medians, all differences significant by Mann-Whitney U, p<0.05): "
        f"product pages {g.loc['Product pages viewed','Median (converted)']:.0f} vs {g.loc['Product pages viewed','Median (not converted)']:.0f}; "
        f"time on product pages {g.loc['Time on product pages (s)','Median (converted)']/60:.1f} vs {g.loc['Time on product pages (s)','Median (not converted)']/60:.1f} minutes; "
        f"mean bounce rate {g.loc['Bounce rate','Mean (converted)']:.3f} vs {g.loc['Bounce rate','Mean (not converted)']:.3f}; "
        f"mean exit rate {g.loc['Exit rate','Mean (converted)']:.3f} vs {g.loc['Exit rate','Mean (not converted)']:.3f}.",
        f"PREDICTIVE MODELS (held-out ROC-AUC): with PageValues, logistic regression {mw['logit_auc']:.3f}, random forest {mw['rf_auc']:.3f}. "
        f"Without PageValues, logistic {mo['logit_auc']:.3f}, random forest {mo['rf_auc']:.3f}. PageValues partly leaks the outcome "
        "(it is computed from pages seen before a transaction), so the 'without' model is the honest view of early-session signals.",
        "TOP DRIVERS WITHOUT PAGEVALUES (random-forest permutation importance): "
        + ", ".join(mo["importance"].head(5)["feature"]) + ".",
        "ACTION (suggestions from the research): re-engage returning visitors, who are most of the traffic but convert "
        "least, for example with remarketing or personalised offers; concentrate campaign budget in the run-up to November; "
        "send paid traffic straight to product pages and work on reducing exits there, since time on product pages is the "
        "strongest early signal of a purchase.",
        "CAVEATS: associations, not causation. Traffic sources are numeric codes with no channel names. "
        "This dataset is session-level, not multi-touch; channel attribution results will come from the Google Analytics 360 sample and Criteo datasets (in progress).",
    ]
    return "\n".join(lines)

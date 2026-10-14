"""RQ1/RQ3 on real multi-channel journeys: Google Analytics 360 sample (Google Merchandise Store, Aug 2016 - Aug 2017).

Queries the public BigQuery dataset through the free sandbox (a Google login opens once in the browser), then runs
the seven attribution models on visitor journeys across sessions. A journey runs up to and including the first
session with a transaction. Converting journeys are downloaded individually (they need timestamps for time decay);
non-converting journeys are aggregated by channel path, which is all the Markov model needs, to keep memory low.

Run: python -m src.ga360_analysis [gcp-project-id]
Writes data/processed/ga360_results.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src import attribution as A

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
CACHE = PROC / "ga360_cache"  # raw query results (gitignored)
PROJECT = sys.argv[1] if len(sys.argv) > 1 else "channeltrace"

JOURNEYS = """
WITH s AS (
  SELECT fullVisitorId AS v, visitStartTime AS t, channelGrouping AS c, IFNULL(totals.transactions, 0) > 0 AS conv
  FROM `bigquery-public-data.google_analytics_sample.ga_sessions_*`
),
f AS (SELECT v, MIN(IF(conv, t, NULL)) AS fc FROM s GROUP BY v),
j AS (SELECT s.v, s.t, s.c, f.fc FROM s JOIN f USING (v) WHERE f.fc IS NULL OR s.t <= f.fc)
"""
CONVERTING = JOURNEYS + "SELECT v AS user_id, t, c AS channel, IF(t = fc, 1, 0) AS converted FROM j WHERE fc IS NOT NULL"
NONCONVERTING = JOURNEYS + """
SELECT path, COUNT(*) AS n FROM (
  SELECT v, ARRAY_TO_STRING(ARRAY_AGG(c ORDER BY t), '>') AS path FROM j WHERE fc IS NULL GROUP BY v
) GROUP BY path
"""
TOTALS = """
SELECT COUNT(*) AS sessions, COUNT(DISTINCT fullVisitorId) AS visitors,
       COUNTIF(IFNULL(totals.transactions, 0) > 0) AS converting_sessions,
       MIN(date) AS first_date, MAX(date) AS last_date
FROM `bigquery-public-data.google_analytics_sample.ga_sessions_*`
"""
CHANNELS = """
SELECT channelGrouping AS channel, COUNT(*) AS sessions, COUNTIF(IFNULL(totals.transactions, 0) > 0) AS converting
FROM `bigquery-public-data.google_analytics_sample.ga_sessions_*` GROUP BY channel ORDER BY sessions DESC
"""
# Referral sessions by recorded source: most have no identifiable referring site
REFERRAL = """
SELECT trafficSource.source = '(direct)' AS no_source, COUNT(*) AS sessions,
       COUNTIF(IFNULL(totals.transactions, 0) > 0) AS converting, COUNTIF(trafficSource.isTrueDirect) AS true_direct
FROM `bigquery-public-data.google_analytics_sample.ga_sessions_*` WHERE channelGrouping = 'Referral' GROUP BY no_source
"""
QUERIES = {"totals": TOTALS, "channels": CHANNELS, "referral": REFERRAL, "nonconverting": NONCONVERTING, "converting": CONVERTING}


def fetch() -> dict:
    CACHE.mkdir(parents=True, exist_ok=True)
    files = {k: CACHE / f"{k}.csv.gz" for k in QUERIES}
    missing = [k for k, f in files.items() if not f.exists()]
    if missing:
        import pydata_google_auth
        from google.cloud import bigquery

        creds = pydata_google_auth.get_user_credentials(["https://www.googleapis.com/auth/bigquery"])
        client = bigquery.Client(project=PROJECT, credentials=creds)
        for key in missing:
            print("query", key, flush=True)
            client.query(QUERIES[key]).to_dataframe(create_bqstorage_client=False).to_csv(files[key], index=False)
    return {k: pd.read_csv(f, dtype={"user_id": str}) for k, f in files.items()}


def main():
    d = fetch()
    conv = d["converting"].assign(timestamp=lambda x: pd.to_datetime(x["t"], unit="s"))
    paths_c = A.build_paths(conv[["user_id", "timestamp", "channel", "converted"]].sort_values(["user_id", "timestamp"]))
    nc = d["nonconverting"]
    paths_n = pd.DataFrame({"path": nc["path"].str.split(">"), "converted": False, "weight": nc["n"].astype(float)})
    paths = pd.concat([paths_c.assign(weight=1.0), paths_n], ignore_index=True)

    table = A.attribute(paths)
    shares = table / table.sum()
    lens = paths_c["path"].map(len)
    distinct = paths_c["path"].map(lambda p: len(set(p)))
    last = shares["Last touch"]
    gap = {m: (shares[m] - last).round(4).to_dict() for m in A.MODELS if m != "Last touch"}
    top = paths_c["path"].map(" > ".join).value_counts().head(10)
    first_last = pd.crosstab(paths_c["path"].map(lambda p: p[0]), paths_c["path"].map(lambda p: p[-1]))
    tot, ch = d["totals"].iloc[0], d["channels"]
    days = paths_c["times"].map(lambda t: (t[-1] - t[0]).total_seconds() / 86400)

    out = {
        "period": f"{tot['first_date']} to {tot['last_date']}",
        "sessions": int(tot["sessions"]), "visitors": int(tot["visitors"]),
        "converting_sessions": int(tot["converting_sessions"]),
        "conversions": int(len(paths_c)),
        "nonconverting_journeys": int(nc["n"].sum()),
        "conv_rate": len(paths_c) / (len(paths_c) + nc["n"].sum()),
        "multi_session_share": float((lens > 1).mean()),
        "multi_channel_share": float((distinct > 1).mean()),
        "sessions_mean": float(lens.mean()), "sessions_max": int(lens.max()),
        "days_first_to_purchase_median_multi": float(days[lens > 1].median()),
        "nonconv_sessions_mean": float((nc["path"].str.count(">") + 1).mul(nc["n"]).sum() / nc["n"].sum()),
        "channels": ch.assign(rate=ch["converting"] / ch["sessions"]).to_dict(orient="records"),
        "shares": {c: {m: float(shares.loc[c, m]) for m in A.MODELS} for c in shares.index},
        "gap_vs_last": gap,
        "top_paths": [[p, int(n)] for p, n in top.items()],
        "first_last": {"rows": first_last.index.tolist(), "cols": first_last.columns.tolist(), "values": first_last.values.tolist()},
    }
    ref = d["referral"].set_index("no_source")
    out["referral_no_source"] = {"sessions_share": float(ref.loc[True, "sessions"] / ref["sessions"].sum()),
                                 "converting_share": float(ref.loc[True, "converting"] / ref["converting"].sum()),
                                 "true_direct_sessions": int(ref["true_direct"].sum()), "sessions": int(ref["sessions"].sum())}
    # where models can disagree at all: converting journeys that used more than one channel
    multi = paths_c[distinct > 1]
    rb = pd.DataFrame(A._rule_based(multi, 7.0)).fillna(0.0)
    ms = (rb / rb.sum()).reindex(shares.index).fillna(0.0)
    out["multi_channel"] = {
        "journeys": int(len(multi)),
        "shares": {c: {m: float(ms.loc[c, m]) for m in rb.columns} for c in ms.index},
        "top_paths": [[q, int(n)] for q, n in multi["path"].map(" > ".join).value_counts().head(8).items()],
    }
    sd = shares.std(axis=1)
    swing = sd.idxmax()
    out["summary_text"] = (
        f"The Google Analytics 360 sample covers {out['visitors']:,} visitors and {out['sessions']:,} sessions of the "
        f"Google Merchandise Store ({out['period']}). Following each visitor across sessions up to the first purchase gives "
        f"{out['conversions']:,} converting journeys ({out['conv_rate']:.1%} of journeys). {out['multi_session_share']:.0%} of "
        f"converting journeys spanned more than one session and {out['multi_channel_share']:.0%} involved more than one "
        f"channel; non-converting journeys averaged {out['nonconv_sessions_mean']:.2f} sessions against "
        f"{out['sessions_mean']:.2f} for converting ones. Across the seven attribution models, {swing} showed the largest "
        f"swing in credit share (from {shares.loc[swing].min():.1%} to {shares.loc[swing].max():.1%}). Within the "
        f"{len(multi):,} multi-channel journeys, first touch gave Direct {ms.loc['Direct', 'First touch']:.0%} of the credit "
        f"against {ms.loc['Direct', 'Last touch']:.0%} under last touch, and Referral {ms.loc['Referral', 'First touch']:.0%} "
        f"against {ms.loc['Referral', 'Last touch']:.0%}."
    )
    (PROC / "ga360_results.json").write_text(json.dumps(out, indent=1, default=float))
    print(out["summary_text"])
    print((shares * 100).round(1).to_string())
    print((ms * 100).round(1).to_string())
    print(out["multi_channel"]["top_paths"])


if __name__ == "__main__":
    main()

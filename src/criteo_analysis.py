"""Criteo Attribution Modeling for Bidding (Diemert et al., 2017): chunked analysis for low-memory machines.

Questions:
- Is each conversion journey tied to a single campaign? (decides whether cross-campaign attribution is valid)
- How long are display-ad journeys before a conversion, and how often is an impression clicked?
- How much credit do rule-based models give to the last vs earlier impressions, and to clicked vs viewed ones?
- How many conversions touched by Criteo ads did Criteo actually receive last-click credit for?
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path(__file__).resolve().parent.parent / "data" / "raw" / "criteo" / "criteo_attribution_dataset.tsv.gz"
OUT = Path(__file__).resolve().parent.parent / "data" / "processed" / "criteo_results.json"
COLS = ["timestamp", "uid", "campaign", "conversion", "conversion_timestamp", "conversion_id", "attribution",
        "click", "cost"]


def main():
    totals = {"impressions": 0, "clicks": 0, "cost": 0.0, "conv_impressions": 0}
    users, campaigns = np.array([], dtype=np.int64), set()
    camp_imps = {}
    conv_parts = []
    for i, ch in enumerate(pd.read_csv(RAW, sep="\t", usecols=COLS, chunksize=1_000_000,
                                       dtype={"uid": "int64", "campaign": "int64", "conversion": "int8",
                                              "attribution": "int8", "click": "int8"})):
        totals["impressions"] += len(ch)
        totals["clicks"] += int(ch["click"].sum())
        totals["cost"] += float(ch["cost"].sum())
        users = np.union1d(users, ch["uid"].unique())
        campaigns.update(ch["campaign"].unique().tolist())
        for c, n in ch["campaign"].value_counts().items():
            camp_imps[c] = camp_imps.get(c, 0) + int(n)
        conv = ch[ch["conversion"] == 1]
        totals["conv_impressions"] += len(conv)
        conv_parts.append(conv)
        print(f"chunk {i}: {totals['impressions']:,} rows", flush=True)

    conv = pd.concat(conv_parts, ignore_index=True)
    del conv_parts
    conv = conv.sort_values(["conversion_id", "timestamp"])
    g = conv.groupby("conversion_id")
    j = pd.DataFrame({
        "touches": g.size(),
        "campaigns": g["campaign"].nunique(),
        "clicks": g["click"].sum(),
        "attributed": g["attribution"].max(),
        "last_clicked": g["click"].last(),
        "first_clicked": g["click"].first(),
        "hours_last_to_conv": (g["conversion_timestamp"].first() - g["timestamp"].last()) / 3600,
        "span_days": (g["timestamp"].last() - g["timestamp"].first()) / 86400,
    })

    # Credit to clicked impressions under each rule (impression-level attribution within a journey)
    pos = conv.assign(n=g["timestamp"].transform("size"), k=g.cumcount())
    lin_w = 1 / pos["n"]
    pb = np.where(pos["n"] == 1, 1.0, np.where(pos["n"] == 2, 0.5,
                  np.where((pos["k"] == 0) | (pos["k"] == pos["n"] - 1), 0.4, 0.2 / (pos["n"] - 2).clip(lower=1))))
    first = (pos["k"] == 0).astype(float)
    last = (pos["k"] == pos["n"] - 1).astype(float)
    n_conv = len(j)
    clicked = pos["click"] == 1
    credit_to_clicked = {
        "First touch": float((first * clicked).sum() / n_conv),
        "Last touch": float((last * clicked).sum() / n_conv),
        "Linear": float((lin_w * clicked).sum() / n_conv),
        "Position based": float((pb * clicked).sum() / n_conv),
    }

    multi = j[j["touches"] > 1]
    j.to_csv(OUT.parent / "criteo_conversion_journeys.csv.gz", compression="gzip")
    by_touches = j.assign(t=j["touches"].clip(upper=6)).groupby("t")["attributed"].agg(["mean", "size"])
    hour_bins = pd.cut(j["hours_last_to_conv"], [0, 1, 6, 24, 72, 168, 24 * 31],
                       labels=["<1h", "1-6h", "6-24h", "1-3d", "3-7d", "7-31d"], include_lowest=True)
    by_hours = j.groupby(hour_bins, observed=False)["attributed"].agg(["mean", "size"])
    res = {
        "impressions": totals["impressions"],
        "users": len(users),
        "campaigns": len(campaigns),
        "clicks": totals["clicks"],
        "ctr": totals["clicks"] / totals["impressions"],
        "conversions": n_conv,
        "conv_impressions": totals["conv_impressions"],
        "share_imps_in_conv_journeys": totals["conv_impressions"] / totals["impressions"],
        "single_campaign_share": float((j["campaigns"] == 1).mean()),
        "touches_mean": float(j["touches"].mean()),
        "touches_median": float(j["touches"].median()),
        "touches_p90": float(j["touches"].quantile(0.9)),
        "single_touch_share": float((j["touches"] == 1).mean()),
        "touches_hist": {str(k): int(v) for k, v in j["touches"].clip(upper=20).value_counts().sort_index().items()},
        "with_click_share": float((j["clicks"] > 0).mean()),
        "last_clicked_share": float(j["last_clicked"].mean()),
        "first_clicked_share": float(j["first_clicked"].mean()),
        "attributed_share": float(j["attributed"].mean()),
        "attributed_given_click": float(j.loc[j["clicks"] > 0, "attributed"].mean()),
        "attributed_given_no_click": float(j.loc[j["clicks"] == 0, "attributed"].mean()),
        "hours_last_to_conv_median": float(j["hours_last_to_conv"].median()),
        "span_days_median_multi": float(multi["span_days"].median()) if len(multi) else None,
        "attributed_by_touches": {str(k): {"share": float(r["mean"]), "n": int(r["size"])} for k, r in by_touches.iterrows()},
        "attributed_by_hours_since_last_click": {str(k): {"share": float(r["mean"]), "n": int(r["size"])}
                                                 for k, r in by_hours.iterrows()},
        "note": "All impressions in converting journeys are clicks: the public sample keeps clicked impressions "
                "for converting users, so click-vs-view effects cannot be measured.",
        "top_campaign_share_of_imps": max(camp_imps.values()) / totals["impressions"],
    }
    OUT.write_text(json.dumps(res, indent=1))
    for k, v in res.items():
        if k != "touches_hist":
            print(k, v)
    print("saved", OUT)


if __name__ == "__main__":
    main()

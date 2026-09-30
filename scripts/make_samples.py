"""Generates the SYNTHETIC sample files used to demo and test the upload tool.

These are not real data. They exist so the tool can be tried without a business export, and so
the attribution code can be checked on journeys whose structure we control.
"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "data" / "samples"
rng = np.random.default_rng(7)


def google_ads():
    # campaign: (daily cost, CTR, CPC, conversion rate, avg order value)
    camps = {
        "Search - Brand": (900, 0.12, 9, 0.11, 2100),
        "Search - Generic": (2600, 0.045, 28, 0.035, 1900),
        "Shopping - All products": (2100, 0.018, 14, 0.028, 1700),
        "Display - Remarketing": (700, 0.006, 6, 0.012, 1600),
        "YouTube - Awareness": (1200, 0.004, 11, 0.002, 1500),
        "Performance Max": (1800, 0.02, 12, 0.03, 1800),
    }
    days = pd.date_range("2026-08-01", "2026-09-29")
    rows = []
    for name, (cost, ctr, cpc, cvr, aov) in camps.items():
        for d in days:
            c = cost * rng.uniform(0.75, 1.25) * (1.15 if d.dayofweek >= 5 else 1)
            clicks = max(1, int(c / (cpc * rng.uniform(0.85, 1.15))))
            impr = int(clicks / (ctr * rng.uniform(0.85, 1.15)))
            conv = rng.binomial(clicks, cvr)
            rows.append([d.strftime("%Y-%m-%d"), name, "Enabled", impr, clicks, round(c, 2), conv,
                         round(conv * aov * rng.uniform(0.8, 1.2), 2)])
    df = pd.DataFrame(rows, columns=["Day", "Campaign", "Campaign status", "Impr.", "Clicks", "Cost",
                                     "Conversions", "Conv. value"])
    path = OUT / "google_ads_synthetic_sample.csv"
    with open(path, "w", newline="") as fh:  # mimic the two title lines of a real Google Ads export
        fh.write("Campaign report (SYNTHETIC SAMPLE, not real data)\n1 August 2026 - 29 September 2026\n")
        df.to_csv(fh, index=False)
    print("wrote", path, len(df))


def journeys(n_users=4000):
    """Channels have known roles: Social and Display open journeys, Email and Paid Search close them,
    Direct often appears last but adds little on its own."""
    channels = ["Organic Search", "Paid Search", "Social", "Email", "Display", "Direct", "Referral"]
    first_p = [0.24, 0.16, 0.26, 0.04, 0.18, 0.08, 0.04]
    lift = {"Organic Search": 0.10, "Paid Search": 0.16, "Social": 0.05, "Email": 0.22, "Display": 0.04,
            "Direct": 0.03, "Referral": 0.08}
    rows = []
    start = pd.Timestamp("2026-08-01")
    for u in range(n_users):
        t = start + pd.Timedelta(days=float(rng.uniform(0, 45)))
        ch = rng.choice(channels, p=first_p)
        path, logit = [], -3.0
        for step in range(8):
            path.append((t, ch))
            logit += lift[ch] * 6
            p_conv = 1 / (1 + np.exp(-logit)) * (0.25 if step == 0 else 0.45)
            if rng.random() < p_conv:
                rows += [[f"U{u:05d}", tt, c, 0] for tt, c in path[:-1]] + [[f"U{u:05d}", t, ch, 1]]
                break
            if rng.random() < 0.35:
                rows += [[f"U{u:05d}", tt, c, 0] for tt, c in path]
                break
            t = t + pd.Timedelta(hours=float(rng.exponential(60)))
            ch = rng.choice(channels, p=[0.18, 0.2, 0.12, 0.2, 0.08, 0.17, 0.05])
        else:
            rows += [[f"U{u:05d}", tt, c, 0] for tt, c in path]
    df = pd.DataFrame(rows, columns=["user_id", "timestamp", "channel", "converted"])
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")
    path = OUT / "journeys_synthetic_sample.csv"
    df.to_csv(path, index=False)
    print("wrote", path, len(df), "rows,", df.user_id.nunique(), "users,", df.converted.sum(), "conversions")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    google_ads()
    journeys()

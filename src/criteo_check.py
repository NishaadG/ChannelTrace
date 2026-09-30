"""Validity check: can the Criteo dataset support cross-campaign (multi-touch) attribution?"""
import zipfile
from pathlib import Path

import pandas as pd

ZIP = Path(__file__).resolve().parent.parent / "data" / "raw" / "criteo" / "criteo.zip"
COLS = ["timestamp", "uid", "campaign", "conversion", "conversion_timestamp", "conversion_id",
        "attribution", "click", "click_pos", "click_nb", "cost"]

with zipfile.ZipFile(ZIP) as z:
    name = next(n for n in z.namelist() if n.endswith((".tsv.gz", ".tsv", ".csv", ".gz")))
    print("file:", name)
    with z.open(name) as fh:
        df = pd.read_csv(fh, sep="\t", usecols=COLS, compression="gzip" if name.endswith(".gz") else None)

print("rows", len(df), "users", df.uid.nunique(), "campaigns", df.campaign.nunique())
conv = df[df.conversion == 1]
print("impressions tied to a conversion", len(conv), "| conversions", conv.conversion_id.nunique())
per_conv = conv.groupby("conversion_id").agg(touches=("timestamp", "size"), campaigns=("campaign", "nunique"),
                                             clicks=("click", "sum"), attributed=("attribution", "max"))
print("\ncampaigns per conversion journey:\n", per_conv.campaigns.value_counts().head())
print("\ntouches per conversion journey:\n", per_conv.touches.describe(percentiles=[.5, .75, .9, .99]))
print("share of journeys with >1 touch:", round((per_conv.touches > 1).mean(), 3))
print("share with >=1 click:", round((per_conv.clicks > 0).mean(), 3))
print("share attributed to Criteo (last-click across all channels):", round(per_conv.attributed.mean(), 3))
per_user = df.groupby("uid").campaign.nunique()
print("\nusers exposed to >1 campaign:", round((per_user > 1).mean(), 3))

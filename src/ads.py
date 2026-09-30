"""Plug-and-play ad performance analysis for Google Ads, Meta Ads and similar CSV exports.

Every input is mapped onto one standard schema:
campaign, group, spend, impressions, clicks, conversions, revenue, date (+ age, gender if present).
"""
import io
import re

import numpy as np
import pandas as pd

ALIASES = {
    "campaign": ["campaign", "campaign name", "xyz_campaign_id"],
    "group": ["ad group", "ad group name", "ad set name", "ad set", "fb_campaign_id"],
    "spend": ["cost", "spend", "spent", "amount spent", "amount spent (usd)", "amount spent (inr)", "amount spent (eur)",
              "amount spent (gbp)"],
    "impressions": ["impressions", "impr.", "impr"],
    "clicks": ["clicks", "link clicks", "clicks (all)"],
    "conversions": ["conversions", "approved_conversion", "results", "purchases", "website purchases", "conv."],
    "revenue": ["conv. value", "conversion value", "all conv. value", "purchases conversion value",
                "website purchases conversion value", "revenue", "purchase conversion value"],
    "date": ["day", "date", "reporting starts"],
    "age": ["age"],
    "gender": ["gender"],
}
REQUIRED = ["campaign", "spend", "clicks", "conversions"]


def _norm(c: str) -> str:
    return re.sub(r"\s+", " ", str(c).strip().lower())


def _match(columns) -> dict:
    found = {}
    normed = {_norm(c): c for c in columns}
    for key, names in ALIASES.items():
        for n in names:
            if n in normed:
                found[key] = normed[n]
                break
        if key not in found and key == "spend":  # "Amount spent (XYZ)" in any currency
            hit = next((orig for nc, orig in normed.items() if nc.startswith("amount spent")), None)
            if hit:
                found[key] = hit
    return found


def _find_header(text: str) -> int:
    """Google Ads exports start with title lines; find the first line that looks like the real header."""
    for i, line in enumerate(text.splitlines()[:15]):
        cells = [c.strip().strip('"') for c in re.split(r"[,\t]", line)]
        if len(_match(cells)) >= 3:
            return i
    return 0


def _to_num(s: pd.Series) -> pd.Series:
    if s.dtype.kind in "if":
        return s.astype(float)
    cleaned = s.astype(str).str.replace(r"[^\d.\-]", "", regex=True).replace({"": "0", "-": "0", "--": "0"})
    return pd.to_numeric(cleaned, errors="coerce").fillna(0.0)


def detect_platform(columns) -> str:
    n = {_norm(c) for c in columns}
    if "xyz_campaign_id" in n:
        return "Facebook Ads (Kaggle export format)"
    if any(c.startswith("amount spent") for c in n) or "ad set name" in n or "reporting starts" in n:
        return "Meta Ads Manager"
    if "impr." in n or "conv." in n or "ad group" in n or ("cost" in n and "conversions" in n):
        return "Google Ads"
    return "Generic ad report"


def load(raw: bytes | str) -> tuple[pd.DataFrame, str, dict]:
    """Returns (standardised frame, platform name, column mapping used)."""
    text = raw.decode("utf-8-sig", errors="replace") if isinstance(raw, bytes) else raw
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    header = _find_header(text)
    sep = "\t" if text.splitlines()[header].count("\t") > text.splitlines()[header].count(",") else ","
    df = pd.read_csv(io.StringIO(text), skiprows=header, sep=sep)
    df = df[~df.iloc[:, 0].astype(str).str.lower().str.startswith("total")]  # drop Google Ads total rows
    mapping = _match(df.columns)
    missing = [k for k in REQUIRED if k not in mapping]
    if missing:
        raise ValueError(f"Could not find column(s) for: {', '.join(missing)}. "
                         f"Found columns: {', '.join(map(str, df.columns))}")
    out = pd.DataFrame({k: df[v] for k, v in mapping.items()})
    for k in ["spend", "impressions", "clicks", "conversions", "revenue"]:
        if k in out:
            out[k] = _to_num(out[k])
    out["campaign"] = out["campaign"].astype(str)
    if "group" in out:
        out["group"] = out["group"].astype(str)
    if "date" in out:
        out["date"] = pd.to_datetime(out["date"], errors="coerce")
    if "impressions" not in out:
        out["impressions"] = np.nan
    return out, detect_platform(df.columns), mapping


def _metrics(g: pd.DataFrame) -> pd.DataFrame:
    g = g.copy()
    safe = lambda a, b: np.where(b > 0, a / b.replace(0, np.nan), np.nan)
    g["ctr"] = safe(g["clicks"], g["impressions"])
    g["cpc"] = safe(g["spend"], g["clicks"])
    g["cvr"] = safe(g["conversions"], g["clicks"])
    g["cpa"] = safe(g["spend"], g["conversions"])
    if "revenue" in g:
        g["roas"] = safe(g["revenue"], g["spend"])
    return g


def summarise(df: pd.DataFrame) -> dict:
    cols = ["spend", "impressions", "clicks", "conversions"] + (["revenue"] if "revenue" in df else [])
    tot = df[cols].sum()
    totals = _metrics(pd.DataFrame([tot])).iloc[0].to_dict()

    camp = _metrics(df.groupby("campaign", as_index=False)[cols].sum())
    camp["spend_share"] = camp["spend"] / tot["spend"] if tot["spend"] else 0
    acct_cpa = totals["cpa"]

    def verdict(r):
        if r.spend > 0 and r.conversions == 0:
            return "No conversions"
        if acct_cpa and r.cpa > 1.5 * acct_cpa:
            return "Expensive"
        if acct_cpa and r.cpa < 0.75 * acct_cpa:
            return "Scale candidate"
        return "On track"

    camp["verdict"] = camp.apply(verdict, axis=1)
    camp = camp.sort_values("spend", ascending=False)

    res = {"totals": totals, "campaigns": camp, "has_revenue": "revenue" in df, "rows": len(df)}

    if "group" in df:
        grp = _metrics(df.groupby(["campaign", "group"], as_index=False)[cols].sum())
        zero = grp[(grp.spend > 0) & (grp.conversions == 0)]
        res["groups"] = grp
        res["zero_conv_groups"] = len(zero)
        res["zero_conv_spend"] = zero["spend"].sum()
        res["waste_unit"] = "ad sets or ad groups"
    else:  # row-level waste (e.g. individual ads)
        zero = df[(df.spend > 0) & (df.conversions == 0)]
        res["zero_conv_groups"] = len(zero)
        res["zero_conv_spend"] = zero["spend"].sum()
        res["waste_unit"] = "campaign-days" if "date" in df else "report rows"
    res["zero_conv_share"] = res["zero_conv_spend"] / tot["spend"] if tot["spend"] else 0

    for dim in ("age", "gender"):
        if dim in df:
            res[dim] = _metrics(df.groupby(dim, as_index=False)[cols].sum()).sort_values(dim)
    if "date" in df and df["date"].notna().any():
        res["daily"] = _metrics(df.groupby("date", as_index=False)[cols].sum())
    return res


def fact_sheet(s: dict, platform: str) -> str:
    t, c = s["totals"], s["campaigns"]
    f = lambda x, d=2: "n/a" if pd.isna(x) else f"{x:,.{d}f}"
    lines = [
        f"UPLOADED AD DATA: {platform}, {s['rows']:,} rows, {len(c)} campaigns. Total spend {f(t['spend'])}, "
        f"{f(t['impressions'], 0)} impressions, {f(t['clicks'], 0)} clicks, {f(t['conversions'], 0)} conversions. "
        f"CTR {t['ctr']:.2%}, CPC {f(t['cpc'])}, conversion rate {t['cvr']:.2%}, CPA {f(t['cpa'])}"
        + (f", ROAS {t['roas']:.2f}x" if s["has_revenue"] else "") + ".",
        "UPLOADED CAMPAIGNS (by spend): " + "; ".join(
            f"{r.campaign}: spend {f(r.spend)} ({r.spend_share:.0%}), {f(r.conversions, 0)} conversions, CPA {f(r.cpa)}"
            + (f", ROAS {r.roas:.2f}x" if s["has_revenue"] and not pd.isna(r.roas) else "") + f", verdict {r.verdict}"
            for r in c.itertuples()) + ".",
        f"UPLOADED WASTE: {s['zero_conv_groups']} {s['waste_unit']} spent money with zero conversions, totalling "
        f"{f(s['zero_conv_spend'])} ({s['zero_conv_share']:.1%} of spend).",
    ]
    scale = c[c.verdict == "Scale candidate"]
    costly = c[c.verdict.isin(["Expensive", "No conversions"])]
    acts = []
    if len(costly) and len(scale):
        acts.append(f"test moving part of the budget from {', '.join(costly.campaign.head(2))} "
                    f"(CPA {', '.join(f(x) for x in costly.cpa.head(2))}) to {', '.join(scale.campaign.head(2))} "
                    f"(CPA {', '.join(f(x) for x in scale.cpa.head(2))})")
    elif len(scale):
        acts.append(f"test raising budget on {', '.join(scale.campaign.head(2))}, which convert well below the account CPA")
    if s["zero_conv_groups"]:
        acts.append(f"review the {s['zero_conv_groups']} {s['waste_unit']} with spend but no conversions "
                    f"({f(s['zero_conv_spend'])} of spend)")
    for dim in ("age", "gender"):
        if dim in s:
            d = s[dim]
            acts.append(f"weight targeting toward {dim} {d.loc[d['cpa'].idxmin()][dim]}, the lowest CPA segment")
    if acts:
        lines.append("ACTION (suggestions for your campaigns): " + "; ".join(acts) + ". Test changes gradually and "
                     "re-check results, since past CPA does not guarantee future performance.")
    for dim in ("age", "gender"):
        if dim in s:
            d = s[dim]
            best = d.loc[d["cpa"].idxmin()]
            worst = d.loc[d["cpa"].idxmax()]
            lines.append(f"UPLOADED BY {dim.upper()}: lowest CPA {best[dim]} ({f(best.cpa)}), highest CPA {worst[dim]} "
                         f"({f(worst.cpa)}). " + "; ".join(f"{r[dim]}: CPA {f(r.cpa)}, CVR {r.cvr:.1%}"
                                                          for _, r in d.iterrows()) + ".")
    return "\n".join(lines)

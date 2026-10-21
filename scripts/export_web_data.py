"""Exports the research results to JSON for the React site (web/public/data) and copies sample files."""
import json
import math
import pickle
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
WEB = ROOT / "web" / "public"
(WEB / "data").mkdir(parents=True, exist_ok=True)
(WEB / "samples").mkdir(parents=True, exist_ok=True)

f = pickle.loads((PROC / "research_findings.pkl").read_bytes())
rec = lambda df: json.loads(df.to_json(orient="records"))
models = {k: {"logit_auc": v["logit_auc"], "rf_auc": v["rf_auc"], "hgb_auc": v.get("hgb_auc"),
              "importance": rec(v["importance"].head(10))} for k, v in f["models"].items()}
uci = {
    "sessions": f["sessions"], "conversion_rate": f["conversion_rate"],
    "purchases": int(f["df"]["Revenue"].sum()),
    "visitor": rec(f["visitor"]), "month": rec(f["month"].assign(Month=f["month"]["Month"].astype(str))),
    "traffic": rec(f["traffic"]), "weekend": rec(f["weekend"]),
    "groups": rec(f["groups"]), "p_visitor": f["p_visitor"], "p_month": f["p_month"], "models": models,
}
out = {
    "uci": uci,
    "criteo": json.loads((PROC / "criteo_results.json").read_text()),
    "simulation": json.loads((PROC / "simulation_results.json").read_text()),
    "synthetic_bootstrap": json.loads((PROC / "synthetic_bootstrap.json").read_text()),
    "facts": f["facts"].replace("channel attribution results will come from the Google Analytics 360 sample and Criteo datasets (in progress).", "channel attribution results come from the Google Analytics 360 sample and Criteo datasets below."),  # pickle predates the GA360 run
}
cr, sim = out["criteo"], out["simulation"]
hours = cr["attributed_by_hours_since_last_click"]
best = lambda name: min(sim[name]["summary"], key=lambda r: r["mae_pp"])
fmt_sim = lambda name: "; ".join(f"{r['model']} {r['mae_pp']:.1f} pp (rank corr {r['spearman']:.2f})" for r in sim[name]["summary"])
out["facts"] += "\n" + "\n".join([
    f"CRITEO DISPLAY ADS: {cr['impressions']:,} impressions, {cr['users']:,} users, {cr['campaigns']} campaigns, "
    f"{cr['conversions']:,} conversions over 30 days. {cr['single_campaign_share']:.1%} of conversions involve a single "
    f"campaign, so the data cannot compare channels or campaigns within a journey. Converting journeys average "
    f"{cr['touches_mean']:.2f} clicks; {cr['single_touch_share']:.0%} have one click.",
    f"CRITEO LAST-CLICK GAP: only {cr['attributed_share']:.1%} of conversions that followed a Criteo click were credited "
    f"to Criteo under the advertiser's last-click rule; the rest went to other channels. Credit depends on recency: "
    f"{hours['<1h']['share']:.0%} when the conversion came within an hour of the click, {hours['1-3d']['share']:.0%} after "
    f"1-3 days and {hours['7-31d']['share']:.0%} after 7-31 days, while the number of clicks barely changes it.",
    f"VALIDATION SIMULATION (known true channel effects, 6 random worlds each): when ads act immediately, mean absolute "
    f"error in credit share was {fmt_sim('immediate')}. When ads act with carry-over (awareness first), it was "
    f"{fmt_sim('carryover')}. Best: {best('immediate')['model']} (immediate), {best('carryover')['model']} (carry-over); "
    "first touch was worst in both, so no single attribution model is best everywhere.",
])
ga = PROC / "ga360_results.json"
if ga.exists():
    g = out["ga360"] = json.loads(ga.read_text())
    mc = g["multi_channel"]["shares"]
    share = lambda d, m: ", ".join(f"{c} {d[c][m]:.0%}" for c in sorted(d, key=lambda c: -d[c][m]) if d[c][m] >= 0.01)
    out["facts"] += "\n" + "\n".join([
        f"GA360 CHANNEL JOURNEYS (Google Merchandise Store, 12 months): {g['visitors']:,} visitors, {g['sessions']:,} sessions, "
        f"{g['conversions']:,} converting journeys ({g['conv_rate']:.1%} of journeys) followed across sessions up to the first "
        f"purchase. {g['multi_session_share']:.0%} of converting journeys took more than one session (mean {g['sessions_mean']:.2f}) "
        f"but only {g['multi_channel_share']:.0%} used more than one channel. Most common multi-channel paths: "
        + "; ".join(f"{q} ({k})" for q, k in g["multi_channel"]["top_paths"][:4]) + ".",
        f"GA360 ATTRIBUTION, all converting journeys: models broadly agree. Last touch: {share(g['shares'], 'Last touch')}. "
        f"Markov: {share(g['shares'], 'Markov chain')}.",
        f"GA360 ATTRIBUTION, the {g['multi_channel']['journeys']:,} multi-channel journeys: first touch: {share(mc, 'First touch')}; "
        f"last touch: {share(mc, 'Last touch')}; linear: {share(mc, 'Linear')}. Direct starts journeys, Referral ends them.",
        f"GA360 CAVEATS: Google Analytics labels a returning direct visit with the previous campaign source "
        f"({g['referral_no_source']['true_direct_sessions']:,} of {g['referral_no_source']['sessions']:,} Referral sessions are "
        f"flagged as direct), so Direct rarely appears late in a journey; {g['referral_no_source']['converting_share']:.0%} of "
        f"converting Referral sessions record no referring site.",
    ])
def clean(o):  # browsers reject NaN/Infinity in JSON
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    return o


(WEB / "data" / "research.json").write_text(json.dumps(clean(json.loads(json.dumps(out, default=float))), allow_nan=False))
for s in (ROOT / "data" / "samples").glob("*.csv"):
    shutil.copy(s, WEB / "samples" / s.name)
print("exported", WEB / "data" / "research.json", round((WEB / "data" / "research.json").stat().st_size / 1024), "KB")

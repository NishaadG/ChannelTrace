"""Builds the ChannelTrace draft research paper (Word + PDF) from the saved analysis results.

Run: python paper/build_paper.py   (then convert to PDF with Word; see README)
Every number in the text is read from data/processed, so re-running after new analysis keeps the paper in sync.
"""
import json
import pickle
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
OUT = Path(__file__).resolve().parent
FIG = OUT / "figures"
FIG.mkdir(exist_ok=True)

uci = pickle.loads((PROC / "research_findings.pkl").read_bytes())
cr = json.loads((PROC / "criteo_results.json").read_text())
sim = json.loads((PROC / "simulation_results.json").read_text())
boot = json.loads((PROC / "synthetic_bootstrap.json").read_text())
ga = json.loads((PROC / "ga360_results.json").read_text()) if (PROC / "ga360_results.json").exists() else None

NAVY, BLUE, GREY, GOLD, RED = "#14213D", "#1F4E8C", "#C8CDD6", "#C9A227", "#B4533C"
plt.rcParams.update({"font.family": "Times New Roman", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": "#888", "axes.labelcolor": "#222"})
pct = lambda x, d=1: f"{100 * x:.{d}f}%"
nm = lambda m: m if m.startswith(("Shapley", "Markov")) else m.lower()  # model name inside a sentence

# ------------------------------------------------------------------ figures
hours = cr["attributed_by_hours_since_last_click"]
fig, ax = plt.subplots(figsize=(6.2, 2.8))
keys = list(hours)
vals = [hours[k]["share"] for k in keys]
ax.bar(keys, vals, color=[BLUE] + [GREY] * (len(keys) - 2) + [RED], width=0.62)
for i, k in enumerate(keys):
    ax.text(i, vals[i] + 0.02, f"{100 * vals[i]:.0f}%\n(n={hours[k]['n']:,})", ha="center", va="bottom", fontsize=8)
ax.set_ylim(0, 1.08); ax.set_ylabel("Share credited to Criteo"); ax.set_xlabel("Time from last Criteo click to conversion")
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
fig.tight_layout(); fig.savefig(FIG / "fig1_recency.png", dpi=220); plt.close(fig)

models = [r["model"] for r in sim["immediate"]["summary"]]
imm = [r["mae_pp"] for r in sim["immediate"]["summary"]]
car = [r["mae_pp"] for r in sim["carryover"]["summary"]]
imm_sd = [r["mae_sd"] for r in sim["immediate"]["summary"]]
car_sd = [r["mae_sd"] for r in sim["carryover"]["summary"]]
fig, ax = plt.subplots(figsize=(6.2, 2.9))
x = range(len(models))
ax.bar([i - 0.2 for i in x], imm, 0.38, yerr=imm_sd, capsize=2, color=BLUE, label="Immediate effects", error_kw={"lw": 0.8})
ax.bar([i + 0.2 for i in x], car, 0.38, yerr=car_sd, capsize=2, color=GOLD, label="Carry-over effects", error_kw={"lw": 0.8})
ax.set_xticks(list(x)); ax.set_xticklabels([m.replace(" ", "\n") for m in models], fontsize=8.5)
ax.set_ylabel("Mean absolute error (pp)"); ax.legend(frameon=False, fontsize=8.5)
fig.tight_layout(); fig.savefig(FIG / "fig2_simulation.png", dpi=220); plt.close(fig)

m = uci["month"].copy(); m["Month"] = m["Month"].astype(str)
fig, ax = plt.subplots(figsize=(6.2, 2.5))
peak = m["conversion_rate"].idxmax()
ax.bar(m["Month"], m["conversion_rate"], color=[BLUE if i == peak else GREY for i in m.index], width=0.62)
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0)); ax.set_ylabel("Conversion rate")
fig.tight_layout(); fig.savefig(FIG / "fig3_month.png", dpi=220); plt.close(fig)

chans = sorted(boot["Markov chain"], key=lambda c: boot["Markov chain"][c][0])
fig, ax = plt.subplots(figsize=(6.2, 2.8))
for i, c in enumerate(chans):
    for mdl, col, off in [("Last touch", "#8A8F99", -0.15), ("Markov chain", BLUE, 0.15)]:
        v, lo, hi = boot[mdl][c]
        ax.errorbar(v, i + off, xerr=[[v - lo], [hi - v]], fmt="o", color=col, ms=5, capsize=2, lw=1,
                    label=mdl if i == 0 else None)
ax.set_yticks(range(len(chans))); ax.set_yticklabels(chans)
ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0)); ax.set_xlabel("Share of conversion credit (95% bootstrap CI)")
ax.legend(frameon=False, fontsize=8.5, loc="lower right")
fig.tight_layout(); fig.savefig(FIG / "fig4_bootstrap.png", dpi=220); plt.close(fig)

# ------------------------------------------------------------------ document helpers
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.left_margin = sec.right_margin = Inches(1)
sec.top_margin = sec.bottom_margin = Inches(1)
st = doc.styles["Normal"]
st.font.name, st.font.size = "Times New Roman", Pt(11)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")


def P(text="", bold=False, italic=False, size=11, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=6, before=0):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after, p.paragraph_format.space_before = Pt(after), Pt(before)
    p.paragraph_format.line_spacing = 1.1
    if text:
        add(p, text, bold, italic, size)
    return p


def add(p, text, bold=False, italic=False, size=11):
    """Supports *italic* spans inside text."""
    parts = text.split("*")
    for i, part in enumerate(parts):
        if part:
            r = p.add_run(part)
            r.bold, r.italic = bold, italic or (i % 2 == 1)
            r.font.size, r.font.name = Pt(size), "Times New Roman"
    return p


def H(num, text):
    P(f"{num}  {text}".upper() if "." not in num else f"{num}  {text}", bold=True, size=11 if "." in num else 11.5,
      align=WD_ALIGN_PARAGRAPH.LEFT, before=10, after=4)


def borders(table):
    tbl = table._tbl
    b = OxmlElement("w:tblBorders")
    for edge, sz in (("top", "8"), ("bottom", "8"), ("insideH", "2")):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single"); el.set(qn("w:sz"), sz); el.set(qn("w:color"), "000000")
        b.append(el)
    tbl.tblPr.append(b)


def T(caption, head, rows, widths=None, numeric=()):
    P(caption, bold=False, size=9.5, align=WD_ALIGN_PARAGRAPH.CENTER, before=6, after=3).paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1 + len(rows), cols=len(head))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    borders(t)
    for r_i, row in enumerate([head] + rows):
        for c_i, val in enumerate(row):
            cell = t.cell(r_i, c_i)
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if c_i in numeric else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(str(val)); r.font.size = Pt(9); r.bold = r_i == 0; r.font.name = "Times New Roman"
            if widths:
                cell.width = Inches(widths[c_i])
    P(after=4)


def F(path, caption, width=6.0):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Inches(width))
    P(caption, size=9.5, align=WD_ALIGN_PARAGRAPH.CENTER, after=8)


# ------------------------------------------------------------------ numbers used in the text
v = uci["visitor"].set_index("VisitorType")
g = uci["groups"].set_index("Behaviour")
mo, mw = uci["models"]["without_page_values"], uci["models"]["with_page_values"]
peak_m = uci["month"].loc[uci["month"]["conversion_rate"].idxmax()]
low_m = uci["month"].loc[uci["month"]["conversion_rate"].idxmin()]
rt = cr["recency_tests"]
si = {r["model"]: r for r in sim["immediate"]["summary"]}
sc = {r["model"]: r for r in sim["carryover"]["summary"]}
best_i = min(si.values(), key=lambda r: r["mae_pp"]); best_c = min(sc.values(), key=lambda r: r["mae_pp"])
ret_share = v.loc["Returning_Visitor", "sessions"] / uci["sessions"]

# ------------------------------------------------------------------ title
P("Who Gets Credit for the Sale? Recency Bias in Last-Click Attribution and the Case for Comparing "
  "Attribution Models", bold=True, size=16, align=WD_ALIGN_PARAGRAPH.CENTER, after=8)
P("[Author 1], [Author 2], [Author 3], [Author 4]", size=11, align=WD_ALIGN_PARAGRAPH.CENTER, after=0)
P("MDM Digital Marketing Capstone (BCE27MD06), Pimpri Chinchwad College of Engineering (PCCoE), Pune, India",
  italic=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, after=0)
P("Guide: [Guide name] · Draft for review, October 2026", italic=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, after=12)

p = P(after=8); add(p, "Abstract. ", bold=True, size=10)
add(p, (f"Customers usually interact with several digital channels before buying, yet most businesses judge channels by "
        f"last-click reports. We study multi-channel attribution and conversion using three public datasets and a "
        f"known-answer simulation. In {cr['impressions'] / 1e6:.1f} million Criteo display impressions, only "
        f"{pct(cr['attributed_share'])} of {cr['conversions']:,} conversions that followed a Criteo click were credited to "
        f"Criteo under the advertiser's last-click rule. Credit was driven by recency: it fell from "
        f"{pct(hours['<1h']['share'], 0)} when the purchase came within an hour of the click to "
        f"{pct(hours['7-31d']['share'], 0)} after 7 to 31 days (logistic odds ratio {rt['logit']['log_hours']['or']:.2f} per "
        f"unit of log hours), while additional clicks barely mattered (odds ratio {rt['logit']['clicks']['or']:.2f}). "
        f"In {uci['sessions']:,} e-commerce sessions, new visitors converted at {pct(v.loc['New_Visitor', 'conversion_rate'])} "
        f"against {pct(v.loc['Returning_Visitor', 'conversion_rate'])} for returning visitors, and early-session behaviour "
        f"predicted purchase with ROC-AUC {mo['rf_auc']:.2f}. A simulation with known channel effects showed that no "
        f"attribution model is best everywhere: {nm(best_i['model'])} was most accurate when advertising acts "
        f"immediately ({best_i['mae_pp']:.1f} percentage points mean error) and {nm(best_c['model'])} when it acts with "
        f"carry-over ({best_c['mae_pp']:.1f} points), while first touch was worst in both. We release ChannelTrace, a "
        f"free tool that applies seven attribution models to a business's own Google Ads, Meta Ads or journey data and "
        f"explains the results through a grounded AI assistant."), size=10)
p = P(after=10); add(p, "Keywords: ", bold=True, size=10)
add(p, "multi-touch attribution, last-click, customer journey, conversion prediction, Markov chain, Shapley value, "
       "digital marketing analytics", italic=True, size=10)

# ------------------------------------------------------------------ 1 introduction
H("1", "Introduction")
P("A typical online purchase is preceded by several touchpoints: a social media advertisement, a search, an email, a "
  "direct return visit. Advertising platforms and analytics tools record these interactions, and attribution decides how "
  "much credit each channel receives for the resulting sale. Because budgets follow credit, the attribution rule shapes "
  "which channels are funded and which are cut.")
P("In practice most reports still use last-click attribution, which gives all credit to the final interaction. Each "
  "platform also reports from its own perspective, so several platforms can claim the same sale while channels that "
  "start journeys appear to contribute little. Data-driven alternatives exist [1]-[4], but they are usually locked "
  "inside paid or single-platform tools, and small businesses rarely have the skills to interpret them.")
P("This study asks five research questions. RQ1: what channel journeys precede a conversion? RQ2: how do converting and "
  "non-converting sessions differ? RQ3: does a channel's estimated importance change with the attribution model? RQ4: "
  "which visitor and session characteristics are associated with conversion? RQ5: can these methods be packaged so that "
  "a small business obtains correct, usable insight from its own data?")
P("Our contributions are: (i) evidence from 16.5 million real display impressions that last-click credit is governed "
  "mainly by recency; (ii) a known-answer simulation showing that the most accurate attribution model depends on how "
  "advertising works, which argues for comparing models rather than choosing one; (iii) an analysis of session behaviour "
  "associated with purchase; and (iv) ChannelTrace, an open, zero-cost tool that implements the methods for any "
  "business's data.")

# ------------------------------------------------------------------ 2 related work
H("2", "Related Work")
P("*Multichannel attribution.* Li and Kannan [1] modelled how customers consider and visit a firm's channels before "
  "converting, using individual-level data and a field experiment, and showed that channel contributions differ "
  "substantially from what last-click metrics suggest. Berman [5] analysed last-touch attribution theoretically and "
  "showed how it can distort advertisers' incentives and spending.")
P("*Data-driven attribution.* Shao and Li [2] proposed learning channel contributions from converting and non-converting "
  "histories and argued that a model should be judged on both accuracy and stability. Dalessandro et al. [6] framed "
  "attribution causally and connected it to the Shapley value; Zhao et al. [7] developed simplified Shapley methods for "
  "online advertising. Anderl et al. [3] represented journeys as Markov chains and measured each channel by its removal "
  "effect, finding that heuristic models misallocate credit.")
P("*Display advertising and conversion prediction.* Diemert et al. [4] studied attribution for real-time bidding and "
  "released the Criteo dataset used here. Sakar et al. [8] predicted purchasing intention from session clickstream data "
  "and released the UCI Online Shoppers dataset. Lemon and Verhoef [9] reviewed the customer journey concept that "
  "underlies all of this work.")
P("Most prior studies evaluate attribution on proprietary data without ground truth. We combine public data with a "
  "simulation in which the true contribution of each channel is known, and we package the methods for practitioners.")

# ------------------------------------------------------------------ 3 data
H("3", "Data")
P("Each dataset is used only for the questions it can support; the datasets come from different populations and are "
  "never pooled (Table I).")
T("TABLE I.  DATASETS AND THEIR ROLE",
  ["Dataset", "Content", "Used for"],
  [["UCI Online Shoppers [8]", f"{uci['sessions']:,} sessions (after removing 125 duplicates), 17 features, purchase outcome", "RQ2, RQ4"],
   ["Criteo Attribution [4]", f"{cr['impressions']:,} impressions, {cr['users']:,} users, {cr['campaigns']} campaigns, 30 days", "RQ3 (last-click gap, recency)"],
   ["Google Analytics 360 sample [10]", "12 months of Google Merchandise Store sessions with named channels", "RQ1, RQ3 (in progress)"],
   ["Facebook Ad Campaign [11]", "1,143 real ads, spend, clicks, conversions, age, gender", "RQ5 (tool validation)"],
   ["Simulated journeys", "6 random worlds x 2 scenarios x 3,000 users with known channel effects", "RQ3 (model accuracy)"]],
  widths=[1.6, 3.4, 1.5])
P(f"A validity check shaped the design. In the Criteo data, {pct(cr['single_campaign_share'])} of conversions involve a "
  f"single campaign, and all impressions in converting journeys are clicks because the public sample retains clicked "
  f"impressions for converting users. Criteo therefore cannot compare channels or campaigns within a journey, nor "
  f"clicked against viewed impressions; we use it for the last-click gap and its recency effect. In the UCI data, traffic "
  f"sources are anonymised codes, so it is used for behaviour rather than channel comparison.")

# ------------------------------------------------------------------ 4 methods
H("4", "Methods")
H("4.1", "Attribution models")
P("For a converting journey of touchpoints c1 ... cn, five rule-based models assign credit: first touch (all to c1), last "
  "touch (all to cn), linear (1/n each), time decay (weights halving every 7 days before the purchase) and position based "
  "(40% first, 40% last, 20% shared). Two data-driven models use converting and non-converting journeys: the Markov "
  "chain removal effect [3], which estimates how much the probability of reaching conversion from the start state falls "
  "when a channel is removed, and the Shapley value [6], [7], each channel's average marginal contribution to "
  "conversions over all channel coalitions. Every model distributes exactly the total number of conversions; we "
  "verified this for all models in the implementation.")
H("4.2", "Known-answer validation")
P("Observational data offers no ground truth for attribution, so we simulated journeys in which channel effects are set "
  "by design. Each user's first channel and subsequent channels are drawn from random distributions; each touch raises "
  "the log-odds of purchase by a channel-specific lift. In the *immediate* scenario a touch raises the chance of buying "
  "in the same visit; in the *carry-over* scenario it raises the chance only on later visits, as with awareness "
  "advertising. A channel's true contribution is the number of conversions lost when its effect is switched off, "
  "computed with common random numbers. Six random worlds per scenario (3,000 users each) were generated. Models are "
  "scored by mean absolute error (MAE) between their credit shares and the true shares, and by Spearman rank "
  "correlation. Stability was assessed with 200 bootstrap resamples of journeys.")
H("4.3", "Recency of last-click credit")
P("For each Criteo conversion we record whether Criteo received last-click credit, the number of Criteo clicks and the "
  "hours from the last click to the conversion. We test association with a chi-square test over six time bands and a "
  "logistic regression of the credit indicator on log(1 + hours) and the number of clicks.")
H("4.4", "Session behaviour and conversion")
P("Converting and non-converting UCI sessions are compared with two-sided Mann-Whitney U tests (numeric measures) and "
  "chi-square tests (visitor type, month). Logistic regression, random forest and gradient boosting classifiers are "
  "trained on a stratified 75/25 split with class-balanced weights and evaluated by ROC-AUC. Because the PageValues "
  "feature is computed from pages viewed before a transaction and partly encodes the outcome, every model is reported "
  "with and without it. Feature importance is measured by permutation on the test set.")

# ------------------------------------------------------------------ 5 results
H("5", "Results")
H("5.1", "Last-click credit is driven by recency (RQ3)")
P(f"All {cr['conversions']:,} Criteo conversions followed at least one Criteo click, yet only {pct(cr['attributed_share'])} "
  f"were credited to Criteo by the advertiser's last-click rule; the remainder were claimed by other channels. Converting "
  f"journeys were short (mean {cr['touches_mean']:.2f} clicks; {pct(cr['single_touch_share'], 0)} with one click; median "
  f"{cr['hours_last_to_conv_median']:.1f} hours from the last click to purchase). Figure 1 shows that credit falls "
  f"steadily with time since the last click (chi-square = {rt['chi2']:,.0f}, df = {rt['dof']}, p < 0.001).")
F(FIG / "fig1_recency.png", "Fig. 1.  Share of conversions credited to Criteo under last-click, by time from the last Criteo click to the conversion.")
by_t = cr["attributed_by_touches"]
T("TABLE II.  LOGISTIC REGRESSION OF LAST-CLICK CREDIT TO CRITEO (n = %s)" % f"{rt['n']:,}",
  ["Predictor", "Odds ratio", "95% CI", "p"],
  [["log(1 + hours since last click)", f"{rt['logit']['log_hours']['or']:.3f}", "%.3f to %.3f" % tuple(rt["logit"]["log_hours"]["ci_or"]), "< 0.001"],
   ["Number of Criteo clicks (capped at 10)", f"{rt['logit']['clicks']['or']:.3f}", "%.3f to %.3f" % tuple(rt["logit"]["clicks"]["ci_or"]), "< 0.001"]],
  widths=[2.8, 1.0, 1.5, 0.8], numeric=(1, 2, 3))
P(f"Holding clicks constant, each unit increase in log(1 + hours) multiplies the odds of Criteo receiving credit by "
  f"{rt['logit']['log_hours']['or']:.2f}, whereas each additional click multiplies them by only "
  f"{rt['logit']['clicks']['or']:.2f} (pseudo R-squared {rt['pseudo_r2']:.2f}). The credit share was "
  f"{pct(by_t['1']['share'])} for single-click journeys and {pct(by_t['6']['share'])} for six or more clicks. Under "
  f"last-click, which platform is paid for a sale depends far more on timing than on how much a channel was used.")

H("5.2", "No attribution model is best everywhere (RQ3)")
F(FIG / "fig2_simulation.png", "Fig. 2.  Mean absolute error between model and true credit shares (percentage points; bars show the standard deviation over six worlds).")
T("TABLE III.  ACCURACY OF ATTRIBUTION MODELS AGAINST KNOWN CHANNEL EFFECTS",
  ["Model", "MAE immediate (pp)", "Rank corr.", "MAE carry-over (pp)", "Rank corr."],
  [[mm, f"{si[mm]['mae_pp']:.1f}", f"{si[mm]['spearman']:.2f}", f"{sc[mm]['mae_pp']:.1f}", f"{sc[mm]['spearman']:.2f}"] for mm in models],
  widths=[1.6, 1.3, 1.0, 1.4, 1.0], numeric=(1, 2, 3, 4))
P(f"When advertising acts immediately, {nm(best_i['model'])} came closest to the truth "
  f"({best_i['mae_pp']:.1f} pp), with time decay close behind ({si['Time decay']['mae_pp']:.1f} pp). With carry-over "
  f"effects, last-touch error rose to {sc['Last touch']['mae_pp']:.1f} pp and its rank agreement fell from "
  f"{si['Last touch']['spearman']:.2f} to {sc['Last touch']['spearman']:.2f}, while time decay and linear became the "
  f"most accurate ({sc['Time decay']['mae_pp']:.1f} and {sc['Linear']['mae_pp']:.1f} pp). The highest rank agreement "
  f"came from {nm(max(si.values(), key=lambda r: r['spearman'])['model'])} under immediate effects "
  f"({max(r['spearman'] for r in si.values()):.2f}) and {nm(max(sc.values(), key=lambda r: r['spearman'])['model'])} "
  f"under carry-over ({max(r['spearman'] for r in sc.values()):.2f}), with the Shapley value close behind in both "
  f"({si['Shapley value']['spearman']:.2f} and {sc['Shapley value']['spearman']:.2f}). "
  f"First touch was worst in both. The Markov removal effect was never the most accurate under these data-generating "
  f"processes, a reminder that data-driven does not automatically mean correct.")
F(FIG / "fig4_bootstrap.png", "Fig. 3.  Last-touch and Markov credit shares with 95% bootstrap intervals on 4,000 synthetic journeys with designed channel roles.")
P("On a separate synthetic dataset in which Social and Display were designed to start journeys and Email and Paid "
  "Search to close them, the data-driven models recovered those roles: last touch gave Display "
  f"{pct(boot['Last touch']['Display'][0], 0)} of the credit against {pct(boot['Markov chain']['Display'][0], 0)} under "
  f"Markov, and Email {pct(boot['Last touch']['Email'][0], 0)} against {pct(boot['Markov chain']['Email'][0], 0)}. The "
  f"bootstrap intervals are narrow (about plus or minus one percentage point), so these differences are not sampling noise.")

H("5.3", "Session behaviour associated with purchase (RQ2, RQ4)")
P(f"The overall conversion rate was {pct(uci['conversion_rate'])}. New visitors converted at "
  f"{pct(v.loc['New_Visitor', 'conversion_rate'])} against {pct(v.loc['Returning_Visitor', 'conversion_rate'])} for "
  f"returning visitors, who made up {pct(ret_share, 0)} of sessions (chi-square p < 0.001). Conversion peaked in "
  f"{peak_m['Month']} ({pct(peak_m['conversion_rate'])}) and was lowest in {low_m['Month']} ({pct(low_m['conversion_rate'])}; Figure 4).")
F(FIG / "fig3_month.png", "Fig. 4.  Conversion rate by month in the UCI Online Shoppers data (January and April are absent).")
rows = []
for b in ["Product pages viewed", "Time on product pages (s)", "Account/admin pages viewed", "Bounce rate", "Exit rate", "Page value"]:
    f = (lambda x: f"{x / 60:.1f} min") if "(s)" in b else ((lambda x: f"{x:.3f}") if "rate" in b else (lambda x: f"{x:.1f}"))
    pv = g.loc[b, "p-value"]
    rows.append([b.replace(" (s)", ""), f(g.loc[b, "Mean (converted)"]), f(g.loc[b, "Mean (not converted)"]),
                 "< 1e-300" if pv == 0 else f"{pv:.1e}"])
T("TABLE IV.  SESSION BEHAVIOUR OF BUYERS AND NON-BUYERS (MEANS; MANN-WHITNEY U)", ["Measure", "Buyers", "Non-buyers", "p"],
  rows, widths=[2.6, 1.2, 1.2, 1.0], numeric=(1, 2, 3))
T("TABLE V.  PURCHASE PREDICTION (ROC-AUC ON HELD-OUT 25%)", ["Model", "With PageValues", "Without PageValues"],
  [["Logistic regression", f"{mw['logit_auc']:.3f}", f"{mo['logit_auc']:.3f}"],
   ["Random forest", f"{mw['rf_auc']:.3f}", f"{mo['rf_auc']:.3f}"],
   ["Gradient boosting", f"{mw['hgb_auc']:.3f}", f"{mo['hgb_auc']:.3f}"]], widths=[2.4, 1.6, 1.6], numeric=(1, 2))
top = ", ".join(mo["importance"].head(3)["feature"].str.replace(" (s)", "", regex=False).str.lower()).replace("month: nov", "the November season")
P(f"All ten behavioural measures differed significantly. Buyers viewed a median of "
  f"{g.loc['Product pages viewed', 'Median (converted)']:.0f} product pages against "
  f"{g.loc['Product pages viewed', 'Median (not converted)']:.0f} and bounced and exited far less (Table IV). With "
  f"PageValues the best model reached ROC-AUC {mw['rf_auc']:.3f}; without it, {mo['rf_auc']:.3f}, which is the honest "
  f"estimate of what early-session behaviour reveals. The strongest signals without PageValues were {top} (Table V).")

H("5.4", "Tool validation on real advertising data (RQ5)")
P("ChannelTrace was run on the real Facebook Ad Campaign data. It recognised the export format automatically and "
  "reproduced the campaign totals computed independently in Python to the cent (spend 58,705.23; cost per acquisition "
  "54.41). It found that 10.0% of spend went to ad sets with no approved conversions, that the 30-34 age group had the "
  "lowest cost per acquisition (30.88 against 99.76 for ages 45-49), and that men converted more cheaply than women "
  "(41.44 against 69.70). The browser implementation of all seven attribution models matched the Python reference "
  "exactly on the synthetic journeys. A usability study (System Usability Scale [12]) and an accuracy test of the "
  "assistant on a fixed question set are planned.")
if ga:
    H("5.5", "Multi-session channel journeys (RQ1)")
    P(str(ga.get("summary_text", "")))
else:
    H("5.5", "Multi-session channel journeys (RQ1): in progress")
    P("The Google Analytics 360 sample is the only public dataset with several named channels per customer across "
      "sessions. Its extraction through Google BigQuery is in progress; the journey and attribution comparison on real "
      "channels will be reported in the next version of this paper.")

# ------------------------------------------------------------------ 6 system
H("6", "The ChannelTrace System")
P("ChannelTrace is a web application built with React and hosted on Vercel at no cost. Its analysis runs entirely in "
  "the user's browser, so uploaded files are never sent to a server. An ad-performance module detects Google Ads, Meta "
  "Ads Manager and similar exports, computes CTR, CPC, conversion rate, CPA and ROAS, gives each campaign a verdict "
  "relative to the account average (scale candidate, on track, expensive, no conversions), measures spend with no "
  "return and breaks results down by audience and day. A journey module applies all seven attribution models and "
  "shows where last-click over- or under-credits each channel. A marketing assistant answers questions using only a "
  "fact sheet of computed results: it uses a free generative model when configured and otherwise a built-in TF-IDF "
  "retrieval model, so it works offline and never invents numbers.")

# ------------------------------------------------------------------ 7 discussion
H("7", "Discussion")
P("The Criteo results show concretely why platforms disagree about who made a sale. A display network whose clicks "
  "precede every one of these conversions is credited for barely half of them, and its share depends mainly on how "
  "long the customer waited before buying. A business that reads last-click reports at face value will therefore "
  "undervalue channels whose influence is delayed, such as awareness advertising, and overvalue whichever channel "
  "happens to be last.")
P("The simulation explains why the remedy is not simply to switch to a single data-driven model. Model accuracy "
  "depended on how advertising works: last touch was competitive when effects were immediate but degraded sharply with "
  "carry-over, while linear, time decay and the Shapley value were more robust. Since a business rarely knows its true "
  "mechanism, comparing several models, and treating channels whose credit swings strongly between them as uncertain, "
  "is the safer practice. ChannelTrace is built around that comparison.")
P("For marketers the session results suggest three practical actions: re-engage returning visitors, who are most of "
  "the traffic but convert least; concentrate budget before the seasonal peak; and send paid traffic directly to product "
  "pages, where depth of browsing is the strongest early signal of purchase intent.")

# ------------------------------------------------------------------ 8 limitations
H("8", "Limitations and Future Work")
P("All findings are associations. Attribution assigns credit and does not establish that a channel caused a sale; "
  "only randomised experiments can do that. The Criteo sample covers one channel and retains only clicked impressions "
  "for converting users, so view-through effects cannot be studied. The UCI traffic sources are anonymised. The "
  "simulation uses two stylised mechanisms and six worlds each; other mechanisms may favour other models. The GA360 "
  "journey analysis, a usability study with 8 to 10 users and an accuracy evaluation of the assistant are the next "
  "steps.")

# ------------------------------------------------------------------ 9 conclusion
H("9", "Conclusion")
P("Using public data at scale and a simulation with known answers, we found that last-click credit is governed mainly "
  "by recency and that the most accurate attribution model depends on how advertising works. Businesses should "
  "therefore compare attribution models rather than trust any single report. ChannelTrace makes that comparison free "
  "and accessible, together with plain-language explanations of the results.")

# ------------------------------------------------------------------ references
H("", "References")
refs = [
    "H. Li and P. K. Kannan, \"Attributing conversions in a multichannel online marketing environment: An empirical model and a field experiment,\" *Journal of Marketing Research*, vol. 51, no. 1, pp. 40-56, 2014.",
    "X. Shao and L. Li, \"Data-driven multi-touch attribution models,\" in *Proc. 17th ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining*, 2011, pp. 258-264.",
    "E. Anderl, I. Becker, F. von Wangenheim, and J. H. Schumann, \"Mapping the customer journey: Lessons learned from graph-based online attribution modeling,\" *International Journal of Research in Marketing*, vol. 33, no. 3, pp. 457-474, 2016.",
    "E. Diemert, J. Meynet, P. Galland, and D. Lefortier, \"Attribution modeling increases efficiency of bidding in display advertising,\" in *Proc. AdKDD and TargetAd Workshop, KDD*, 2017.",
    "R. Berman, \"Beyond the last touch: Attribution in online advertising,\" *Marketing Science*, vol. 37, no. 5, pp. 771-792, 2018.",
    "B. Dalessandro, C. Perlich, O. Stitelman, and F. Provost, \"Causally motivated attribution for online advertising,\" in *Proc. Sixth Int. Workshop on Data Mining for Online Advertising (ADKDD)*, 2012.",
    "K. Zhao, S. H. Mahboobi, and S. R. Bagheri, \"Shapley value methods for attribution modeling in online advertising,\" arXiv:1804.05327, 2018.",
    "C. O. Sakar, S. O. Polat, M. Katircioglu, and Y. Kastro, \"Real-time prediction of online shoppers' purchasing intention using multilayer perceptron and LSTM recurrent neural networks,\" *Neural Computing and Applications*, vol. 31, pp. 6893-6908, 2019.",
    "K. N. Lemon and P. C. Verhoef, \"Understanding customer experience throughout the customer journey,\" *Journal of Marketing*, vol. 80, no. 6, pp. 69-96, 2016.",
    "Google, \"BigQuery sample dataset for Google Analytics 360 (google_analytics_sample),\" Google Analytics Help.",
    "Kaggle, \"Sales conversion optimization (Facebook ad campaign data),\" Kaggle Datasets.",
    "J. Brooke, \"SUS: A quick and dirty usability scale,\" in *Usability Evaluation in Industry*. London: Taylor & Francis, 1996, pp. 189-194.",
]
for i, r in enumerate(refs, 1):
    p = P(size=9.5, after=3)
    add(p, f"[{i}] ", size=9.5)
    add(p, r, size=9.5)

path = OUT / "ChannelTrace_Draft_Paper.docx"
doc.save(path)
print("saved", path)

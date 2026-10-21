"""Builds the extended ChannelTrace research paper (Word; convert to PDF with Word).

Run: python paper/build_paper_extended.py
A longer companion to build_paper.py: fuller related work, model equations, the system architecture, more
GA360 and UCI results and the RQ5 assistant evaluation. It writes its own files (ChannelTrace_Paper_Extended.*,
figures_extended/) and leaves the original draft paper untouched. Every number is read from data/processed.
"""
import json
import pickle
from pathlib import Path

import latex2mathml.converter
import matplotlib
import pandas as pd
from lxml import etree

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from matplotlib.patches import FancyBboxPatch
from scipy.stats import chi2_contingency

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
OUT = Path(__file__).resolve().parent
FIG = OUT / "figures_extended"
FIG.mkdir(exist_ok=True)

uci = pickle.loads((PROC / "research_findings.pkl").read_bytes())
cr = json.loads((PROC / "criteo_results.json").read_text())
sim = json.loads((PROC / "simulation_results.json").read_text())
boot = json.loads((PROC / "synthetic_bootstrap.json").read_text())
ga = json.loads((PROC / "ga360_results.json").read_text())
EVAL = PROC / "assistant_eval.json"  # written by scripts/eval_assistant.py; the RQ5 accuracy parts appear once it exists
ev = json.loads(EVAL.read_text(encoding="utf-8")) if EVAL.exists() else None

NAVY, BLUE, GREY, GOLD, RED = "#14213D", "#1F4E8C", "#C8CDD6", "#C9A227", "#B4533C"
plt.rcParams.update({"font.family": "Times New Roman", "font.size": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
                     "legend.fontsize": 7, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#888", "axes.labelcolor": "#222"})
pct = lambda x, d=1: f"{100 * x:.{d}f}%"
nm = lambda m: m if m.startswith(("Shapley", "Markov")) else m.lower()  # model name inside a sentence

# ------------------------------------------------------------------ references, numbered in order of first citation
REFS = {
    "court09": "D. Court, D. Elzinga, S. Mulder, and O. J. Vetvik, \"The consumer decision journey,\" *McKinsey Quarterly*, no. 3, pp. 96-107, 2009.",
    "lemon16": "K. N. Lemon and P. C. Verhoef, \"Understanding customer experience throughout the customer journey,\" *Journal of Marketing*, vol. 80, no. 6, pp. 69-96, 2016.",
    "kannan17": "P. K. Kannan and H. Li, \"Digital marketing: A framework, review and research agenda,\" *International Journal of Research in Marketing*, vol. 34, no. 1, pp. 22-45, 2017.",
    "berman18": "R. Berman, \"Beyond the last touch: Attribution in online advertising,\" *Marketing Science*, vol. 37, no. 5, pp. 771-792, 2018.",
    "google": "Google, \"About attribution models,\" Google Ads Help. [Online]. Available: https://support.google.com/google-ads/answer/6259715",
    "lewis15": "R. A. Lewis and J. M. Rao, \"The unfavorable economics of measuring the returns to advertising,\" *The Quarterly Journal of Economics*, vol. 130, no. 4, pp. 1941-1973, 2015.",
    "gordon19": "B. R. Gordon, F. Zettelmeyer, N. Bhargava, and D. Chapsky, \"A comparison of approaches to advertising measurement: Evidence from big field experiments at Facebook,\" *Marketing Science*, vol. 38, no. 2, pp. 193-225, 2019.",
    "li14": "H. Li and P. K. Kannan, \"Attributing conversions in a multichannel online marketing environment: An empirical model and a field experiment,\" *Journal of Marketing Research*, vol. 51, no. 1, pp. 40-56, 2014.",
    "shao11": "X. Shao and L. Li, \"Data-driven multi-touch attribution models,\" in *Proc. 17th ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining*, 2011, pp. 258-264.",
    "anderl16": "E. Anderl, I. Becker, F. von Wangenheim, and J. H. Schumann, \"Mapping the customer journey: Lessons learned from graph-based online attribution modeling,\" *International Journal of Research in Marketing*, vol. 33, no. 3, pp. 457-474, 2016.",
    "diemert17": "E. Diemert, J. Meynet, P. Galland, and D. Lefortier, \"Attribution modeling increases efficiency of bidding in display advertising,\" in *Proc. AdKDD and TargetAd Workshop, KDD*, 2017.",
    "wiesel11": "T. Wiesel, K. Pauwels, and J. Arts, \"Marketing's profit impact: Quantifying online and off-line funnel progression,\" *Marketing Science*, vol. 30, no. 4, pp. 604-611, 2011.",
    "kireyev16": "P. Kireyev, K. Pauwels, and S. Gupta, \"Do display ads influence search? Attribution and dynamics in online advertising,\" *International Journal of Research in Marketing*, vol. 33, no. 3, pp. 475-490, 2016.",
    "dehaan16": "E. de Haan, T. Wiesel, and K. Pauwels, \"The effectiveness of different forms of online advertising for purchase conversion in a multiple-channel attribution framework,\" *International Journal of Research in Marketing*, vol. 33, no. 3, pp. 491-507, 2016.",
    "xu14": "L. Xu, J. A. Duan, and A. Whinston, \"Path to purchase: A mutually exciting point process model for online advertising and conversion,\" *Management Science*, vol. 60, no. 6, pp. 1392-1412, 2014.",
    "ji17": "W. Ji and X. Wang, \"Additional multi-touch attribution for online advertising,\" in *Proc. 31st AAAI Conf. Artificial Intelligence*, 2017, pp. 1360-1366.",
    "dalessandro12": "B. Dalessandro, C. Perlich, O. Stitelman, and F. Provost, \"Causally motivated attribution for online advertising,\" in *Proc. Sixth Int. Workshop on Data Mining for Online Advertising (ADKDD)*, 2012.",
    "shapley53": "L. S. Shapley, \"A value for n-person games,\" in *Contributions to the Theory of Games II*, H. W. Kuhn and A. W. Tucker, Eds. Princeton, NJ, USA: Princeton Univ. Press, 1953, pp. 307-317.",
    "zhao18": "K. Zhao, S. H. Mahboobi, and S. R. Bagheri, \"Shapley value methods for attribution modeling in online advertising,\" arXiv:1804.05327, 2018.",
    "singal22": "R. Singal, O. Besbes, A. Désir, V. Goyal, and G. Iyengar, \"Shapley meets uniform: An axiomatic framework for attribution in online advertising,\" *Management Science*, vol. 68, no. 10, pp. 7457-7479, 2022.",
    "lundberg17": "S. M. Lundberg and S.-I. Lee, \"A unified approach to interpreting model predictions,\" in *Advances in Neural Information Processing Systems 30*, 2017, pp. 4765-4774.",
    "li18": "N. Li, S. K. Arava, C. Dong, Z. Yan, and A. Pani, \"Deep neural net with attention for multi-channel multi-touch attribution,\" arXiv:1809.02230, 2018.",
    "ren18": "K. Ren, Y. Fang, W. Zhang, S. Liu, J. Li, Y. Zhang, Y. Yu, and J. Wang, \"Learning multi-touch conversion attribution with dual-attention mechanisms for online advertising,\" in *Proc. 27th ACM Int. Conf. Information and Knowledge Management (CIKM)*, 2018, pp. 1433-1442.",
    "du19": "R. Du, Y. Zhong, H. S. Nair, B. Cui, and R. Shou, \"Causally driven incremental multi touch attribution using a recurrent neural network,\" arXiv:1902.00215, 2019.",
    "kumar20": "S. Kumar, G. Gupta, R. Prasad, A. Chatterjee, L. Vig, and G. Shroff, \"CAMTA: Causal attention model for multi-touch attribution,\" in *Proc. IEEE Int. Conf. Data Mining Workshops (ICDMW)*, 2020, pp. 79-86.",
    "blake15": "T. Blake, C. Nosko, and S. Tadelis, \"Consumer heterogeneity and paid search effectiveness: A large-scale field experiment,\" *Econometrica*, vol. 83, no. 1, pp. 155-174, 2015.",
    "johnson17": "G. A. Johnson, R. A. Lewis, and E. I. Nubbemeyer, \"Ghost ads: Improving the economics of measuring online ad effectiveness,\" *Journal of Marketing Research*, vol. 54, no. 6, pp. 867-884, 2017.",
    "moe04": "W. W. Moe and P. S. Fader, \"Dynamic conversion behavior at e-commerce sites,\" *Management Science*, vol. 50, no. 3, pp. 326-335, 2004.",
    "montgomery04": "A. L. Montgomery, S. Li, K. Srinivasan, and J. C. Liechty, \"Modeling online browsing and path analysis using clickstream data,\" *Marketing Science*, vol. 23, no. 4, pp. 579-595, 2004.",
    "bucklin09": "R. E. Bucklin and C. Sismeiro, \"Click here for Internet insight: Advances in clickstream data analysis in marketing,\" *Journal of Interactive Marketing*, vol. 23, no. 1, pp. 35-48, 2009.",
    "sakar19": "C. O. Sakar, S. O. Polat, M. Katircioglu, and Y. Kastro, \"Real-time prediction of online shoppers' purchasing intention using multilayer perceptron and LSTM recurrent neural networks,\" *Neural Computing and Applications*, vol. 31, pp. 6893-6908, 2019.",
    "ga360": "Google, \"BigQuery sample dataset for Google Analytics 360,\" Google Analytics Help. [Online]. Available: https://support.google.com/analytics/answer/7586738",
    "kaggle": "Kaggle, \"Sales conversion optimization (Facebook ad campaign data),\" Kaggle Datasets. [Online]. Available: https://www.kaggle.com/datasets/loveall/clicks-conversion-tracking",
    "norris97": "J. R. Norris, *Markov Chains*. Cambridge, U.K.: Cambridge Univ. Press, 1997.",
    "spearman04": "C. Spearman, \"The proof and measurement of association between two things,\" *American Journal of Psychology*, vol. 15, no. 1, pp. 72-101, 1904.",
    "efron93": "B. Efron and R. J. Tibshirani, *An Introduction to the Bootstrap*. New York, NY, USA: Chapman & Hall, 1993.",
    "pearson1900": "K. Pearson, \"On the criterion that a given system of deviations from the probable in the case of a correlated system of variables is such that it can be reasonably supposed to have arisen from random sampling,\" *Philosophical Magazine*, ser. 5, vol. 50, no. 302, pp. 157-175, 1900.",
    "mann47": "H. B. Mann and D. R. Whitney, \"On a test of whether one of two random variables is stochastically larger than the other,\" *Annals of Mathematical Statistics*, vol. 18, no. 1, pp. 50-60, 1947.",
    "breiman01": "L. Breiman, \"Random forests,\" *Machine Learning*, vol. 45, no. 1, pp. 5-32, 2001.",
    "friedman01": "J. H. Friedman, \"Greedy function approximation: A gradient boosting machine,\" *Annals of Statistics*, vol. 29, no. 5, pp. 1189-1232, 2001.",
    "pedregosa11": "F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" *Journal of Machine Learning Research*, vol. 12, pp. 2825-2830, 2011.",
    "fawcett06": "T. Fawcett, \"An introduction to ROC analysis,\" *Pattern Recognition Letters*, vol. 27, no. 8, pp. 861-874, 2006.",
    "salton88": "G. Salton and C. Buckley, \"Term-weighting approaches in automatic text retrieval,\" *Information Processing & Management*, vol. 24, no. 5, pp. 513-523, 1988.",
    "lewis20": "P. Lewis et al., \"Retrieval-augmented generation for knowledge-intensive NLP tasks,\" in *Advances in Neural Information Processing Systems 33*, 2020, pp. 9459-9474.",
    "ji23": "Z. Ji et al., \"Survey of hallucination in natural language generation,\" *ACM Computing Surveys*, vol. 55, no. 12, pp. 1-38, 2023.",
    "brooke96": "J. Brooke, \"SUS: A quick and dirty usability scale,\" in *Usability Evaluation in Industry*. London, U.K.: Taylor & Francis, 1996, pp. 189-194.",
}
ORDER: list = []


def c(*keys):
    """IEEE citation: numbers assigned in order of first use; consecutive numbers collapse to a range."""
    nums = []
    for k in keys:
        if k not in ORDER:
            ORDER.append(k)
        nums.append(ORDER.index(k) + 1)
    nums = sorted(set(nums))
    parts, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        parts.append(f"[{nums[i]}]" if j == i else (f"[{nums[i]}], [{nums[j]}]" if j == i + 1 else f"[{nums[i]}]-[{nums[j]}]"))
        i = j + 1
    return ", ".join(parts)


# ------------------------------------------------------------------ figures
hours = cr["attributed_by_hours_since_last_click"]
fig, ax = plt.subplots(figsize=(3.5, 2.3))
keys = list(hours)
vals = [hours[k]["share"] for k in keys]
ax.bar(keys, vals, color=[BLUE] + [GREY] * (len(keys) - 2) + [RED], width=0.62)
for i, k in enumerate(keys):
    ax.text(i, vals[i] + 0.02, f"{100 * vals[i]:.0f}%\n({hours[k]['n'] / 1000:.0f}k)", ha="center", va="bottom", fontsize=6.5)
ax.set_ylim(0, 1.15); ax.set_ylabel("Share credited to Criteo"); ax.set_xlabel("Time from last Criteo click to conversion")
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
fig.tight_layout(); fig.savefig(FIG / "recency.png", dpi=300); plt.close(fig)

models = [r["model"] for r in sim["immediate"]["summary"]]
imm = [r["mae_pp"] for r in sim["immediate"]["summary"]]
car = [r["mae_pp"] for r in sim["carryover"]["summary"]]
imm_sd = [r["mae_sd"] for r in sim["immediate"]["summary"]]
car_sd = [r["mae_sd"] for r in sim["carryover"]["summary"]]
fig, ax = plt.subplots(figsize=(3.5, 2.3))
x = range(len(models))
ax.bar([i - 0.2 for i in x], imm, 0.38, yerr=imm_sd, capsize=2, color=BLUE, label="Immediate effects", error_kw={"lw": 0.8})
ax.bar([i + 0.2 for i in x], car, 0.38, yerr=car_sd, capsize=2, color=GOLD, label="Carry-over effects", error_kw={"lw": 0.8})
ax.set_xticks(list(x)); ax.set_xticklabels([m.replace(" ", "\n") for m in models], fontsize=6.5)
ax.set_ylabel("Mean absolute error (pp)"); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(FIG / "simulation.png", dpi=300); plt.close(fig)

m = uci["month"].copy(); m["Month"] = m["Month"].astype(str)
fig, ax = plt.subplots(figsize=(3.5, 1.9))
peak = m["conversion_rate"].idxmax()
ax.bar(m["Month"], m["conversion_rate"], color=[BLUE if i == peak else GREY for i in m.index], width=0.62)
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0)); ax.set_ylabel("Conversion rate")
fig.tight_layout(); fig.savefig(FIG / "month.png", dpi=300); plt.close(fig)

chans = sorted(boot["Markov chain"], key=lambda ch: boot["Markov chain"][ch][0])
fig, ax = plt.subplots(figsize=(3.5, 2.3))
for i, ch in enumerate(chans):
    for mdl, col, off in [("Last touch", "#8A8F99", -0.15), ("Markov chain", BLUE, 0.15)]:
        val, lo, hi = boot[mdl][ch]
        ax.errorbar(val, i + off, xerr=[[val - lo], [hi - val]], fmt="o", color=col, ms=3.5, capsize=2, lw=1,
                    label=mdl if i == 0 else None)
ax.set_yticks(range(len(chans))); ax.set_yticklabels(chans)
ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0)); ax.set_xlabel("Share of conversion credit (95% bootstrap CI)")
ax.legend(frameon=False, loc="lower right")
fig.tight_layout(); fig.savefig(FIG / "bootstrap.png", dpi=300); plt.close(fig)

mc = ga["multi_channel"]["shares"]
gch = sorted([ch for ch in mc if mc[ch]["Linear"] > 0.005], key=lambda ch: mc[ch]["Linear"])
fig, ax = plt.subplots(figsize=(3.5, 2.4))
for j, (mdl, col) in enumerate([("First touch", GOLD), ("Linear", GREY), ("Last touch", BLUE)]):
    ax.barh([i + (j - 1) * 0.26 for i in range(len(gch))], [mc[ch][mdl] for ch in gch], 0.25, color=col, label=mdl)
ax.set_yticks(range(len(gch))); ax.set_yticklabels(gch)
ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0)); ax.set_xlabel("Share of conversion credit")
ax.legend(frameon=False, loc="lower right")
fig.tight_layout(); fig.savefig(FIG / "ga360.png", dpi=300); plt.close(fig)

# system architecture
fig, ax = plt.subplots(figsize=(3.5, 2.9))
ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")


def box(x0, y0, w, h, text, fc="#FFFFFF", ec=NAVY, bold=False):
    ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0.02,rounding_size=0.25", fc=fc, ec=ec, lw=0.9))
    ax.text(x0 + w / 2, y0 + h / 2, text, ha="center", va="center", fontsize=6.6, color="#111", weight="bold" if bold else "normal")


def arrow(x0, y0, x1, y1):
    ax.annotate("", (x1, y1), (x0, y0), arrowprops={"arrowstyle": "-|>", "color": "#444", "lw": 0.8, "shrinkA": 0, "shrinkB": 0})


ax.add_patch(FancyBboxPatch((0.15, 2.55), 9.7, 6.0, boxstyle="round,pad=0.02,rounding_size=0.3", fc="#F2F4F8", ec="#8A8F99", lw=0.8, ls="--"))
ax.text(0.45, 8.2, "User's browser (raw rows never leave)", fontsize=6.4, color="#555", style="italic")
box(0.5, 9.0, 9.0, 0.85, "CSV export: Google Ads, Meta Ads Manager or touchpoint journeys", fc="#FFF8E6", ec=GOLD)
box(0.6, 6.75, 8.8, 0.95, "Format detection, column mapping and cleaning (PapaParse)")
box(0.6, 4.75, 4.2, 1.35, "Ad performance\nCTR, CPC, CPA, ROAS,\nverdicts, wasted spend")
box(5.2, 4.75, 4.2, 1.35, "Journey attribution\n5 rule-based + Markov\n+ Shapley models")
box(0.6, 2.85, 4.2, 1.2, "Charts and tables\n(Recharts)")
box(5.2, 2.85, 4.2, 1.2, "Fact sheet\n(aggregated results only)", fc="#E8EEF7", ec=BLUE, bold=True)
box(0.5, 0.2, 4.3, 1.7, "Generative model\n/api/chat edge function\n(Gemini free tier)", fc="#FFFFFF", ec=RED)
box(5.2, 0.2, 4.3, 1.7, "Built-in fallback\nTF-IDF retrieval over\nthe fact sheet", fc="#FFFFFF", ec=RED)
arrow(5, 9.0, 5, 7.7)
arrow(2.7, 6.75, 2.7, 6.1); arrow(7.3, 6.75, 7.3, 6.1)
arrow(2.7, 4.75, 2.7, 4.05); arrow(7.3, 4.75, 7.3, 4.05); arrow(4.8, 5.1, 5.2, 3.9)
arrow(6.6, 2.85, 3.6, 1.9); arrow(7.3, 2.85, 7.3, 1.9)
fig.tight_layout(pad=0.1); fig.savefig(FIG / "architecture.png", dpi=300); plt.close(fig)

# ------------------------------------------------------------------ document helpers
# IEEE conference layout: US Letter, 10 pt Times, title block in one column, body in two 3.5" columns
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.left_margin = sec.right_margin = Inches(0.625)
sec.top_margin, sec.bottom_margin = Inches(0.75), Inches(1)
st = doc.styles["Normal"]
st.font.name, st.font.size = "Times New Roman", Pt(10)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.paragraph_format.space_after = Pt(0)
COL = 3.5  # column width in inches


def columns(section, n):
    cols = section._sectPr.xpath("./w:cols")
    el = cols[0] if cols else OxmlElement("w:cols")
    el.set(qn("w:num"), str(n)); el.set(qn("w:space"), "360")
    if not cols:
        section._sectPr.append(el)


def P(text="", bold=False, italic=False, size=10, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=0, before=0, indent=True, caps=False):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.space_after, pf.space_before, pf.line_spacing = Pt(after), Pt(before), 1.0
    if indent and align == WD_ALIGN_PARAGRAPH.JUSTIFY:
        pf.first_line_indent = Inches(0.14)
    if text:
        add(p, text, bold, italic, size, caps)
    return p


# Word's own MathML-to-equation stylesheet, so equations are native, editable Word equations
MML2OMML = etree.XSLT(etree.parse(r"C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL"))


M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"


def omml(latex):
    root = MML2OMML(etree.fromstring(latex2mathml.converter.convert(latex))).getroot()
    # the converter leaves a sum's body empty and puts the summand after it; move the rest of the expression inside
    for nary in root.iter(M + "nary"):
        body = nary.find(M + "e")
        if body is not None and not len(body):
            for sib in list(nary.itersiblings()):
                body.append(sib)
    return root


def add(p, text, bold=False, italic=False, size=10, caps=False):
    """Supports *italic* spans and $latex$ inline equations inside text."""
    for k, seg in enumerate(text.split("$")):
        if k % 2:
            p._p.append(omml(seg))
            continue
        for i, part in enumerate(seg.split("*")):
            if part:
                r = p.add_run(part)
                r.bold, r.italic = bold, italic or (i % 2 == 1)
                r.font.size, r.font.name, r.font.small_caps = Pt(size), "Times New Roman", caps
    return p


EQ = iter(range(1, 100))


def E(latex):
    """Numbered display equation: centred, number flush right."""
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before, pf.space_after = Pt(3), Pt(3)
    pf.tab_stops.add_tab_stop(Inches(COL / 2), WD_TAB_ALIGNMENT.CENTER)
    pf.tab_stops.add_tab_stop(Inches(COL), WD_TAB_ALIGNMENT.RIGHT)
    add(p, "\t")
    p._p.append(omml(latex))
    add(p, f"\t({next(EQ)})")


ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]


def H(num, text):
    """IEEE headings: 'I. Introduction' centred in small caps; subsections 'A. Title' in italics."""
    if "." in num:
        p = P(f"{chr(64 + int(num.split('.')[1]))}. {text}", italic=True, align=WD_ALIGN_PARAGRAPH.LEFT, before=4, after=2)
    else:
        p = P(f"{ROMAN[int(num)]}. {text}" if num else text, caps=True, align=WD_ALIGN_PARAGRAPH.CENTER, before=8, after=3)
    p.paragraph_format.keep_with_next = True


def borders(table):
    tbl = table._tbl
    b = OxmlElement("w:tblBorders")
    for edge, sz in (("top", "8"), ("bottom", "8"), ("insideH", "2")):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single"); el.set(qn("w:sz"), sz); el.set(qn("w:color"), "000000")
        b.append(el)
    tbl.tblPr.append(b)


TABLES = iter(ROMAN[1:])


def T(title, head, rows, widths=None, numeric=()):
    """IEEE table: 'TABLE I' and the title in small caps above the table, 8 pt body."""
    P(f"Table {next(TABLES)}", caps=True, size=8, align=WD_ALIGN_PARAGRAPH.CENTER, before=6).paragraph_format.keep_with_next = True
    P(title, caps=True, size=8, align=WD_ALIGN_PARAGRAPH.CENTER, after=3).paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1 + len(rows), cols=len(head))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    borders(t)
    for r_i, tr in enumerate(t.rows):  # keep each table in one piece
        trPr = tr._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
        if r_i == 0:
            el = OxmlElement("w:tblHeader"); trPr.append(el)
    for r_i, row in enumerate([head] + rows):
        for c_i, val in enumerate(row):
            cell = t.cell(r_i, c_i)
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if c_i in numeric else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(str(val)); r.font.size = Pt(8); r.bold = r_i == 0; r.font.name = "Times New Roman"
            p.paragraph_format.keep_with_next = r_i < len(rows)
            if widths:
                cell.width = Inches(widths[c_i])
    P(after=4)


FIGS = iter(range(1, 20))


def F(path, caption, width=COL):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4); p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Inches(width))
    P(f"Fig. {next(FIGS)}.  {caption}", size=8, indent=False, after=6)


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
wk = uci["weekend"].set_index("Weekend")
p_weekend = chi2_contingency(pd.crosstab(uci["df"]["Weekend"], uci["df"]["Revenue"]))[1]
mcs, sh, rf = ga["multi_channel"]["shares"], ga["shares"], ga["referral_no_source"]
fl = ga["first_last"]
stay = {r: fl["values"][i][fl["cols"].index(r)] / sum(fl["values"][i]) for i, r in enumerate(fl["rows"]) if sum(fl["values"][i]) >= 100}
chan = {r["channel"]: r for r in ga["channels"]}
eg, er = (ev["generative"], ev["retrieval"]) if ev else ({}, {})

# ------------------------------------------------------------------ title (single column)
P("Who Gets Credit for the Sale? Recency Bias in Last-Click Attribution and the Case for Comparing "
  "Attribution Models", size=24, align=WD_ALIGN_PARAGRAPH.CENTER, after=12)
IT, CR = "Dept. of Information Technology", "Dept. of Computer Engineering (Regional Language)"
AUTHORS = [("Nishaad Gangal", IT, "nishaad.gangal23"), ("Om Katole", IT, "om.katole23"), ("Satyam Kumar", IT, "satyam.kumar23"),
           ("Akshat Jhanwar", IT, "akshat.jhanwar23"), ("Minal Shahakar", CR, "minal.shahakar")]
for group in (AUTHORS[:3], AUTHORS[3:]):  # IEEE author blocks, three per row
    blk = doc.add_table(rows=1, cols=len(group))
    blk.alignment = WD_TABLE_ALIGNMENT.CENTER
    for cell, (name, dept, mail) in zip(blk.rows[0].cells, group):
        cell.width = Inches(2.3)
        cell.text = ""
        for i, line in enumerate([name, dept, "Pimpri Chinchwad College of Engineering", "Pune, India", f"{mail}@pccoepune.org"]):
            p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(line); r.font.size = Pt(11 if i == 0 else 9); r.italic = 0 < i < 4; r.font.name = "Times New Roman"
    P(after=6)
P(after=10)
body = doc.add_section(WD_SECTION.CONTINUOUS)
columns(body, 2)

p = P(indent=False, after=6); add(p, "Abstract", bold=True, italic=True, size=9); add(p, "—", bold=True, size=9)
add(p, (f"Customers usually interact with several digital channels before buying, yet most businesses judge channels by "
        f"last-click reports. We study multi-channel attribution and conversion using four public datasets, a "
        f"known-answer simulation{' and an evaluation of an AI assistant' if ev else ''}. In {cr['impressions'] / 1e6:.1f} million Criteo "
        f"display impressions, only {pct(cr['attributed_share'])} of {cr['conversions']:,} conversions that followed a "
        f"Criteo click were credited to Criteo under the advertiser's last-click rule. Credit was driven by recency: it fell "
        f"from {pct(hours['<1h']['share'], 0)} when the purchase came within an hour of the click to "
        f"{pct(hours['7-31d']['share'], 0)} after 7 to 31 days (logistic odds ratio {rt['logit']['log_hours']['or']:.2f} per "
        f"unit of log hours), while additional clicks barely mattered (odds ratio {rt['logit']['clicks']['or']:.2f}). "
        f"In {ga['conversions']:,} real Google Analytics 360 journeys, {pct(ga['multi_session_share'], 0)} of buyers "
        f"returned over several sessions but only {pct(ga['multi_channel_share'], 0)} used more than one channel; within "
        f"those, first and last touch disagreed sharply (Direct {pct(mcs['Direct']['First touch'], 0)} against "
        f"{pct(mcs['Direct']['Last touch'], 0)} of the credit). In {uci['sessions']:,} e-commerce sessions, new visitors "
        f"converted at {pct(v.loc['New_Visitor', 'conversion_rate'])} against "
        f"{pct(v.loc['Returning_Visitor', 'conversion_rate'])} for returning visitors, and early-session behaviour predicted "
        f"purchase with ROC-AUC {mo['rf_auc']:.2f}. A simulation with known channel effects showed that no attribution model "
        f"is best everywhere: {nm(best_i['model'])} was most accurate when advertising acts immediately "
        f"({best_i['mae_pp']:.1f} percentage points mean error) and {nm(best_c['model'])} when it acts with carry-over "
        f"({best_c['mae_pp']:.1f} points), while first touch was worst in both. We release ChannelTrace, a free tool that "
        f"applies seven attribution models to a business's own Google Ads, Meta Ads or journey data"
        + (f". Its grounded assistant answered {eg['answerable_correct']} of {eg['answerable']} test questions correctly and "
           f"declined {eg['unanswerable_declined']} of {eg['unanswerable']} questions the data could not answer." if ev else
           " and explains the results through a grounded AI assistant.")), bold=True, size=9)
p = P(indent=False, after=8); add(p, "Index Terms", bold=True, italic=True, size=9); add(p, "—", bold=True, size=9)
add(p, "multi-touch attribution, last-click, customer journey, conversion prediction, Markov chain, Shapley value, "
       "retrieval-grounded assistant, digital marketing analytics", bold=True, size=9)

# ------------------------------------------------------------------ I introduction
H("1", "Introduction")
P("A typical online purchase is preceded by several touchpoints: a social media advertisement, a search, an email, a "
  f"direct return visit. The customer journey has replaced the linear purchase funnel as the way marketers describe "
  f"this process {c('court09', 'lemon16')}, and digital channels make each step of it measurable {c('kannan17')}. "
  "Attribution decides how much credit each channel receives for the resulting sale. Because budgets follow credit, the "
  "attribution rule shapes which channels are funded and which are cut.")
P("In practice most reports still use last-click attribution, which gives all credit to the final interaction. The rule "
  f"is simple but it distorts incentives, rewarding channels that appear late in the journey {c('berman18')}. Each "
  "advertising platform also reports from its own perspective, so several platforms can claim the same sale while "
  "channels that start journeys appear to contribute little. Google has retired the first-click, linear, time-decay and "
  f"position-based models from Google Ads, leaving last click and its own data-driven model {c('google')}, whose "
  "workings an advertiser cannot inspect. The gold standard, a randomised experiment, is expensive and statistically "
  f"demanding even for very large advertisers {c('lewis15', 'gordon19')}, and is out of reach for a small business.")
P(f"Data-driven alternatives have been proposed for over a decade {c('li14', 'shao11', 'anderl16', 'diemert17')}, but they "
  "are usually evaluated on proprietary data without ground truth, and they are rarely available to the small "
  "businesses, student teams and local marketers who most need simple, trustworthy guidance. This paper takes a "
  "practitioner's view of the problem and asks five research questions:")
for q in ["*RQ1:* what channel journeys precede a conversion?",
          "*RQ2:* how do converting and non-converting sessions differ?",
          "*RQ3:* does a channel's estimated importance change with the attribution model, and which model is most accurate?",
          "*RQ4:* which visitor and session characteristics are associated with conversion?",
          "*RQ5:* can these methods be packaged so that a small business obtains correct, usable insight from its own data?"]:
    pp = P(q, indent=False); pp.paragraph_format.left_indent = Inches(0.14)
P("Our contributions are: (i) evidence from 16.5 million real display impressions that last-click credit is governed "
  "mainly by recency; (ii) a cross-session analysis of real multi-channel journeys showing where attribution models "
  "disagree; (iii) a known-answer simulation showing that the most accurate attribution model depends on how "
  "advertising works, which argues for comparing models rather than choosing one; (iv) an analysis of session behaviour "
  "associated with purchase; and (v) ChannelTrace, an open, zero-cost tool that implements the methods for any "
  f"business's data, with {'an evaluated' if ev else 'a grounded'} assistant that explains the results in plain language.", before=2)
P("Section II reviews related work. Section III describes the data and Section IV the methods. Section V presents the "
  "ChannelTrace system and Section VI the results. Section VII discusses implications and threats to validity, "
  "Section VIII limitations and future work, and Section IX concludes.")

# ------------------------------------------------------------------ II related work
H("2", "Related Work")
H("2.1", "Customer Journeys and Multichannel Marketing")
P(f"Lemon and Verhoef {c('lemon16')} reviewed the customer journey as a sequence of pre-purchase, purchase and "
  f"post-purchase touchpoints, many of which the firm does not control. Kannan and Li {c('kannan17')} placed attribution "
  "within a broader research agenda for digital marketing and identified it as one of the field's open measurement "
  f"problems. Wiesel et al. {c('wiesel11')} linked online and offline marketing actions to funnel progression and profit, "
  f"and Kireyev et al. {c('kireyev16')} showed that display advertising raises later search activity, so a channel can "
  f"create value that is credited to another. De Haan et al. {c('dehaan16')} compared online advertising forms in a "
  "multiple-channel framework and found that last-click attribution undervalues content-integrated advertising.")
H("2.2", "Probabilistic and Data-Driven Attribution")
P(f"Shao and Li {c('shao11')} proposed learning channel contributions from converting and non-converting histories and "
  f"argued that a model should be judged on both accuracy and stability. Li and Kannan {c('li14')} modelled how customers "
  "consider and visit a firm's channels before converting, using individual-level data and a field experiment, and "
  "showed that channel contributions differ substantially from what last-click metrics suggest. Anderl et al. "
  f"{c('anderl16')} represented journeys as Markov chains and measured each channel by its removal effect, finding that "
  f"heuristic models misallocate credit. Xu et al. {c('xu14')} modelled ad exposures and conversions as mutually exciting "
  f"point processes, and Ji and Wang {c('ji17')} used survival analysis with additive hazards so that the influence of an "
  f"exposure decays over time. Berman {c('berman18')} analysed last-touch attribution theoretically and showed how it can "
  "distort advertisers' incentives and spending.")
H("2.3", "Game-Theoretic Attribution")
P(f"The Shapley value {c('shapley53')} divides a joint payoff among players by averaging each player's marginal "
  f"contribution over all coalitions. Dalessandro et al. {c('dalessandro12')} framed attribution causally and connected it "
  f"to the Shapley value, and Zhao et al. {c('zhao18')} developed simplified Shapley methods for online advertising. "
  f"Singal et al. {c('singal22')} built an axiomatic framework for attribution, showed how common heuristics fail its "
  "axioms, and proposed a counterfactual adjusted Shapley value. The same idea underlies SHAP explanations of machine "
  f"learning models {c('lundberg17')}.")
H("2.4", "Deep Learning Attribution")
P(f"Recent work learns attribution from sequences with neural networks. Li et al. {c('li18')} used attention over "
  f"touchpoints with user controls; Ren et al. {c('ren18')} proposed a dual-attention recurrent network that combines "
  f"post-view and post-click effects; Du et al. {c('du19')} used a recurrent network with counterfactual reasoning to "
  f"estimate incremental contributions; and Kumar et al. {c('kumar20')} added a causal correction for selection bias in "
  f"channel exposure. Several of these models are evaluated on the Criteo attribution dataset {c('diemert17')}, which we "
  "also use. Their accuracy is measured by conversion prediction, which does not directly test whether the credit is "
  "correct.")
H("2.5", "Experiments and Incrementality")
P(f"Field experiments measure what attribution can only approximate. Blake et al. {c('blake15')} found that eBay's "
  f"brand-keyword search advertising produced little incremental revenue, Johnson et al. {c('johnson17')} introduced "
  f"\"ghost ads\" to make experiments cheaper, and Gordon et al. {c('gordon19')} showed in large Facebook experiments that "
  f"observational methods often fail to recover experimental lift. Lewis and Rao {c('lewis15')} explained why even large "
  "experiments struggle to measure returns precisely. These results motivate a known-answer test of attribution models "
  "when experiments are not available.")
H("2.6", "Clickstream Conversion Prediction")
P(f"Moe and Fader {c('moe04')} modelled how conversion probability evolves over repeated store visits, Montgomery et al. "
  f"{c('montgomery04')} predicted purchase from page-to-page browsing paths, and Bucklin and Sismeiro {c('bucklin09')} "
  f"reviewed clickstream analysis in marketing. Sakar et al. {c('sakar19')} predicted purchasing intention from session "
  "data and released the UCI Online Shoppers dataset used here.")
H("2.7", "Research Gap")
T("Representative Attribution Studies Compared With This Work",
  ["Study", "Data", "Method", "Known truth"],
  [[f"Shao and Li {c('shao11')}", "Advertiser campaign logs", "Bagged logistic, probabilistic", "No"],
   [f"Li and Kannan {c('li14')}", "Hospitality firm journeys", "Bayesian channel model", "Field experiment"],
   [f"Anderl et al. {c('anderl16')}", "Four online businesses", "Markov chain", "No"],
   [f"Ren et al. {c('ren18')}", "Criteo and a second ad dataset", "Dual-attention RNN", "No"],
   [f"Kumar et al. {c('kumar20')}", "Criteo", "Causal attention RNN", "No"],
   [f"Gordon et al. {c('gordon19')}", "15 Facebook experiments", "Experiment vs. observational", "Experiment"],
   ["This work", "Four public datasets", "Seven models compared, open tool", "Simulation"]],
  widths=[0.85, 0.95, 0.95, 0.75])
P("Table I shows the gap this work addresses. Most studies rely on proprietary data, evaluate a single proposed model "
  "and offer nothing a practitioner can run. We combine public data with a simulation in which the true contribution of "
  "each channel is known, compare models rather than champion one, and package the methods in a free tool whose "
  + ("assistant is itself evaluated." if ev else "assistant explains the results."))

# ------------------------------------------------------------------ III data
H("3", "Data")
P("Each dataset is used only for the questions it can support; the datasets come from different populations and are "
  "never pooled (Table II).")
T("Datasets and Their Role",
  ["Dataset", "Content", "Used for"],
  [[f"UCI Online Shoppers {c('sakar19')}", f"{uci['sessions']:,} sessions (after removing 125 duplicates), 17 features, purchase outcome", "RQ2, RQ4"],
   [f"Criteo Attribution {c('diemert17')}", f"{cr['impressions']:,} impressions, {cr['users']:,} users, {cr['campaigns']} campaigns, 30 days", "RQ3 (last-click gap, recency)"],
   [f"Google Analytics 360 sample {c('ga360')}", f"{ga['sessions']:,} sessions, {ga['visitors']:,} visitors, named channels, 12 months", "RQ1, RQ3"],
   [f"Facebook Ad Campaign {c('kaggle')}", "1,143 real ads, spend, clicks, conversions, age, gender", "RQ5 (tool validation)"],
   ["Simulated journeys", "6 random worlds x 2 scenarios x 3,000 users with known channel effects", "RQ3 (model accuracy)"],
   *([["Assistant test set", f"{ev['n']} questions with known answers", "RQ5 (assistant accuracy)"]] if ev else [])],
  widths=[1.0, 1.65, 0.85])
P("*UCI Online Shoppers.* Each row is one session on an online store over a year, with counts of and time on "
  "administrative, informational and product pages, bounce and exit rates, Google Analytics page value, the month, "
  "visitor type, weekend flag, anonymised traffic source and whether the session ended in a purchase. We removed 125 "
  "exact duplicate rows.")
P(f"*Criteo Attribution.* Each row is a display impression with a user, campaign, timestamp, click flag and, for "
  f"converting users, the conversion time and a flag for whether the advertiser's last-click rule credited the "
  f"conversion to Criteo. We grouped impressions into journeys ending at each conversion. A validity check shaped the "
  f"design: {pct(cr['single_campaign_share'])} of conversions involve a single campaign, and all impressions in converting "
  f"journeys are clicks because the public sample retains clicked impressions for converting users. Criteo therefore "
  f"cannot compare channels or campaigns within a journey, nor clicked against viewed impressions; we use it for the "
  f"last-click gap and its recency effect.")
d0, d1 = (pd.to_datetime(s.strip()).strftime("%B %Y") for s in ga["period"].split("to"))
P(f"*Google Analytics 360.* The public BigQuery sample covers the Google Merchandise Store from {d0} to {d1}. Each row is a session with a persistent visitor "
  "identifier, start time, Google's default channel grouping and the number of transactions. A journey is a visitor's "
  "sessions in time order up to and including the first session with a transaction; journeys without a purchase run to "
  "the visitor's last session. Converting journeys were downloaded individually; non-converting journeys were aggregated "
  "by channel path inside BigQuery, which is all the Markov model needs and keeps memory low.")
P("*Facebook Ad Campaign.* A public export of 1,143 ads with spend, impressions, clicks, total and approved "
  "conversions and the targeted age and gender. It serves as a realistic file for testing the tool. *Simulated "
  "journeys* and the *assistant test set* are described in Section IV.")

# ------------------------------------------------------------------ IV methods
H("4", "Methods")
H("4.1", "Notation and Rule-Based Models")
P(r"A converting journey is a sequence of touchpoints $(c_1,t_1),\dots,(c_n,t_n)$, where $c_i$ is a channel, $t_i$ a "
  r"time and the purchase happens at time $T$ after the last touch. An attribution model assigns each touch a weight "
  r"$w_i$ with $\sum_i w_i=1$, and the credit of channel $k$ is the sum of the weights of its touches over all "
  r"converting journeys:")
E(r"A(k)=\sum_{\text{journeys}}\sum_{i:\,c_i=k}w_i")
P(r"First touch sets $w_1=1$, last touch sets $w_n=1$ and linear sets $w_i=1/n$. Time decay halves a touch's weight for "
  r"every $h=7$ days between it and the purchase:")
E(r"w_i=\frac{2^{-(T-t_i)/h}}{\sum_j 2^{-(T-t_j)/h}}")
P(r"Position based gives 40% each to the first and last touch and shares the remaining 20% equally among the touches "
  r"in between (half each when $n=2$, all of it when $n=1$).")
H("4.2", "Markov Chain Removal Effect")
P(f"Following Anderl et al. {c('anderl16')}, all journeys, converting and not, are treated as paths through the states "
  r"start, the channels, conversion and null. The transition probability from state $a$ to state $b$ is estimated from "
  r"the transition counts $N$:")
E(r"p(a,b)=\frac{N(a,b)}{\sum_{b'}N(a,b')}")
P(r"Conversion and null are absorbing states. Splitting the transition matrix into its transient part $Q$ and absorbing "
  r"part $R$, the absorption probabilities are $B=(I-Q)^{-1}R$ " + c("norris97") + r", and $P(\text{conv})$ is the entry "
  r"of $B$ for start and conversion. Removing channel $k$ redirects every transition into $k$ to the null state. Its "
  r"removal effect and credit are")
E(r"RE(k)=1-\frac{P_{-k}(\text{conv})}{P(\text{conv})}")
E(r"A(k)=C\cdot\frac{RE(k)}{\sum_j RE(j)}")
P(r"where $C$ is the number of conversions. For GA360, aggregated non-converting paths enter the count matrix with a "
  r"weight equal to the number of journeys they represent; we verified that this gives results identical to the "
  r"unweighted computation.")
H("4.3", "Shapley Value")
P(r"Let $K$ be the set of channels and $v(S)$ the number of converting journeys whose channels all lie in the coalition "
  r"$S\subseteq K$. The Shapley value " + c("shapley53") + r" of channel $k$ is")
E(r"\phi(k)=\sum_{S\subseteq K\setminus\{k\}}\frac{|S|!\,(|K|-|S|-1)!}{|K|!}\left[v(S\cup\{k\})-v(S)\right]")
P(r"By the efficiency property $\sum_k\phi(k)=v(K)=C$, so, like the other models, it distributes exactly the observed "
  r"conversions. Exact computation is exponential in $|K|$ and the implementation is limited to 12 channels, which "
  r"covers every dataset here. Table III summarises the seven models.")
T("Attribution Models Compared", ["Model", "Credit rule", "Uses non-buyers", "Implicit assumption"],
  [["First touch", "All to first touch", "No", "Discovery drives sales"],
   ["Last touch", "All to last touch", "No", "Closing drives sales"],
   ["Linear", "1/n to each touch", "No", "All touches equal"],
   ["Time decay", "Halves every 7 days", "No", "Recent touches matter more"],
   ["Position based", "40/20/40", "No", "Opening and closing matter"],
   ["Markov chain", "Removal effect (4)-(5)", "Yes", "Next step depends on current channel"],
   ["Shapley value", "Marginal contribution (6)", "No", "Channels cooperate as a coalition"]],
  widths=[0.75, 0.95, 0.55, 1.25])
H("4.4", "Known-Answer Validation")
P("Observational data offers no ground truth for attribution, so we simulated journeys in which channel effects are set "
  r"by design. In each random world, seven channels receive a lift $\lambda_k$ drawn uniformly from $[0.01,0.25]$, and "
  r"the first channel and each subsequent channel are drawn from Dirichlet(2) distributions. A user makes up to eight "
  r"visits; after visit $m$ without a purchase the user leaves with probability 0.35, otherwise returns after an "
  r"exponential gap with a mean of 60 hours. The purchase probability at visit $m$ is")
E(r"P(\text{buy at }m)=\kappa_m\,\sigma\left(-3+6\sum_{j\in J(m)}\lambda_{c_j}\right)")
P(r"where $\sigma$ is the logistic function, $\kappa_1=0.25$ and $\kappa_m=0.45$ for later visits. In the *immediate* "
  r"scenario $J(m)$ includes visit $m$, so a touch can trigger a purchase in the same visit; in the *carry-over* scenario "
  r"$J(m)$ includes only earlier visits, as with awareness advertising. A channel's true contribution is the number of "
  r"conversions lost when its lift is switched off, computed with the same random numbers so that only that channel's "
  r"effect changes. Its true share $s_k$ is that loss divided by the sum of losses over all channels. Each model's credit "
  r"shares $\hat{a}_k$ are scored by")
E(r"\text{MAE}=\frac{1}{|K|}\sum_k\left|\hat{a}_k-s_k\right|")
P(f"in percentage points, and by Spearman rank correlation {c('spearman04')} with the true shares. Six worlds of 3,000 "
  f"users were generated per scenario. Stability was assessed with 200 bootstrap resamples of journeys {c('efron93')} on "
  "a separate synthetic dataset in which Social and Display were designed to start journeys and Email and Paid Search "
  "to close them.")
H("4.5", "Recency of Last-Click Credit")
P(r"For each Criteo conversion $i$ we record whether Criteo received last-click credit ($y_i=1$), the number of Criteo "
  r"clicks $n_i$ (capped at 10) and the hours $h_i$ from the last click to the conversion. We test association with Pearson's chi-square test "
  + c("pearson1900") + " over six time bands and with the logistic regression")
E(r"\mathrm{logit}\,P(y_i=1)=\beta_0+\beta_1\log(1+h_i)+\beta_2 n_i")
H("4.6", "Session Behaviour and Conversion")
P(f"Converting and non-converting UCI sessions are compared with two-sided Mann-Whitney U tests {c('mann47')} for "
  f"numeric measures and chi-square tests for visitor type, month and weekend. Logistic regression, random forest "
  f"{c('breiman01')} and gradient boosting {c('friedman01')} classifiers, implemented in scikit-learn {c('pedregosa11')}, "
  f"are trained on a stratified 75/25 split with class-balanced weights and evaluated by ROC-AUC {c('fawcett06')}. Because "
  "the PageValues feature is computed from pages viewed before a transaction and partly encodes the outcome, every "
  "model is reported with and without it. Feature importance is measured by permutation on the test set.")
if ev:
    H("4.7", "Assistant Evaluation")
    P(f"The assistant was tested on a fixed set of {ev['n']} questions written before the run: {eg['answerable']} whose answers "
      f"are stated in the fact sheet and {eg['unanswerable']} that the data cannot answer, such as television return on "
      "investment or next month's sales. Each question was asked once, without conversation history, to both answer paths "
      "the site uses. An answerable question is scored correct when the reply contains every expected fact (allowing "
      "alternative spellings, such as 54% for 54.2%); an unanswerable question is correct when the reply declines and states "
      "no figure. Every number in every reply was also checked against the fact sheet, and numbers found nowhere in it were "
      "counted as unsupported, a direct measure of invented figures. All replies were saved and the automatic scores "
      "reviewed by hand.")

# ------------------------------------------------------------------ V system
H("5", "The ChannelTrace System")
F(FIG / "architecture.png", "ChannelTrace architecture. Everything inside the dashed box runs in the user's browser; only the aggregated fact sheet reaches the assistant.")
P("ChannelTrace is a web application written in TypeScript with React and hosted on Vercel at no cost (Fig. 1). Its "
  "analysis runs entirely in the user's browser, so uploaded files are never sent to a server. An ad-performance module "
  "detects Google Ads, Meta Ads Manager and similar exports, maps their columns, computes click-through rate, cost per "
  "click, conversion rate, cost per acquisition (CPA) and return on ad spend, gives each campaign a verdict relative to "
  "the account average (scale candidate, on track, expensive, no conversions), measures spend with no return and breaks "
  "results down by audience and day. A journey module applies all seven attribution models and shows where last click "
  "over- or under-credits each channel. The browser implementation of the models was checked against the Python "
  "reference used for the research.")
P("Results are condensed into a fact sheet: short, labelled statements of computed figures, with suggested actions and "
  "caveats. The assistant answers questions only from this sheet, a form of retrieval grounding that reduces invented "
  f"content {c('lewis20', 'ji23')}. When the site has a key configured, an edge function sends the sheet and the "
  "question to a free generative model; because free model versions are retired and often overloaded, it tries several "
  "in turn within a fixed time budget. Otherwise a built-in model scores fact-sheet statements against the question with "
  f"TF-IDF weighting {c('salton88')} and quotes the most relevant ones, so the assistant works offline and can only "
  "repeat computed numbers.")

# ------------------------------------------------------------------ VI results
H("6", "Results")
H("6.1", "Last-Click Credit Is Driven by Recency (RQ3)")
P(f"All {cr['conversions']:,} Criteo conversions followed at least one Criteo click, yet only {pct(cr['attributed_share'])} "
  f"were credited to Criteo by the advertiser's last-click rule; the remainder were claimed by other channels. Converting "
  f"journeys were short (mean {cr['touches_mean']:.2f} clicks; {pct(cr['single_touch_share'], 0)} with one click; median "
  f"{cr['hours_last_to_conv_median']:.1f} hours from the last click to purchase; median {cr['span_days_median_multi']:.1f} "
  f"days from first to last click in multi-click journeys). Fig. 2 shows that credit falls steadily with time since the "
  f"last click (chi-square = {rt['chi2']:,.0f}, df = {rt['dof']}, p < 0.001).")
F(FIG / "recency.png", "Share of conversions credited to Criteo under last click, by time from the last Criteo click to the conversion (number of conversions in brackets).")
by_t = cr["attributed_by_touches"]
T("Logistic Regression of Last-Click Credit to Criteo (n = %s)" % f"{rt['n']:,}",
  ["Predictor", "Odds ratio", "95% CI", "p"],
  [["log(1 + hours since click)", f"{rt['logit']['log_hours']['or']:.3f}", "%.3f to %.3f" % tuple(rt["logit"]["log_hours"]["ci_or"]), "< 0.001"],
   ["Criteo clicks (capped at 10)", f"{rt['logit']['clicks']['or']:.3f}", "%.3f to %.3f" % tuple(rt["logit"]["clicks"]["ci_or"]), "< 0.001"]],
  widths=[1.4, 0.6, 0.95, 0.55], numeric=(1, 2, 3))
P(f"Holding clicks constant, each unit increase in log(1 + hours) multiplies the odds of Criteo receiving credit by "
  f"{rt['logit']['log_hours']['or']:.2f}, whereas each additional click multiplies them by only "
  f"{rt['logit']['clicks']['or']:.2f} (pseudo R-squared {rt['pseudo_r2']:.2f}; Table IV). Table V confirms this "
  "directly: the credit share hardly moves with the number of clicks.")
T("Last-Click Credit to Criteo by Number of Criteo Clicks", ["Clicks in journey", "Conversions", "Credited to Criteo"],
  [[k if k != "6" else "6 or more", f"{by_t[k]['n']:,}", pct(by_t[k]["share"])] for k in by_t],
  widths=[1.1, 1.0, 1.1], numeric=(1, 2))
P("Under last click, which platform is paid for a sale depends far more on timing than on how much a channel was used. "
  "A customer who clicks a display ad and buys an hour later almost always credits it; one who buys a week later, "
  "after a search or an email, usually does not.")

H("6.2", "Real Multi-Channel Journeys (RQ1, RQ3)")
P(f"The Google Analytics 360 sample covers {ga['visitors']:,} visitors and {ga['sessions']:,} sessions. Following each "
  f"visitor across sessions up to the first purchase gives {ga['conversions']:,} converting journeys "
  f"({pct(ga['conv_rate'])} of all journeys). Buying took repeated visits: {pct(ga['multi_session_share'], 0)} of "
  f"converting journeys spanned more than one session (mean {ga['sessions_mean']:.2f} sessions, maximum "
  f"{ga['sessions_max']}, against {ga['nonconv_sessions_mean']:.2f} for journeys without a purchase), and multi-session "
  f"buyers took a median of {ga['days_first_to_purchase_median_multi']:.1f} days from first visit to purchase. Yet only "
  f"{pct(ga['multi_channel_share'], 0)} of converting journeys involved more than one channel. The most common converting "
  f"paths were a single {ga['top_paths'][0][0]} session ({ga['top_paths'][0][1]:,}), a single {ga['top_paths'][1][0]} "
  f"session ({ga['top_paths'][1][1]:,}) and {ga['top_paths'][3][0]} ({ga['top_paths'][3][1]:,}).")
T("Sessions and Converting Sessions by Channel (GA360)", ["Channel", "Sessions", "Converting", "Rate"],
  [[ch["channel"], f"{ch['sessions']:,}", f"{ch['converting']:,}", pct(ch["rate"], 2)]
   for ch in sorted(ga["channels"], key=lambda r: -r["rate"]) if ch["sessions"] >= 1000],
  widths=[1.1, 0.8, 0.8, 0.7], numeric=(1, 2, 3))
P(f"Channels differ widely in how often a session ends in a purchase (Table VI). Referral sessions converted at "
  f"{pct(chan['Referral']['rate'], 1)}, while Social, the second-largest source of traffic with "
  f"{chan['Social']['sessions']:,} sessions, converted at {pct(chan['Social']['rate'], 2)}. Organic Search brought the "
  f"most sessions but converted at {pct(chan['Organic Search']['rate'], 1)}.")
T("Credit Share by Channel, All Converting Journeys (GA360)", ["Channel", "First", "Last", "Linear", "Markov", "Shapley"],
  [[ch, *[pct(sh[ch][mm]) for mm in ("First touch", "Last touch", "Linear", "Markov chain", "Shapley value")]]
   for ch in sorted(sh, key=lambda ch: -sh[ch]["Linear"]) if sh[ch]["Linear"] > 0.0005],
  widths=[0.92, 0.48, 0.48, 0.48, 0.56, 0.58], numeric=(1, 2, 3, 4, 5))
swing = max(sh, key=lambda ch: max(sh[ch].values()) - min(sh[ch].values()))
P(f"Because so few journeys mix channels, the seven models broadly agree on the whole sample (Table VII); the largest "
  f"swing, for {swing}, is from {pct(min(sh[swing].values()))} to {pct(max(sh[swing].values()))}. The disagreement is "
  f"concentrated in the {ga['multi_channel']['journeys']:,} multi-channel journeys (Fig. 3). There, first touch gives "
  f"Direct {pct(mcs['Direct']['First touch'], 0)} of the credit and last touch {pct(mcs['Direct']['Last touch'], 0)}, "
  f"while Referral moves from {pct(mcs['Referral']['First touch'], 0)} to {pct(mcs['Referral']['Last touch'], 0)}; the "
  f"most common multi-channel paths were {ga['multi_channel']['top_paths'][0][0]} "
  f"({ga['multi_channel']['top_paths'][0][1]}) and {ga['multi_channel']['top_paths'][1][0]} "
  f"({ga['multi_channel']['top_paths'][1][1]}). For these customers the choice of model decides which channel is funded.")
F(FIG / "ga360.png", f"Credit share by channel within the {ga['multi_channel']['journeys']:,} GA360 converting journeys that used more than one channel.")
order = sorted(stay, key=lambda ch: stay[ch])  # most likely to hand the journey on first
P("Channels also differ in whether they hand journeys on. The share of converting journeys that ended in a different "
  "channel from the one they began with was " + ", ".join(f"{ch} {pct(1 - stay[ch], 0)}" for ch in order[:-1])
  + f" and {order[-1]} {pct(1 - stay[order[-1]], 0)} (channels starting at least 100 journeys). Journeys that start "
  f"with {order[0]}, {order[1]} or {order[2]} are the ones most often closed by another channel, which is exactly where "
  "last click moves credit away from the channel that started them; a referral, by contrast, almost never hands on.")
P(f"Two properties of the data qualify these figures. Google Analytics labels a returning direct visit with the source "
  f"of the visitor's previous campaign: {rf['true_direct_sessions']:,} of the {rf['sessions']:,} Referral sessions are "
  f"flagged in the data as direct visits. Direct can therefore rarely follow another channel, which mechanically lowers "
  f"its last-touch share. And {pct(rf['converting_share'], 0)} of converting Referral sessions record no referring site, "
  f"so Referral's large share cannot be read as the value of third-party sites.")

H("6.3", "No Attribution Model Is Best Everywhere (RQ3)")
F(FIG / "simulation.png", "Mean absolute error between model and true credit shares (percentage points; bars show the standard deviation over six worlds).")
T("Accuracy of Attribution Models Against Known Channel Effects",
  ["Model", "Immediate MAE", "ρ", "Carry-over MAE", "ρ"],
  [[mm, f"{si[mm]['mae_pp']:.1f}", f"{si[mm]['spearman']:.2f}", f"{sc[mm]['mae_pp']:.1f}", f"{sc[mm]['spearman']:.2f}"] for mm in models],
  widths=[1.0, 0.75, 0.4, 0.85, 0.4], numeric=(1, 2, 3, 4))
P(f"When advertising acts immediately, {nm(best_i['model'])} came closest to the truth "
  f"({best_i['mae_pp']:.1f} pp), with time decay close behind ({si['Time decay']['mae_pp']:.1f} pp). With carry-over "
  f"effects, last-touch error rose to {sc['Last touch']['mae_pp']:.1f} pp and its rank agreement fell from "
  f"{si['Last touch']['spearman']:.2f} to {sc['Last touch']['spearman']:.2f}, while time decay and linear became the "
  f"most accurate ({sc['Time decay']['mae_pp']:.1f} and {sc['Linear']['mae_pp']:.1f} pp; Fig. 4, Table VIII). The highest "
  f"rank agreement came from {nm(max(si.values(), key=lambda r: r['spearman'])['model'])} under immediate effects "
  f"({max(r['spearman'] for r in si.values()):.2f}) and {nm(max(sc.values(), key=lambda r: r['spearman'])['model'])} "
  f"under carry-over ({max(r['spearman'] for r in sc.values()):.2f}), with the Shapley value close behind in both "
  f"({si['Shapley value']['spearman']:.2f} and {sc['Shapley value']['spearman']:.2f}). First touch was worst in both. The "
  f"Markov removal effect was never the most accurate under these data-generating processes, a reminder that "
  f"data-driven does not automatically mean correct.")
P("The pattern has a simple explanation. Under immediate effects the touch that triggers a purchase is usually the last "
  "one, so last touch is nearly right. Under carry-over the decisive touches come earlier and the purchase happens on a "
  "later visit, possibly through a weak channel, so any rule that concentrates credit at one end of the journey errs, "
  "and rules that spread credit do better.")
F(FIG / "bootstrap.png", "Last-touch and Markov credit shares with 95% bootstrap intervals on 4,000 synthetic journeys with designed channel roles.")
P("On the separate synthetic dataset in which Social and Display were designed to start journeys and Email and Paid "
  "Search to close them, the data-driven models recovered those roles (Fig. 5): last touch gave Display "
  f"{pct(boot['Last touch']['Display'][0], 0)} of the credit against {pct(boot['Markov chain']['Display'][0], 0)} under "
  f"Markov, and Email {pct(boot['Last touch']['Email'][0], 0)} against {pct(boot['Markov chain']['Email'][0], 0)}. The "
  f"bootstrap intervals are narrow (about plus or minus one percentage point), so these differences are not sampling noise.")

H("6.4", "Session Behaviour Associated With Purchase (RQ2, RQ4)")
P(f"The overall conversion rate was {pct(uci['conversion_rate'])}. New visitors converted at "
  f"{pct(v.loc['New_Visitor', 'conversion_rate'])} against {pct(v.loc['Returning_Visitor', 'conversion_rate'])} for "
  f"returning visitors, who made up {pct(ret_share, 0)} of sessions (chi-square p < 0.001). Conversion peaked in "
  f"{peak_m['Month']} ({pct(peak_m['conversion_rate'])}) and was lowest in {low_m['Month']} "
  f"({pct(low_m['conversion_rate'])}; Fig. 6). Weekend sessions converted at {pct(wk.loc[True, 'conversion_rate'])} against "
  f"{pct(wk.loc[False, 'conversion_rate'])} on weekdays (chi-square p = {p_weekend:.3f}), a small but significant difference.")
F(FIG / "month.png", "Conversion rate by month in the UCI Online Shoppers data (January and April are absent).")
rows = []
for b in ["Product pages viewed", "Time on product pages (s)", "Account/admin pages viewed", "Bounce rate", "Exit rate", "Page value"]:
    f = (lambda x: f"{x / 60:.1f} min") if "(s)" in b else ((lambda x: f"{x:.3f}") if "rate" in b else (lambda x: f"{x:.1f}"))
    pv = g.loc[b, "p-value"]
    rows.append([b.replace(" (s)", ""), f(g.loc[b, "Mean (converted)"]), f(g.loc[b, "Mean (not converted)"]),
                 "< 1e-300" if pv == 0 else f"{pv:.1e}"])
T("Session Behaviour of Buyers and Non-Buyers (Means; Mann-Whitney U)", ["Measure", "Buyers", "Non-buyers", "p"],
  rows, widths=[1.45, 0.65, 0.7, 0.65], numeric=(1, 2, 3))
T("Purchase Prediction (ROC-AUC on Held-Out 25%)", ["Model", "With PageValues", "Without PageValues"],
  [["Logistic regression", f"{mw['logit_auc']:.3f}", f"{mo['logit_auc']:.3f}"],
   ["Random forest", f"{mw['rf_auc']:.3f}", f"{mo['rf_auc']:.3f}"],
   ["Gradient boosting", f"{mw['hgb_auc']:.3f}", f"{mo['hgb_auc']:.3f}"]], widths=[1.4, 1.0, 1.05], numeric=(1, 2))
imp = mo["importance"].head(5)
P(f"All ten behavioural measures differed significantly. Buyers viewed a median of "
  f"{g.loc['Product pages viewed', 'Median (converted)']:.0f} product pages against "
  f"{g.loc['Product pages viewed', 'Median (not converted)']:.0f} and bounced and exited far less (Table IX). With "
  f"PageValues the best model reached ROC-AUC {mw['rf_auc']:.3f}; without it, {mo['rf_auc']:.3f}, which is the honest "
  f"estimate of what early-session behaviour reveals (Table X). The strongest signals without PageValues, by "
  f"permutation importance (drop in AUC), were "
  + "; ".join(f"{r.feature.replace(' (s)', '').lower().replace('month: nov', 'a November visit')} ({r.importance:.3f})" for r in imp.itertuples())
  + ". Time spent on product pages carries more information than the number of pages viewed.")

H("6.5", "Tool Validation on Real Advertising Data (RQ5)")
P("ChannelTrace was run on the real Facebook Ad Campaign data. It recognised the export format automatically and "
  "reproduced the campaign totals computed independently in Python to the cent (spend 58,705.23; cost per acquisition "
  "54.41). It found that 10.0% of spend went to ad sets with no approved conversions, that the 30-34 age group had the "
  "lowest cost per acquisition (30.88 against 99.76 for ages 45-49), and that men converted more cheaply than women "
  "(41.44 against 69.70). The browser implementation of all seven attribution models matched the Python reference "
  "exactly on the synthetic journeys.")

if ev:
    H("6.6", "Assistant Accuracy (RQ5)")
    T("Assistant Accuracy on the Fixed Question Set", ["Measure", "Generative", "Built-in"],
      [["Answerable, correct", f"{eg['answerable_correct']} / {eg['answerable']}", f"{er['answerable_correct']} / {er['answerable']}"],
       ["Unanswerable, declined", f"{eg['unanswerable_declined']} / {eg['unanswerable']}", f"{er['unanswerable_declined']} / {er['unanswerable']}"],
       ["Overall accuracy", pct(eg["overall"], 0), pct(er["overall"], 0)],
       ["Replies with unsupported numbers", f"{eg['replies_with_unsupported_numbers']} / {ev['n']}", f"{er['replies_with_unsupported_numbers']} / {ev['n']}"]],
      widths=[1.6, 0.85, 0.85], numeric=(1, 2))
    miss = [r["question"] for r in ev["rows"] if r["answerable"] and not r["generative"]["correct"]]
    P(f"The generative path answered {eg['answerable_correct']} of {eg['answerable']} answerable questions correctly and "
      f"declined {eg['unanswerable_declined']} of {eg['unanswerable']} questions outside the data (Table XI), for example "
      "explaining that the fact sheet has no television, influencer or device-level figures and suggesting what data would "
      f"answer the question. {eg['replies_with_unsupported_numbers'] or 'None'} of its {ev['n']} replies contained a number "
      "absent from the fact sheet"
      + (". " if not miss else f"; its misses were {', '.join(chr(8220) + q + chr(8221) for q in miss)}. ")
      + f"The built-in retrieval model answered {er['answerable_correct']} of {er['answerable']} correctly. Because it can "
      "only quote computed statements it never invents a figure, but it recognised only "
      f"{er['unanswerable_declined']} of {er['unanswerable']} unanswerable questions; for the others it returned the "
      "closest related facts, which a reader could mistake for an answer. The two paths are therefore complementary: the "
      "generative model is better at saying what the data cannot show, and the retrieval model guarantees that every "
      f"number shown is computed. The test used the free model tier as deployed on {ev['date']} "
      f"({', '.join(ev['models_used'])}).")

# ------------------------------------------------------------------ VII discussion
H("7", "Discussion")
H("7.1", "Implications for Practitioners")
P("The Criteo results show concretely why platforms disagree about who made a sale. A display network whose clicks "
  "precede every one of these conversions is credited for barely half of them, and its share depends mainly on how "
  "long the customer waited before buying. A business that reads last-click reports at face value will therefore "
  "undervalue channels whose influence is delayed, such as awareness advertising, and overvalue whichever channel "
  f"happens to be last, consistent with the incentive problems described by Berman {c('berman18')} and the search "
  f"spill-overs found by Kireyev et al. {c('kireyev16')}.")
P("The simulation explains why the remedy is not simply to switch to a single data-driven model. Model accuracy "
  "depended on how advertising works: last touch was competitive when effects were immediate but degraded sharply with "
  "carry-over, while linear, time decay and the Shapley value were more robust. Since a business rarely knows its true "
  "mechanism, comparing several models, and treating channels whose credit swings strongly between them as uncertain, "
  "is the safer practice. ChannelTrace is built around that comparison.")
P("The GA360 journeys add a practical nuance. For most of this store's customers the attribution model hardly "
  "matters, because they return through the same channel; it matters a great deal for the minority who move between "
  "channels, typically arriving directly or through search and buying later through a referral link. A business can "
  "check this cheaply: if few of its converting journeys mix channels, last-click reports are roughly adequate; if "
  "many do, the models must be compared before budgets are moved.")
P("For marketers the session results suggest three practical actions: re-engage returning visitors, who are most of "
  "the traffic but convert least; concentrate budget before the seasonal peak; and send paid traffic directly to product "
  "pages, where time spent is the strongest early signal of purchase intent. These are suggestions to test, not "
  f"proven effects; where budgets allow, a holdout experiment {c('johnson17', 'gordon19')} is the way to confirm them.")
H("7.2", "Implications for Research")
P("Attribution models are usually compared by how well they predict conversion. Our simulation shows that a model can "
  "rank well on that criterion and still distribute credit wrongly, because prediction and credit are different "
  "targets. Known-answer simulations, though stylised, give a direct test of credit and are cheap to extend to new "
  "mechanisms, and we encourage their use alongside experimental benchmarks. Public journey data with named channels "
  "remains scarce; the GA360 sample is one of the few sources and shows how strongly a platform's own channel "
  "definitions shape the result.")
H("7.3", "Threats to Validity")
P("*Construct validity.* Credit is not causal contribution: every model here, including the data-driven ones, assigns "
  "observed conversions and none measures what would have happened without a channel. The simulation's true shares are "
  "causal by construction, which is why it is used to judge the models. *Internal validity.* The Criteo credit flag is "
  "the advertiser's own last-click decision and the other channels are not observed, so the recency effect describes "
  "how credit was assigned, not why. GA360 journeys depend on a cookie-based visitor identifier and on Google's channel "
  "rules, including the relabelling of direct visits. *External validity.* Each dataset represents one store, network "
  "or advertiser, mostly from mature markets; results for Indian small businesses may differ and should be checked on "
  "their own data, which the tool allows. *Statistical conclusion validity.* With hundreds of thousands of "
  "observations almost any difference is significant, so we report effect sizes (credit shares, odds ratios, AUC and "
  "error in percentage points) alongside p-values.")
H("7.4", "Ethics and Privacy")
P("All datasets are public and anonymised, and no personal data was collected. ChannelTrace processes uploaded files "
  "in the browser and sends only the aggregated fact sheet, never raw rows, to the generative model. The assistant is "
  "instructed to label recommendations as suggestions and to state that the data shows associations, not proof of "
  "cause, so that users are not led to over-trust its advice.")

# ------------------------------------------------------------------ VIII limitations
H("8", "Limitations and Future Work")
P("All findings are associations. The Criteo sample covers one channel and retains only clicked impressions for "
  "converting users, so view-through effects cannot be studied. The UCI traffic sources are anonymised. The simulation "
  "uses two stylised mechanisms and six worlds each; other mechanisms, such as diminishing returns or interactions "
  "between channels, may favour other models. The GA360 sample is one store, uses Google Analytics' own channel "
  "definitions and splits journeys across devices. "
  + ("The assistant test uses a single run of a fixed question set written by the authors, and the free generative "
     "models behind it change over time." if ev else "The accuracy of the assistant has not yet been measured."))
P(f"Future work has {'four' if ev else 'five'} parts: {'' if ev else 'an accuracy test of the assistant on a fixed question set with known answers; '}a usability study of the tool with small-business users using the System Usability "
  f"Scale {c('brooke96')}; a business-intelligence dashboard (Power BI or Looker Studio) on the same data; simulations with "
  f"further mechanisms and comparison with the neural models of Section II-D {c('ren18', 'kumar20')}; and, with a partner "
  "business, a holdout experiment to compare attribution credit with measured incremental lift.")

# ------------------------------------------------------------------ IX conclusion
H("9", "Conclusion")
P("Using public data at scale and a simulation with known answers, we found that last-click credit is governed mainly "
  "by recency, that attribution models disagree mainly on the customers who move between channels, and that the most "
  "accurate attribution model depends on how advertising works. Businesses should therefore compare attribution models "
  "rather than trust any single report. ChannelTrace makes that comparison free and accessible, and its grounded "
  "assistant explains the results in plain language from computed figures only.")

# ------------------------------------------------------------------ acknowledgment
H("", "Acknowledgment")
P("This work was carried out for the MDM Digital Marketing Capstone (BCE27MD06) at Pimpri Chinchwad College of "
  "Engineering, Pune, under the guidance of Mrs. Minal Shahakar.")

# ------------------------------------------------------------------ references
H("", "References")
missing = [k for k in REFS if k not in ORDER]
assert not missing, f"references never cited: {missing}"
for i, k in enumerate(ORDER, 1):
    p = P(indent=False, after=2, align=WD_ALIGN_PARAGRAPH.LEFT)
    p.paragraph_format.left_indent, p.paragraph_format.first_line_indent = Inches(0.3), Inches(-0.3)
    p.paragraph_format.tab_stops.add_tab_stop(Inches(0.3))
    add(p, f"[{i}]\t", size=8)
    add(p, REFS[k], size=8)

path = OUT / "ChannelTrace_Paper_Extended.docx"
doc.save(path)
print("saved", path, "|", len(ORDER), "references")

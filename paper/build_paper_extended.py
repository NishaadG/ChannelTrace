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
add(p, (f"Most small businesses decide which marketing channel is working by reading last-click reports, even though "
        f"their customers often see several channels before buying. We tested how much that habit distorts the picture, "
        f"using four public datasets, a simulation in which the right answer is known"
        f"{' and a question-answering test of our own assistant' if ev else ''}. In {cr['impressions'] / 1e6:.1f} million "
        f"Criteo display impressions, Criteo was credited with only {pct(cr['attributed_share'])} of the "
        f"{cr['conversions']:,} conversions that came after one of its clicks. The deciding factor was time: a purchase "
        f"made within an hour of the click was credited {pct(hours['<1h']['share'], 0)} of the time, one made 7 to 31 days "
        f"later {pct(hours['7-31d']['share'], 0)} (odds ratio {rt['logit']['log_hours']['or']:.2f} per unit of log hours), "
        f"and extra clicks made almost no difference (odds ratio {rt['logit']['clicks']['or']:.2f}). Across "
        f"{ga['conversions']:,} Google Analytics 360 purchase journeys, {pct(ga['multi_session_share'], 0)} took more than "
        f"one visit but only {pct(ga['multi_channel_share'], 0)} used more than one channel, and in those journeys first "
        f"and last touch told opposite stories (Direct received {pct(mcs['Direct']['First touch'], 0)} of the credit under "
        f"one and {pct(mcs['Direct']['Last touch'], 0)} under the other). In {uci['sessions']:,} store sessions, new visitors "
        f"bought more often than returning ones ({pct(v.loc['New_Visitor', 'conversion_rate'])} against "
        f"{pct(v.loc['Returning_Visitor', 'conversion_rate'])}), and browsing behaviour alone predicted a purchase with "
        f"ROC-AUC {mo['rf_auc']:.2f}. In the simulation, {nm(best_i['model'])} was the most accurate model when ads work "
        f"straight away ({best_i['mae_pp']:.1f} percentage points mean error) and {nm(best_c['model'])} when their effect "
        f"builds up over later visits ({best_c['mae_pp']:.1f} points); first touch was the worst in both cases. The methods "
        f"are packaged in ChannelTrace, a free web tool that runs seven attribution models on a business's own Google Ads, "
        f"Meta Ads or journey export"
        + (f". Its assistant answered {eg['answerable_correct']} of {eg['answerable']} test questions correctly and turned "
           f"down {eg['unanswerable_declined']} of {eg['unanswerable']} that the data could not answer." if ev else
           " and explains the results in plain language.")), bold=True, size=9)
p = P(indent=False, after=8); add(p, "Index Terms", bold=True, italic=True, size=9); add(p, "—", bold=True, size=9)
add(p, "multi-touch attribution, last-click, customer journey, conversion prediction, Markov chain, Shapley value, "
       "retrieval-grounded assistant, digital marketing analytics", bold=True, size=9)

# ------------------------------------------------------------------ I introduction
H("1", "Introduction")
P("Someone sees an Instagram ad on Monday, searches for the brand on Wednesday, gets an email on Friday and buys after "
  f"typing the address in directly. Marketers now describe buying as a journey of this kind rather than a funnel "
  f"{c('court09', 'lemon16')}, and digital tools record most of its steps {c('kannan17')}. Attribution is the rule that "
  "splits the credit for the sale among those steps. It matters because next month's budget usually follows this "
  "month's credit.")
P("The rule most reports still use is last click: the final interaction gets everything. It is easy to explain, and "
  f"it is also biased toward whatever channel tends to come last {c('berman18')}. Each ad platform adds its own bias by "
  "reporting from its own side, so two platforms can both claim the same sale while the channel that first brought the "
  "customer in looks useless. The choice has also narrowed: Google Ads no longer offers first-click, linear, "
  f"time-decay or position-based attribution, only last click and its own data-driven model {c('google')}, which an "
  "advertiser cannot inspect. Randomised experiments would settle the question, but they are costly and need very "
  f"large samples even at the scale of major advertisers {c('lewis15', 'gordon19')}. A local shop cannot run one.")
P(f"Researchers have proposed better models for more than a decade {c('li14', 'shao11', 'anderl16', 'diemert17')}. "
  "These models are mostly tested on private company data where nobody knows the true answer, and they rarely reach "
  "the people who could use them: small businesses, student teams, freelance marketers. We started this project as a "
  "practical question for that audience, and it became five research questions:")
for q in ["*RQ1:* which channel journeys come before a purchase?",
          "*RQ2:* how do sessions that end in a purchase differ from those that do not?",
          "*RQ3:* does a channel's importance change with the attribution model, and which model is closest to the truth?",
          "*RQ4:* which visitor and session traits go together with buying?",
          "*RQ5:* can the methods be packaged so that a small business gets correct, usable answers from its own data?"]:
    pp = P(q, indent=False); pp.paragraph_format.left_indent = Inches(0.14)
P("The paper makes five contributions. First, using 16.5 million real display impressions, we show that last-click "
  "credit depends mostly on how recently the customer clicked. Second, we follow real customers across visits and "
  "find where the models actually disagree. Third, a simulation with known channel effects shows that the best model "
  "depends on how the advertising works, so models should be compared rather than picked once. Fourth, we describe "
  "which session behaviours go with buying. Fifth, we release ChannelTrace, a free tool that does all of this on any "
  f"business's export, with {'a tested' if ev else 'a grounded'} assistant that explains the output.", before=2)
P("Section II reviews earlier work, Sections III and IV cover the data and methods, Section V describes the tool and "
  "Section VI the results. Section VII discusses what the results mean and where they could be wrong, Section VIII "
  "lists limitations and next steps, and Section IX concludes.")

# ------------------------------------------------------------------ II related work
H("2", "Related Work")
H("2.1", "Customer Journeys and Multichannel Marketing")
P(f"Lemon and Verhoef {c('lemon16')} describe the journey in three stages, before, during and after purchase, and "
  f"point out that the firm controls only some of the touchpoints. Kannan and Li {c('kannan17')} list attribution among "
  f"the unsolved measurement problems of digital marketing. Two studies show why it is hard: Wiesel et al. "
  f"{c('wiesel11')} traced how online and offline activity moves customers through the funnel toward profit, and "
  f"Kireyev et al. {c('kireyev16')} found that display ads increase later searches, so the value one channel creates "
  f"can be booked to another. De Haan et al. {c('dehaan16')} reached a similar conclusion for content-integrated "
  "advertising, which last click undervalues.")
H("2.2", "Probabilistic and Data-Driven Attribution")
P(f"Shao and Li {c('shao11')} were among the first to learn credit from both buyers and non-buyers, and they argued "
  f"that a model needs to be stable as well as accurate. Li and Kannan {c('li14')} modelled how customers consider and "
  "move between a firm's channels and checked the model with a field experiment; the credit it gave differed a lot from the "
  f"last-click figures. Anderl et al. {c('anderl16')} treated journeys as Markov chains and scored each channel by how "
  "much conversion drops when it is removed, and they also found the simple rules misleading. Other approaches model "
  f"exposures and purchases as point processes that excite each other {c('xu14')}, or use survival analysis so that "
  f"an ad's influence fades over time {c('ji17')}. On the theory side, Berman {c('berman18')} showed that last-touch "
  "payment rules can push advertisers toward the wrong spending.")
H("2.3", "Game-Theoretic Attribution")
P(f"The Shapley value {c('shapley53')} comes from cooperative game theory: each player's share is its average extra "
  f"contribution across every possible team. Dalessandro et al. {c('dalessandro12')} linked it to a causal view of "
  f"attribution, and Zhao et al. {c('zhao18')} gave simpler versions for advertising data. Singal et al. "
  f"{c('singal22')} wrote down the properties a fair attribution rule should have, showed that the common rules break "
  "them, and proposed an adjusted Shapley value. The same idea is behind SHAP, the popular way of explaining "
  f"machine-learning predictions {c('lundberg17')}.")
H("2.4", "Deep Learning Attribution")
P(f"Newer models learn credit from touchpoint sequences with neural networks: attention with user controls "
  f"{c('li18')}, a dual-attention recurrent network that separates the effect of views and clicks {c('ren18')}, a "
  f"recurrent network that asks what would have happened without each touch {c('du19')}, and a causal correction for "
  f"the fact that people are not shown ads at random {c('kumar20')}. Several are tested on the Criteo data "
  f"{c('diemert17')} that we also use. Their success is judged by how well they predict conversions, and a model can "
  "predict well while still giving credit to the wrong channel.")
H("2.5", "Experiments and Incrementality")
P(f"Experiments measure what attribution tries to estimate. Blake et al. {c('blake15')} switched off eBay's brand "
  f"search ads and found that most of the sales they seemed to drive happened anyway. Johnson et al. {c('johnson17')} "
  f"proposed \"ghost ads\" to make such tests cheaper, and Gordon et al. {c('gordon19')} compared large Facebook "
  "experiments with the observational methods advertisers normally use and found that the latter often missed. Lewis "
  f"and Rao {c('lewis15')} explain why even large experiments give noisy answers. When an experiment is not possible, a "
  "simulation where the true effect is set in advance is the next best way to check a model.")
H("2.6", "Clickstream Conversion Prediction")
P(f"Moe and Fader {c('moe04')} showed that the chance of buying changes from one store visit to the next. Montgomery "
  f"et al. {c('montgomery04')} predicted purchase from the order in which pages were browsed, and Bucklin and Sismeiro "
  f"{c('bucklin09')} surveyed clickstream research in marketing. Sakar et al. {c('sakar19')} predicted purchase intent "
  "from session features and published the UCI Online Shoppers data we analyse.")
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
P("Table I puts the gap in one place. Most studies use data the reader cannot get, propose one model and test it, "
  "and leave nothing a practitioner can run. We work only with public data, add a simulation where the true answer is "
  "known, compare seven models side by side, and hand the whole method over as a free tool"
  + (" whose assistant we also tested." if ev else "."))

# ------------------------------------------------------------------ III data
H("3", "Data")
P("We used each dataset only for the questions it can answer. They come from different businesses and periods, so we "
  "never combine them (Table II).")
T("The Datasets and What Each Is Used For",
  ["Dataset", "Content", "Used for"],
  [[f"UCI Online Shoppers {c('sakar19')}", f"{uci['sessions']:,} sessions (after removing 125 duplicates), 17 features, purchase outcome", "RQ2, RQ4"],
   [f"Criteo Attribution {c('diemert17')}", f"{cr['impressions']:,} impressions, {cr['users']:,} users, {cr['campaigns']} campaigns, 30 days", "RQ3 (last-click gap, recency)"],
   [f"Google Analytics 360 sample {c('ga360')}", f"{ga['sessions']:,} sessions, {ga['visitors']:,} visitors, named channels, 12 months", "RQ1, RQ3"],
   [f"Facebook Ad Campaign {c('kaggle')}", "1,143 real ads, spend, clicks, conversions, age, gender", "RQ5 (tool validation)"],
   ["Simulated journeys", "6 random worlds x 2 scenarios x 3,000 users with known channel effects", "RQ3 (model accuracy)"],
   *([["Assistant test set", f"{ev['n']} questions with known answers", "RQ5 (assistant accuracy)"]] if ev else [])],
  widths=[1.0, 1.65, 0.85])
P("*UCI Online Shoppers.* One year of sessions from a single online shop. For each session the data gives how many "
  "account, information and product pages were opened and for how long, the bounce and exit rates, a page-value score "
  "from Google Analytics, the month, whether the visitor was new, whether it was a weekend, a traffic-source code and "
  "whether the session ended in a sale. 125 rows were exact copies of others and were dropped.")
P(f"*Criteo Attribution.* Thirty days of display impressions, each with a user, campaign, time and click flag. For "
  f"users who bought, it also gives the purchase time and whether the advertiser's last-click rule gave Criteo the "
  f"credit. We grouped each user's impressions into a journey ending at the purchase. Our first plan was to compare "
  f"campaigns inside a journey, but a check ruled that out: {pct(cr['single_campaign_share'])} of purchases involve "
  f"only one campaign. The sample also keeps only clicked impressions for buyers, so clicks cannot be compared with "
  f"views either. We therefore used Criteo for a narrower question that it answers well: how often last click credits "
  f"the network, and what decides it.")
d0, d1 = (pd.to_datetime(s.strip()).strftime("%B %Y") for s in ga["period"].split("to"))
P(f"*Google Analytics 360.* Google publishes a year of anonymised sessions from its own Merchandise Store, {d0} to "
  f"{d1}, in BigQuery. Each session has a visitor ID that persists across visits, a start time, Google's channel label "
  "and a transaction count. We defined a journey as a visitor's sessions in time order up to and including the first "
  "one with a purchase; for visitors who never bought it runs to their last session. We queried it through the free "
  "BigQuery sandbox. Our computer could not hold every journey in memory, so buyers' journeys were downloaded one by one "
  "and the rest were counted by channel path inside BigQuery, which is all the Markov model needs.")
P("*Facebook Ad Campaign.* A public export of 1,143 ads with spend, impressions, clicks, conversions and the age and "
  "gender targeted. We used it as a realistic upload to test the tool. The *simulated journeys* and the *assistant test "
  "set* are described in Section IV.")

# ------------------------------------------------------------------ IV methods
H("4", "Methods")
H("4.1", "Notation and Rule-Based Models")
P(r"Write a converting journey as touchpoints $(c_1,t_1),\dots,(c_n,t_n)$, where $c_i$ is the channel and $t_i$ the "
  r"time of touch $i$, and the sale happens at time $T$. A model gives each touch a weight $w_i$, with $\sum_i w_i=1$. "
  r"A channel's credit is the total weight of its touches over all converting journeys:")
E(r"A(k)=\sum_{\text{journeys}}\sum_{i:\,c_i=k}w_i")
P(r"First touch puts $w_1=1$, last touch $w_n=1$, and linear $w_i=1/n$. Time decay halves the weight for every "
  r"$h=7$ days between a touch and the sale:")
E(r"w_i=\frac{2^{-(T-t_i)/h}}{\sum_j 2^{-(T-t_j)/h}}")
P(r"Position based gives 40% to the first touch, 40% to the last and splits the other 20% evenly across the middle "
  r"(with two touches each gets half; with one it gets everything).")
H("4.2", "Markov Chain Removal Effect")
P(f"We follow Anderl et al. {c('anderl16')} and treat every journey, with or without a sale, as a walk between states: "
  r"a start state, one state per channel, and two end states, conversion and null. From the observed transition counts "
  r"$N$, the probability of moving from state $a$ to state $b$ is")
E(r"p(a,b)=\frac{N(a,b)}{\sum_{b'}N(a,b')}")
P(r"Conversion and null are absorbing. If $Q$ holds the transitions between ordinary states and $R$ those into the two "
  r"end states, the absorption probabilities are $B=(I-Q)^{-1}R$ " + c("norris97") + r", and $P(\text{conv})$ is the "
  r"chance of ending in conversion from start. To remove channel $k$ we send every step into $k$ to null instead. "
  r"The removal effect and the resulting credit are")
E(r"RE(k)=1-\frac{P_{-k}(\text{conv})}{P(\text{conv})}")
E(r"A(k)=C\cdot\frac{RE(k)}{\sum_j RE(j)}")
P(r"with $C$ the number of conversions. For GA360 each counted non-converting path enters $N$ with a weight equal to "
  r"the number of journeys it stands for. We checked on smaller data that this weighting gives exactly the same answer "
  r"as counting journeys one by one.")
H("4.3", "Shapley Value")
P(r"Let $K$ be the set of channels and let $v(S)$, the value of a group $S\subseteq K$, be the number of converting "
  r"journeys that use only channels in $S$. The Shapley value " + c("shapley53") + r" of channel $k$ is")
E(r"\phi(k)=\sum_{S\subseteq K\setminus\{k\}}\frac{|S|!\,(|K|-|S|-1)!}{|K|!}\left[v(S\cup\{k\})-v(S)\right]")
P(r"The shares add up to the whole, $\sum_k\phi(k)=v(K)=C$, so this model also hands out exactly the observed "
  r"conversions. The exact sum grows exponentially with $|K|$; our implementation allows up to 12 channels, more than "
  r"any dataset here has. Table III lists the seven models side by side.")
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
P("Real data never tells us how much credit a channel really deserves, so we built worlds where we set it ourselves. "
  r"In each world the seven channels get a lift $\lambda_k$ drawn at random from $[0.01,0.25]$, and the first channel "
  r"and each later channel are drawn from Dirichlet(2) distributions. A simulated user makes up to eight visits. After "
  r"a visit without a purchase the user leaves for good with probability 0.35; otherwise they come back after a gap "
  r"drawn from an exponential distribution with a mean of 60 hours. The chance of buying at visit $m$ is")
E(r"P(\text{buy at }m)=\kappa_m\,\sigma\left(-3+6\sum_{j\in J(m)}\lambda_{c_j}\right)")
P(r"with $\sigma$ the logistic function, $\kappa_1=0.25$ and $\kappa_m=0.45$ after the first visit. Two scenarios "
  r"differ only in $J(m)$. In the *immediate* scenario it includes visit $m$ itself, so an ad can trigger a sale on the "
  r"spot. In the *carry-over* scenario it includes only earlier visits, the way awareness ads work. To get the truth "
  r"for channel $k$ we rerun the same world, with the same random numbers, with $k$'s lift set to zero, and count the "
  r"sales that disappear. Its true share $s_k$ is that loss over the sum of losses for all channels. A model's shares "
  r"$\hat{a}_k$ are scored by")
E(r"\text{MAE}=\frac{1}{|K|}\sum_k\left|\hat{a}_k-s_k\right|")
P(f"in percentage points, and by Spearman's rank correlation {c('spearman04')} with the true shares. We ran six worlds "
  f"of 3,000 users for each scenario. To check how stable the credit is, we also drew 200 bootstrap resamples "
  f"{c('efron93')} of a separate synthetic set in which Social and Display were built to open journeys while Email "
  "and Paid Search were built to finish them.")
H("4.5", "Recency of Last-Click Credit")
P(r"For each Criteo purchase $i$ we note whether Criteo got the last-click credit ($y_i=1$), the number of Criteo "
  r"clicks $n_i$ (capped at 10) and the hours $h_i$ between the last click and the purchase. We test the link with "
  r"Pearson's chi-square test " + c("pearson1900") + " across six time bands and fit")
E(r"\mathrm{logit}\,P(y_i=1)=\beta_0+\beta_1\log(1+h_i)+\beta_2 n_i")
H("4.6", "Session Behaviour and Conversion")
P(f"Numeric session measures of buyers and non-buyers are compared with the Mann-Whitney U test {c('mann47')} "
  "(two-sided), and the categorical ones, visitor type, month and weekend, with chi-square tests. For prediction we train logistic regression, "
  f"random forest {c('breiman01')} and gradient boosting {c('friedman01')} models in scikit-learn {c('pedregosa11')} on "
  f"three quarters of the sessions (stratified by outcome, classes reweighted to balance them) and score them by "
  f"ROC-AUC {c('fawcett06')} on the remaining quarter. One feature needed care. "
  "PageValues is calculated from the pages a visitor saw before a transaction, so it partly contains the answer, and "
  "we therefore report every model both with and without it. To see which inputs matter, we shuffle one feature at a "
  "time in the test data and record how far the AUC drops.")
if ev:
    H("4.7", "Assistant Evaluation")
    P(f"Before running the test we wrote {ev['n']} questions. For {eg['answerable']} of them the answer is in the fact "
      f"sheet; the other {eg['unanswerable']} cannot be answered from the data, for example the return on television "
      "advertising or next month's sales. Each question was sent once, with no earlier conversation, to both of the "
      "site's answer paths. An answerable question counts as correct if the reply contains every expected fact, allowing "
      "for rounding such as 54% for 54.2%. An unanswerable one counts as correct if the reply says the data does not "
      "cover it and gives no figure. We also pulled every number out of every reply and looked it up in the fact sheet; "
      "a number found nowhere counts as unsupported, which is a direct measure of made-up figures. We read all replies "
      "ourselves to check the automatic scores.")

# ------------------------------------------------------------------ V system
H("5", "The ChannelTrace System")
F(FIG / "architecture.png", "ChannelTrace architecture. Everything inside the dashed box runs in the user's browser; only the aggregated fact sheet reaches the assistant.")
P("Our first prototype was a Streamlit dashboard in Python. We rebuilt it as a TypeScript and React web app hosted "
  "free on Vercel (Fig. 1) so that all analysis happens in the browser and an uploaded file never leaves the user's "
  "computer. The ad module recognises exports from Google Ads, Meta Ads Manager and "
  "similar tools, renames their columns to a common set, and works out click-through rate, cost per click, conversion rate, cost per "
  "acquisition (CPA) and return on ad spend. Every campaign is then labelled by comparing it with the account as a "
  "whole: worth scaling, on track, too expensive, or not converting at all. The module also shows money spent with nothing to show for it, "
  "and splits results by audience and by day. The journey module puts the seven attribution models next to each "
  "other, so a user can see which channels last click flatters and which it shortchanges. We checked the browser code against the Python version used for "
  "the research.")
P("All results are boiled down to a fact sheet of short, labelled statements, plus suggested actions and caveats. The "
  "assistant may only answer from this sheet, which limits how much it can invent "
  f"{c('lewis20', 'ji23')}. When a key is set, a small server function passes the sheet and the question to a free "
  "Gemini model. During development the model we started with was retired and the newer ones were often overloaded, so "
  "the function now tries several models in turn within a fixed time limit. Without a key, or if every model fails, a "
  f"built-in fallback ranks the sheet's statements against the question by TF-IDF {c('salton88')} and quotes the "
  "closest ones. That version works offline and can only repeat numbers we computed.")

# ------------------------------------------------------------------ VI results
H("6", "Results")
H("6.1", "Last-Click Credit Is Driven by Recency (RQ3)")
P(f"Each of the {cr['conversions']:,} Criteo purchases had a Criteo click somewhere before it. Even so, the "
  f"advertiser's attribution system handed Criteo only {pct(cr['attributed_share'])} of them; the rest went to other channels. Journeys "
  f"were short: {cr['touches_mean']:.2f} clicks on average, {pct(cr['single_touch_share'], 0)} with a single click, and "
  f"typically {cr['hours_last_to_conv_median']:.1f} hours between the final click and the sale (median), and a median of "
  f"{cr['span_days_median_multi']:.1f} days between the first and last click when there was more than one. Fig. 2 shows "
  f"credit falling steadily as the gap grows (chi-square = {rt['chi2']:,.0f}, df = {rt['dof']}, p < 0.001).")
F(FIG / "recency.png", "How often Criteo kept the last-click credit, grouped by the gap between its last click and the purchase (purchases per group in brackets).")
by_t = cr["attributed_by_touches"]
T("What Predicts Criteo Keeping the Credit (Logistic Regression, n = %s)" % f"{rt['n']:,}",
  ["Predictor", "Odds ratio", "95% CI", "p"],
  [["log(1 + hours since click)", f"{rt['logit']['log_hours']['or']:.3f}", "%.3f to %.3f" % tuple(rt["logit"]["log_hours"]["ci_or"]), "< 0.001"],
   ["Criteo clicks (capped at 10)", f"{rt['logit']['clicks']['or']:.3f}", "%.3f to %.3f" % tuple(rt["logit"]["clicks"]["ci_or"]), "< 0.001"]],
  widths=[1.4, 0.6, 0.95, 0.55], numeric=(1, 2, 3))
P(f"With the number of clicks held fixed, each unit of log(1 + hours) multiplies the odds of Criteo getting credit by "
  f"{rt['logit']['log_hours']['or']:.2f}. Each extra click multiplies them by just {rt['logit']['clicks']['or']:.2f} "
  f"(pseudo R-squared {rt['pseudo_r2']:.2f}; Table IV). Table V shows the same thing without a model: the credited "
  "share barely moves between one click and six.")
T("Last-Click Credit to Criteo by Number of Criteo Clicks", ["Clicks in journey", "Conversions", "Credited to Criteo"],
  [[k if k != "6" else "6 or more", f"{by_t[k]['n']:,}", pct(by_t[k]["share"])] for k in by_t],
  widths=[1.1, 1.0, 1.1], numeric=(1, 2))
P("So under last click, whether a channel gets paid for a sale depends on timing far more than on effort. Click a "
  "display ad and buy within the hour, and the ad nearly always gets the credit. Wait a week, search for the product "
  "or open an email in between, and it usually does not.")

H("6.2", "Real Multi-Channel Journeys (RQ1, RQ3)")
P(f"The GA360 sample has {ga['visitors']:,} visitors and {ga['sessions']:,} sessions. Tracing each visitor up to their "
  f"first purchase gives {ga['conversions']:,} converting journeys, {pct(ga['conv_rate'])} of all journeys. Most buyers "
  f"needed more than one visit: {pct(ga['multi_session_share'], 0)} of converting journeys had two or more sessions "
  f"(mean {ga['sessions_mean']:.2f}, maximum {ga['sessions_max']}), against {ga['nonconv_sessions_mean']:.2f} sessions for "
  f"journeys that ended without a sale. Repeat-visit buyers took a median of "
  f"{ga['days_first_to_purchase_median_multi']:.1f} days to decide. Surprisingly, only "
  f"{pct(ga['multi_channel_share'], 0)} of converting journeys used more than one channel. The most common paths were a "
  f"single {ga['top_paths'][0][0]} visit ({ga['top_paths'][0][1]:,}), a single {ga['top_paths'][1][0]} visit "
  f"({ga['top_paths'][1][1]:,}) and {ga['top_paths'][3][0]} ({ga['top_paths'][3][1]:,}).")
T("Sessions and Converting Sessions by Channel (GA360)", ["Channel", "Sessions", "Converting", "Rate"],
  [[ch["channel"], f"{ch['sessions']:,}", f"{ch['converting']:,}", pct(ch["rate"], 2)]
   for ch in sorted(ga["channels"], key=lambda r: -r["rate"]) if ch["sessions"] >= 1000],
  widths=[1.1, 0.8, 0.8, 0.7], numeric=(1, 2, 3))
P(f"How often a visit ends in a sale varies a lot by channel (Table VI). Referral visits converted at "
  f"{pct(chan['Referral']['rate'], 1)}. Social brought the second-largest stream of visits, "
  f"{chan['Social']['sessions']:,}, but converted at only {pct(chan['Social']['rate'], 2)}. Organic Search brought the "
  f"most visits and converted at {pct(chan['Organic Search']['rate'], 1)}.")
T("GA360 Credit Share by Channel and Model, All Buying Journeys", ["Channel", "First", "Last", "Linear", "Markov", "Shapley"],
  [[ch, *[pct(sh[ch][mm]) for mm in ("First touch", "Last touch", "Linear", "Markov chain", "Shapley value")]]
   for ch in sorted(sh, key=lambda ch: -sh[ch]["Linear"]) if sh[ch]["Linear"] > 0.0005],
  widths=[0.92, 0.48, 0.48, 0.48, 0.56, 0.58], numeric=(1, 2, 3, 4, 5))
swing = max(sh, key=lambda ch: max(sh[ch].values()) - min(sh[ch].values()))
P(f"Since so few journeys mix channels, the seven models give similar answers for the store as a whole (Table VII). "
  f"The biggest spread is for {swing}, from {pct(min(sh[swing].values()))} to {pct(max(sh[swing].values()))}. The "
  f"disagreement sits in the {ga['multi_channel']['journeys']:,} journeys that did mix channels (Fig. 3). For those, "
  f"first touch gives Direct {pct(mcs['Direct']['First touch'], 0)} of the credit and last touch gives it "
  f"{pct(mcs['Direct']['Last touch'], 0)}; Referral goes the other way, from {pct(mcs['Referral']['First touch'], 0)} "
  f"to {pct(mcs['Referral']['Last touch'], 0)}. The two most common mixed paths were "
  f"{ga['multi_channel']['top_paths'][0][0]} ({ga['multi_channel']['top_paths'][0][1]}) and "
  f"{ga['multi_channel']['top_paths'][1][0]} ({ga['multi_channel']['top_paths'][1][1]}). For these customers, the model "
  "decides which channel looks worth paying for.")
F(FIG / "ga360.png", f"First-touch, linear and last-touch credit for the {ga['multi_channel']['journeys']:,} GA360 buying journeys that mixed channels.")
order = sorted(stay, key=lambda ch: stay[ch])  # most likely to hand the journey on first
P("Channels also differ in how often they pass a customer on. The share of converting journeys that ended in a "
  "different channel from the one they started in was " + ", ".join(f"{ch} {pct(1 - stay[ch], 0)}" for ch in order[:-1])
  + f" and {order[-1]} {pct(1 - stay[order[-1]], 0)} (counting channels that started at least 100 journeys). Journeys "
  f"that begin with {order[0]}, {order[1]} or {order[2]} are the ones most often finished by something else, and "
  "these are the cases where last click takes credit away from the channel that started them. A referral almost never "
  "hands over.")
P(f"Two quirks of the data matter here. When a visitor comes back directly, Google Analytics records the visit under "
  f"the source of their previous campaign; in this sample {rf['true_direct_sessions']:,} sessions labelled Referral "
  f"(out of {rf['sessions']:,}) carry the direct-visit flag. That makes it hard for Direct to appear after another channel, which pushes its "
  f"last-touch share down. Also, {pct(rf['converting_share'], 0)} of converting Referral sessions have no referring site "
  f"recorded, so Referral's large share says little about how valuable links from other websites are.")

H("6.3", "No Attribution Model Is Best Everywhere (RQ3)")
F(FIG / "simulation.png", "Average gap between each model's credit and the true shares, in percentage points; whiskers give the spread across the six simulated worlds.")
T("Model Error Against the True Channel Shares",
  ["Model", "Immediate MAE", "ρ", "Carry-over MAE", "ρ"],
  [[mm, f"{si[mm]['mae_pp']:.1f}", f"{si[mm]['spearman']:.2f}", f"{sc[mm]['mae_pp']:.1f}", f"{sc[mm]['spearman']:.2f}"] for mm in models],
  widths=[1.0, 0.75, 0.4, 0.85, 0.4], numeric=(1, 2, 3, 4))
P(f"With ads that work immediately, the smallest error belonged to {nm(best_i['model'])} ({best_i['mae_pp']:.1f} pp), "
  f"just ahead of time decay ({si['Time decay']['mae_pp']:.1f} pp). Once the effect carried over to later visits, "
  f"the error of last touch climbed to {sc['Last touch']['mae_pp']:.1f} pp while its rank correlation slid from "
  f"{si['Last touch']['spearman']:.2f} to {sc['Last touch']['spearman']:.2f}, and time decay and linear tied for the "
  f"lowest error, {sc['Time decay']['mae_pp']:.1f} pp each (Fig. 4, Table VIII). On ranking the "
  f"channels in the right order, {nm(max(si.values(), key=lambda r: r['spearman'])['model'])} did best with immediate "
  f"effects ({max(r['spearman'] for r in si.values()):.2f}) and "
  f"{nm(max(sc.values(), key=lambda r: r['spearman'])['model'])} with carry-over "
  f"({max(r['spearman'] for r in sc.values()):.2f}), the Shapley value close behind both times "
  f"({si['Shapley value']['spearman']:.2f} and {sc['Shapley value']['spearman']:.2f}). Neither scenario was kind "
  "to first touch, which had the largest error in both. The Markov model never came out on top in these worlds, so being data-driven did not by itself make "
  "it right.")
P("The reason is simple. When an ad works on the spot, the touch that causes the sale is usually the final one, so last "
  "touch is close to the truth. When the effect builds up, the important touches come early and the sale can happen "
  "later through a weak channel. Any rule that piles the credit onto one end of the journey then gets it wrong, and "
  "rules that spread it do better.")
F(FIG / "bootstrap.png", "Credit under last touch and under Markov for 4,000 synthetic journeys with built-in channel roles; whiskers are 95% bootstrap intervals.")
P("In the separate synthetic set where Social and Display open journeys and Email and Paid Search close them, the "
  "data-driven models picked up those roles (Fig. 5). Under last touch Display received "
  f"{pct(boot['Last touch']['Display'][0], 0)}, while Markov gave it {pct(boot['Markov chain']['Display'][0], 0)}; "
  f"for Email the figures were {pct(boot['Last touch']['Email'][0], 0)} and {pct(boot['Markov chain']['Email'][0], 0)}. "
  "The bootstrap intervals are about one percentage point either side, far smaller than these gaps.")

H("6.4", "Session Behaviour Associated With Purchase (RQ2, RQ4)")
P(f"{pct(uci['conversion_rate'])} of UCI sessions ended in a purchase. New visitors bought in "
  f"{pct(v.loc['New_Visitor', 'conversion_rate'])} of sessions and returning visitors in "
  f"{pct(v.loc['Returning_Visitor', 'conversion_rate'])}, even though returning visitors made up {pct(ret_share, 0)} of "
  f"the traffic (chi-square p < 0.001). The best month was {peak_m['Month']} ({pct(peak_m['conversion_rate'])}) and the "
  f"worst {low_m['Month']} ({pct(low_m['conversion_rate'])}; Fig. 6). Weekend sessions converted slightly more often than "
  f"weekday ones, {pct(wk.loc[True, 'conversion_rate'])} against {pct(wk.loc[False, 'conversion_rate'])} "
  f"(chi-square p = {p_weekend:.3f}).")
F(FIG / "month.png", "Share of UCI sessions ending in a purchase, by month. The data has no January or April.")
rows = []
for b in ["Product pages viewed", "Time on product pages (s)", "Account/admin pages viewed", "Bounce rate", "Exit rate", "Page value"]:
    f = (lambda x: f"{x / 60:.1f} min") if "(s)" in b else ((lambda x: f"{x:.3f}") if "rate" in b else (lambda x: f"{x:.1f}"))
    pv = g.loc[b, "p-value"]
    rows.append([b.replace(" (s)", ""), f(g.loc[b, "Mean (converted)"]), f(g.loc[b, "Mean (not converted)"]),
                 "< 1e-300" if pv == 0 else f"{pv:.1e}"])
T("How Buyers and Non-Buyers Browsed (Session Means)", ["Measure", "Buyers", "Non-buyers", "p"],
  rows, widths=[1.45, 0.65, 0.7, 0.65], numeric=(1, 2, 3))
T("Predicting a Purchase: ROC-AUC on the 25% Test Split", ["Model", "With PageValues", "Without PageValues"],
  [["Logistic regression", f"{mw['logit_auc']:.3f}", f"{mo['logit_auc']:.3f}"],
   ["Random forest", f"{mw['rf_auc']:.3f}", f"{mo['rf_auc']:.3f}"],
   ["Gradient boosting", f"{mw['hgb_auc']:.3f}", f"{mo['hgb_auc']:.3f}"]], widths=[1.4, 1.0, 1.05], numeric=(1, 2))
imp = mo["importance"].head(5)
P(f"All ten behaviour measures differed between buyers and non-buyers. A buyer typically opened "
  f"{g.loc['Product pages viewed', 'Median (converted)']:.0f} product pages, a non-buyer "
  f"{g.loc['Product pages viewed', 'Median (not converted)']:.0f}, and buyers bounced and left far less often "
  f"(Table IX). Including PageValues lifted the random forest to an AUC of {mw['rf_auc']:.3f}; leaving it out brought it "
  f"down to {mo['rf_auc']:.3f}, and that is the fair measure of what browsing alone tells a shop (Table X). Without "
  f"PageValues, the most useful signals by permutation importance (drop in AUC) were "
  + "; ".join(f"{r.feature.replace(' (s)', '').lower().replace('month: nov', 'a November visit')} ({r.importance:.3f})" for r in imp.itertuples())
  + ". How long someone stays on product pages says more than how many they open.")

H("6.5", "Tool Validation on Real Advertising Data (RQ5)")
P("As a check on real advertising data, we loaded the public Facebook campaign export into ChannelTrace. It worked "
  "out the file format without help, and its totals agreed exactly with a separate Python calculation (total spend "
  "58,705.23, cost per acquisition 54.41). Its report flagged a tenth of the budget (10.0%) as spent on ad sets that "
  "never produced an approved conversion. The cheapest age band was 30-34, at 30.88 per acquisition; the most "
  "expensive, 45-49, cost 99.76. Male audiences converted for 41.44 each and female audiences for 69.70. On the synthetic journeys, the browser version of all seven models gave exactly the same credit "
  "as the Python version.")

if ev:
    H("6.6", "Assistant Accuracy (RQ5)")
    T("Assistant Accuracy on the Fixed Question Set", ["Measure", "Generative", "Built-in"],
      [["Answerable, correct", f"{eg['answerable_correct']} / {eg['answerable']}", f"{er['answerable_correct']} / {er['answerable']}"],
       ["Unanswerable, declined", f"{eg['unanswerable_declined']} / {eg['unanswerable']}", f"{er['unanswerable_declined']} / {er['unanswerable']}"],
       ["Overall accuracy", pct(eg["overall"], 0), pct(er["overall"], 0)],
       ["Replies with unsupported numbers", f"{eg['replies_with_unsupported_numbers']} / {ev['n']}", f"{er['replies_with_unsupported_numbers']} / {ev['n']}"]],
      widths=[1.6, 0.85, 0.85], numeric=(1, 2))
    miss = [r["question"] for r in ev["rows"] if r["answerable"] and not r["generative"]["correct"]]
    quote = lambda q: "“" + q + "”"
    P(f"The generative path got {eg['answerable_correct']} of the {eg['answerable']} answerable questions right and "
      f"declined {eg['unanswerable_declined']} of the {eg['unanswerable']} it could not answer (Table XI). "
      + (f"{eg['replies_with_unsupported_numbers']} of its {ev['n']} replies contained a number that is not in the fact "
         "sheet. " if eg["replies_with_unsupported_numbers"] else f"None of its {ev['n']} replies contained a number that "
         "is not in the fact sheet. ")
      + (f"The automatic check marked {', '.join(quote(q) for q in miss)} as wrong. " if miss else "")
      + ("Reading every reply ourselves, we would not change the total: the reply to the signals question was right "
         "in substance but used a different wording from the one the check looked for (and called medians averages), "
         "while the reply on the Markov model's carry-over error, marked right, gave the correct 7.5 pp after first "
         "saying, wrongly, that the facts did not contain it. " if ev.get("review") else "")
      + f"The built-in retrieval model got {er['answerable_correct']} of {er['answerable']} right. It can only quote "
      "computed statements, so it never makes up a figure, but it recognised only "
      f"{er['unanswerable_declined']} of the {er['unanswerable']} questions outside the data; for the rest it returned "
      "the nearest related facts, which a reader could take for an answer. The two paths therefore cover each other's "
      "weak spot: the generative model is better at saying what the data cannot show, and the fallback guarantees that "
      f"every number it shows was computed. The test ran on {ev['date']} on the free Gemini tier "
      f"({', '.join(ev['models_used'])}).")

# ------------------------------------------------------------------ VII discussion
H("7", "Discussion")
H("7.1", "Implications for Practitioners")
P("The Criteo numbers explain why ad platforms rarely agree on who made a sale. Here was a network whose click came "
  "before every single purchase, and it got credit for about half, mostly depending on how long the buyer waited. A "
  "business that takes last-click reports at face value will underrate channels that work slowly, such as awareness "
  f"campaigns, and overrate whatever happens to come last. This fits Berman's argument {c('berman18')} and the "
  f"display-to-search spill-over found by Kireyev et al. {c('kireyev16')}.")
P("The simulation shows why swapping last click for one data-driven model is not the fix. Which model was right "
  "depended on how the ads worked. Last touch was fine for ads that act immediately and poor for ads whose effect "
  "builds up; linear, time decay and the Shapley value held up better in both. A business rarely knows which kind of "
  "advertising it is running, so it is safer to run several models and treat any channel whose credit jumps around "
  "between them as uncertain. ChannelTrace is designed around exactly that comparison.")
P("The GA360 store shows that the comparison does not always change the answer. Most of its buyers came back "
  "through the channel that first brought them, and for them the model barely matters. It matters a lot for the "
  "minority who switch: typically people who first arrive by typing the address or searching, then complete the "
  "purchase after following a referral link. Any "
  "business can check this for itself: if few converting journeys mix channels, last click is roughly good enough; "
  "if many do, compare the models before moving money.")
P("The session data points to three things a shop could try. Returning visitors make up the bulk of traffic yet "
  "buy least, so they are worth winning back. Budget is best raised in the weeks leading up to the seasonal peak. And "
  "paid traffic should land directly on product pages, where time spent is the clearest early sign of intent. These are ideas to test, not proven effects. Where "
  f"the budget allows, a holdout test {c('johnson17', 'gordon19')} is how to confirm them.")
H("7.2", "Implications for Research")
P("Attribution models are usually ranked by how well they predict conversion. In our simulation a model could "
  "predict reasonably and still hand credit to the wrong channels, because predicting a sale and dividing credit for "
  "it are different tasks. Simulations with a known answer are simplified, but they test the credit directly and are "
  "cheap to extend, and we think they belong next to experimental benchmarks. Public journey data with named channels "
  "is still hard to find. GA360 is one of the few sources, and its relabelling of direct visits shows how much a "
  "platform's own definitions can shape the result.")
H("7.3", "Threats to Validity")
P("*Construct validity.* Credit is not the same as causal effect. Every model here, including the data-driven ones, "
  "shares out sales that happened; none of them says what would have happened without a channel. That is why we "
  "judge the models in a simulation whose true shares are causal by design. *Internal validity.* The Criteo credit "
  "flag is the advertiser's own last-click decision, and the competing channels are not in the data, so the recency "
  "result describes how credit was given, not why customers bought. GA360 journeys rely on a cookie-based visitor ID "
  "and on Google's channel rules, including the relabelling of direct visits. *External validity.* Each dataset comes "
  "from a single store, network or advertiser, mostly in mature markets. Indian small businesses may behave "
  "differently, and the tool lets them check on their own data. *Statistical conclusion validity.* With hundreds of "
  "thousands of rows almost every difference is significant, so we report sizes (credit shares, odds ratios, AUC, "
  "error in percentage points) next to every p-value.")
H("7.4", "Ethics and Privacy")
P("Every dataset is public and anonymised, and we collected no personal data. ChannelTrace processes uploads in the "
  "browser and sends only the summary fact sheet, never raw rows, to the language model. The assistant is told to "
  "mark recommendations as suggestions and to say that the data shows associations rather than causes, so that "
  "people do not trust its advice more than the data allows.")

# ------------------------------------------------------------------ VIII limitations
H("8", "Limitations and Future Work")
P("Everything we report is an association. The Criteo sample covers one channel and keeps only clicked impressions "
  "for buyers, which leaves the effect of ads that were seen but not clicked out of reach. In the UCI data the "
  "traffic sources are numbered codes without names. The simulation uses two simplified mechanisms with six worlds each, and others, such as "
  "diminishing returns or channels that boost each other, could favour different models. GA360 is one store, uses "
  "Google's own channel labels and splits a person who switches devices into two journeys. "
  + ("The assistant was tested once, on questions we wrote ourselves, and the free models behind it keep changing."
     if ev else "We have not yet measured how accurate the assistant is."))
P(f"We see {'four' if ev else 'five'} next steps: {'' if ev else 'an accuracy test of the assistant on fixed questions with known answers; '}"
  f"a usability study with small-business owners using the System Usability Scale {c('brooke96')}; a Power BI or "
  "Looker Studio dashboard on the same data; more simulated mechanisms and a comparison with the neural models of "
  f"Section II-D {c('ren18', 'kumar20')}; and, with a partner business, a holdout experiment to compare attribution "
  "credit with measured lift.")

# ------------------------------------------------------------------ IX conclusion
H("9", "Conclusion")
P("Using large public datasets and a simulation where the answer is known, we found three things. Last-click credit "
  "depends mostly on how recently the customer clicked. Attribution models disagree mainly about customers who move "
  "between channels. And the most accurate model depends on how the advertising works. A business should therefore "
  "compare models instead of trusting any single report. ChannelTrace lets anyone do that for free, and its assistant "
  "explains the results in plain language using only the figures the tool computed.")

# ------------------------------------------------------------------ acknowledgment
H("", "Acknowledgment")
P("We carried out this project as our MDM Digital Marketing Capstone (course code BCE27MD06) at PCCoE, Pune. We thank our guide, Mrs. Minal Shahakar, for her guidance.")

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

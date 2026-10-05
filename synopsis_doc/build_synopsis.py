"""Builds the ChannelTrace synopsis in the college's MDM Capstone format (Word + PDF).

Run:  python build_synopsis.py
Fill the [bracketed] fields in TEAM / HEADER below, then run again.
"""
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

HERE = Path(__file__).resolve().parent
OUT = HERE / "ChannelTrace_Synopsis.docx"

# ----------------------------------------------------------------------------- fill these in
HEADER = {
    "department": "[Department]",
    "academic_year": "2026-2027",
    "semester": "I",
    "year": "B. Tech",
    "group_id": "[Group ID]",
    "date": "[DD/MM/2026]",
    "guide": "[Guide name]",
}
TEAM = [  # (PRN, name, department, mail, contact)
    ("[PRN]", "[Student name]", "[Department]", "[Mail-id]", "[Contact]"),
    ("[PRN]", "[Student name]", "[Department]", "[Mail-id]", "[Contact]"),
    ("", "", "", "", ""),
    ("", "", "", "", ""),
]
TITLE = "Multi-Channel Digital Marketing Attribution and Conversion Analysis (ChannelTrace)"
SDGS = [("SDG 8", "Decent Work and Economic Growth"), ("SDG 9", "Industry, Innovation and Infrastructure"), ("", "")]

# ----------------------------------------------------------------------------- helpers
FONT = "Times New Roman"


def set_cell_border(table):
    tbl = table._tbl
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:color"), "000000")
        borders.append(el)
    tbl.tblPr.append(borders)


def run(p, text, bold=False, italic=False, size=11, underline=False):
    r = p.add_run(text)
    r.bold, r.italic, r.underline = bold, italic, underline
    r.font.size = Pt(size)
    r.font.name = FONT
    r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    return r


def para(doc, text="", bold=False, size=11, align=None, after=4, before=0, italic=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_after, pf.space_before, pf.line_spacing = Pt(after), Pt(before), 1.0
    if align:
        p.alignment = align
    if text:
        run(p, text, bold=bold, size=size, italic=italic)
    return p


def heading(doc, text):
    return para(doc, text, bold=True, size=13, before=12, after=4)


def sub(doc, text):
    return para(doc, text, bold=True, size=11, before=6, after=2)


def body(doc, text):
    p = para(doc, text, after=6)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p


def bullets(doc, items, bold_lead=True):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.0
        if bold_lead and ": " in item:
            lead, rest = item.split(": ", 1)
            run(p, lead + ": ", bold=True)
            run(p, rest)
        else:
            run(p, item)


def numbered(doc, items):
    for item in items:
        p = doc.add_paragraph(style="List Number")
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.0
        run(p, item)


def cell_text(cell, text, bold=False, size=10, align=None):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    if align:
        p.alignment = align
    run(p, text, bold=bold, size=size)


# ----------------------------------------------------------------------------- document
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.left_margin = sec.right_margin = Inches(0.75)
sec.top_margin = sec.bottom_margin = Inches(0.75)
normal = doc.styles["Normal"]
normal.font.name, normal.font.size = FONT, Pt(11)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

# ---- page 1: header box
hdr = doc.add_table(rows=2, cols=2)
set_cell_border(hdr)
hdr.alignment = WD_TABLE_ALIGNMENT.CENTER
hdr.columns[0].width = Inches(1.55)
hdr.columns[1].width = Inches(5.45)
for r in hdr.rows:
    r.cells[0].width, r.cells[1].width = Inches(1.55), Inches(5.45)
logo_cell = hdr.cell(0, 0)
logo_cell.text = ""
lp = logo_cell.paragraphs[0]
lp.alignment = WD_ALIGN_PARAGRAPH.CENTER
lp.add_run().add_picture(str(HERE / "logo_0.png"), width=Inches(1.25))
tc = hdr.cell(0, 1)
tc.text = ""
p = tc.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(0)
run(p, "PimpriChinchwad Education Trust’s ", size=10)
run(p, "PimpriChinchwad College of Engineering (PCCoE)", bold=True, size=10)
run(p, " (An Autonomous Institute)", size=10)
p2 = tc.add_paragraph()
p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p2, "Affiliated to SavitribaiPhule Pune University(SPPU)", size=10)
bottom = hdr.cell(1, 0).merge(hdr.cell(1, 1))
cell_text(bottom, "MDM-Digital Marketing - Capstone Project [BCE27MD06]", bold=True, size=10,
          align=WD_ALIGN_PARAGRAPH.CENTER)
bottom.paragraphs[0].runs[0].underline = True

para(doc, after=6)
meta = doc.add_table(rows=2, cols=3)
meta.alignment = WD_TABLE_ALIGNMENT.CENTER
vals = [[f"Department: {HEADER['department']}", f"Academic Year: {HEADER['academic_year']}", f"Semester: {HEADER['semester']}"],
        [f"Year: {HEADER['year']}", f"Group ID: {HEADER['group_id']}", f"Date: {HEADER['date']}"]]
for i, row in enumerate(vals):
    for j, v in enumerate(row):
        cell_text(meta.cell(i, j), v, bold=True, size=11,
                  align=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT][j])
        meta.cell(i, j).paragraphs[0].paragraph_format.space_after = Pt(6)

para(doc, after=4)
p = para(doc, after=10)
run(p, "Problem Statement: ", bold=True)
run(p, TITLE, bold=True)

para(doc, "SDG Goals aligned with the project:", bold=True, after=6)
sdg = doc.add_table(rows=1 + len(SDGS), cols=2)
set_cell_border(sdg)
sdg.alignment = WD_TABLE_ALIGNMENT.CENTER
for r in sdg.rows:
    r.cells[0].width, r.cells[1].width = Inches(1.8), Inches(4.9)
cell_text(sdg.cell(0, 0), "SDG No.", bold=True)
cell_text(sdg.cell(0, 1), "Name", bold=True)
for i, (n, name) in enumerate(SDGS, start=1):
    cell_text(sdg.cell(i, 0), n)
    cell_text(sdg.cell(i, 1), name)

para(doc, after=12)
para(doc, "Team Members:", bold=True, after=6)
cols = ["PRN No", "Name of Student", "Department", "Mail-id", "Contact No.", "Signature"]
widths = [0.95, 1.55, 1.15, 1.35, 1.0, 1.0]
tm = doc.add_table(rows=1 + len(TEAM), cols=len(cols))
set_cell_border(tm)
tm.alignment = WD_TABLE_ALIGNMENT.CENTER
for r in tm.rows:
    for c, w in zip(r.cells, widths):
        c.width = Inches(w)
for j, c in enumerate(cols):
    cell_text(tm.cell(0, j), c, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
for i, member in enumerate(TEAM, start=1):
    for j, v in enumerate(member):
        cell_text(tm.cell(i, j), v)
    tm.rows[i].height = Inches(0.3)

para(doc, after=18)
p = para(doc)
run(p, "Project Guide: ", bold=True)
run(p, HEADER["guide"], bold=True)
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

# ---- 1) Introduction
heading(doc, "1) Introduction")
sub(doc, "Background of the Selected Business/Domain")
body(doc, "Customers rarely buy a product after a single interaction with a brand. A typical online purchase is preceded by "
          "several touchpoints across different digital channels: a person may first see a social media advertisement, later "
          "search for the product on Google, open a promotional email, return to the website directly and only then complete "
          "the purchase. Businesses of every size now spend across search, social, display, email and referral channels at the "
          "same time, yet they usually see only the final sale and not the path that led to it.")
sub(doc, "Role of Digital Marketing")
body(doc, "Digital marketing makes these interactions measurable. Every advertising platform reports impressions, clicks, "
          "spend and conversions, and web analytics tools record the channel through which each visit arrives. Marketing "
          "attribution uses this data to decide how much credit each channel deserves for a conversion. The answer directly "
          "shapes budget decisions: a channel that receives little credit is often cut, even when it plays an important role "
          "earlier in the customer journey.")
sub(doc, "Motivation")
body(doc, "Most ad platforms report conversions using their own view, typically last-click, so several platforms can claim "
          "the same sale while channels that start journeys appear to contribute little. Advanced attribution tools exist, "
          "but they are usually tied to a single platform or require paid subscriptions, and small businesses rarely have "
          "the analytical skills to interpret them. The motivation of this project is to study, with real public data, how "
          "much a channel's apparent value depends on the attribution rule used, and to turn these methods into a free, "
          "easy-to-use tool with an AI assistant that explains the results in plain language.")

# ---- 2) Literature / Market Review
heading(doc, "2) Literature / Market Review")
sub(doc, "Research Paper 1 – Multichannel Conversion Attribution")
body(doc, "Li and Kannan (2014) developed an empirical model of how customers consider and visit a firm's online channels "
          "before converting, using individual-level touchpoint data, and validated it with a field experiment. The study shows "
          "that the contribution of channels estimated by the model differs considerably from what simple metrics such as last "
          "click suggest, because channels influence each other through carryover and spillover effects. This directly "
          "supports our research question on whether channel importance changes under different attribution approaches.")
sub(doc, "Research Paper 2 – Data-Driven Multi-Touch Attribution")
body(doc, "Shao and Li (2011) proposed data-driven multi-touch attribution models that learn the contribution of each "
          "advertising channel from both converting and non-converting user histories, instead of relying on fixed rules. "
          "They also argued that an attribution model should be judged on both accuracy and stability. This work motivates "
          "the inclusion of data-driven models (Shapley value) alongside rule-based models in our project, and our use of "
          "stability checks such as bootstrap confidence intervals.")
sub(doc, "Research Paper 3 – Graph-Based (Markov) Attribution")
body(doc, "Anderl, Becker, von Wangenheim and Schumann (2016) introduced a graph-based framework that represents customer "
          "journeys as Markov chains and measures each channel's importance through its removal effect, that is, how much the "
          "probability of conversion falls when the channel is removed. Applied to large customer-journey datasets, the "
          "framework showed that common heuristic models misallocate credit. Our project implements this Markov removal-effect "
          "model as one of its two data-driven attribution methods.")
sub(doc, "Research Paper 4 – Predicting Purchase Intention from Session Behaviour")
body(doc, "Sakar, Polat, Katircioglu and Kastro (2019) used clickstream and session information from an online store to "
          "predict whether a visit will end in a purchase, comparing several machine-learning classifiers. Their work, and the "
          "public UCI dataset released with it, shows that session behaviour such as pages viewed, time spent and page value is "
          "strongly associated with purchase. We use this dataset to study which visitor and session characteristics are "
          "associated with conversion.")
sub(doc, "Research Paper 5 – Attribution in Display Advertising")
body(doc, "Diemert, Meynet, Galland and Lefortier (2017) studied attribution modelling for real-time bidding in display "
          "advertising and released the Criteo attribution dataset of 16.5 million impressions. Their work shows that taking "
          "attribution into account improves advertising efficiency, and the dataset allows us to study how credit is spread "
          "across repeated advertising exposures and how often last-click credit misses earlier impressions.")
sub(doc, "Existing Market Solutions")
body(doc, "Google Analytics 4 offers attribution reports including a data-driven model, Google Ads and Meta Ads Manager each "
          "report conversions attributed to their own campaigns, and commercial multi-touch attribution platforms combine data "
          "from several sources. These tools are useful, but each platform naturally reports from its own perspective, the "
          "multi-source tools are paid, and none of them explain their results in plain language for a small business owner.")

# ---- 3) Gap Identification
heading(doc, "3) Gap Identification")
sub(doc, "Existing Solutions Provide")
body(doc, "Existing tools and research provide several useful capabilities:")
bullets(doc, [
    "Ad platform reports (Google Ads, Meta Ads Manager) provide spend, clicks and conversions for their own campaigns.",
    "Web analytics tools provide traffic-source information and, in some cases, built-in attribution reports.",
    "Academic research provides rule-based and data-driven attribution models and conversion-prediction methods.",
    "Commercial attribution platforms provide cross-channel views for businesses that can pay for them.",
], bold_lead=False)
sub(doc, "Limitations of Existing Practices")
body(doc, "Each ad platform measures performance from its own perspective, usually with last-click logic, so the same sale "
          "is claimed several times and channels that start customer journeys are undervalued. Cross-channel attribution "
          "tools are usually paid or tied to one ecosystem. Research models are rarely available in a form a small business "
          "can use, and even when numbers are available, owners often do not know what action to take.")
sub(doc, "Identified Gap")
body(doc, "The gap is therefore not the absence of attribution methods, but the absence of a free, transparent, "
          "research-backed tool that compares several attribution models on a business's own data, shows how much the choice "
          "of model changes the answer, and explains the results in plain language.")
sub(doc, "How the Proposed Project Addresses the Gap")
body(doc, "The project first studies multi-channel journeys, attribution and conversion behaviour on public datasets. It then "
          "packages the same methods into ChannelTrace, a free web application where a business uploads a Google Ads, Meta Ads "
          "or customer-journey CSV and receives an insight dashboard, a side-by-side comparison of seven attribution models and "
          "an AI assistant that answers questions from the computed results. The proposed analysis flow is:")
para(doc, "Upload / Collect Data → Clean → Reconstruct Journeys → Compare Attribution Models → Analyse Conversion → "
          "Explain with AI Assistant", bold=True, after=6)

# ---- 4) Problem Statement
heading(doc, "4) Problem Statement")
body(doc, "Customers interact with several digital marketing channels before purchasing, but businesses usually measure "
          "channel performance with single-platform, last-click reports. As a result, budget decisions may favour channels "
          "that close sales and undervalue channels that start customer journeys. Existing cross-channel attribution tools "
          "are often paid or difficult for small businesses to use and interpret.")
body(doc, "The project aims to analyse multi-channel customer journeys using public digital marketing and e-commerce data, "
          "compare how different attribution models assign conversion credit, identify behaviours associated with conversion, "
          "and deliver these methods as a free plug-and-play dashboard with an AI assistant for businesses.")
body(doc, "Target Users: Small and medium businesses running online advertising, digital marketers and marketing students.")

# ---- 5) Objectives
heading(doc, "5) Objectives")
numbered(doc, [
    "To collect, clean and document public datasets on web analytics, advertising and online shopping behaviour.",
    "To reconstruct customer journeys and identify common channel paths that lead to a purchase.",
    "To compare seven attribution models (first touch, last touch, linear, time decay, position based, Markov chain and "
    "Shapley value) and measure how channel credit changes between them.",
    "To identify visitor and session behaviours associated with conversion using statistical tests and machine learning.",
    "To develop a free plug-and-play dashboard that analyses Google Ads, Meta Ads and customer-journey CSV files.",
    "To develop an AI assistant that answers questions and suggests actions using only the computed results.",
    "To evaluate the tool for correctness, usability and assistant accuracy, and to document the work as a research paper.",
])

# ---- 6) Scope
heading(doc, "6) Scope of the Project")
bullets(doc, [
    "Data Collection and Preparation: Use the Google Analytics 360 sample, UCI Online Shoppers, Criteo Attribution and "
    "Facebook Ad Campaign datasets, each for the question it can support; clean and document every step.",
    "Customer Journey Analysis: Order each visitor's sessions by time and identify the most common paths to purchase.",
    "Attribution Modelling: Implement and compare five rule-based and two data-driven attribution models.",
    "Conversion Analysis: Compare converting and non-converting sessions and model which factors are associated with buying.",
    "Insight Dashboard: Present research findings and analyse uploaded Google Ads, Meta Ads or journey CSV files.",
    "AI Assistant: Answer questions in plain language from computed results only, working offline or with a free AI model.",
    "Evaluation: Check output correctness, run a usability survey (SUS) and measure the assistant's accuracy.",
])

# ---- 7) Tools and Technologies
heading(doc, "7) Tools and Technologies")
bullets(doc, [
    "Python, Pandas and NumPy: For data cleaning, journey reconstruction and analysis.",
    "SciPy and scikit-learn: For statistical tests, attribution models and machine-learning classifiers.",
    "Google BigQuery (free sandbox): For querying the Google Analytics 360 sample dataset.",
    "Streamlit and Plotly: For the interactive dashboard and charts.",
    "Generative AI (Google Gemini free tier) and TF-IDF retrieval: For the AI assistant, with an offline mode.",
    "GitHub and Streamlit Community Cloud: For version control and free hosting of the application.",
    "Power BI / Looker Studio: For an additional business-intelligence style dashboard (planned).",
])
body(doc, "All tools used are free or open source, so the project has no cost.")

# ---- 8) Proposed Methodology
heading(doc, "8) Proposed Methodology")
body(doc, "The project will follow a step-by-step research and development approach:")
para(doc, "1. Data Collection → 2. Data Cleaning → 3. Exploratory Analysis → 4. Journey Reconstruction → 5. Attribution "
          "Modelling → 6. Conversion Analysis → 7. Tool Development → 8. Evaluation → 9. Research Paper", bold=True, after=6)
body(doc, "First, the public datasets will be collected and cleaned, and each will be matched to the research question it "
          "can genuinely answer. Customer journeys will then be reconstructed from the Google Analytics 360 sample, and "
          "seven attribution models will be applied and compared. The attribution code will be validated on synthetic "
          "journeys with a known correct answer, by checking that every model distributes exactly the total number of "
          "conversions, and with bootstrap confidence intervals. Conversion behaviour will be studied with Mann-Whitney U "
          "and chi-square tests and with logistic regression and random forest models evaluated by ROC-AUC.")
body(doc, "The same methods will then be packaged into the ChannelTrace web application and AI assistant. Finally, the tool "
          "will be evaluated for correctness on real Facebook advertising data, for usability through a System Usability "
          "Scale survey, and for the accuracy of the assistant's answers, and the findings will be written up as a research paper.")

# ---- 9) Result and Discussion
heading(doc, "9) Result and Discussion")
body(doc, "Preliminary results on the UCI Online Shoppers dataset (12,205 sessions after removing duplicates) show an overall "
          "conversion rate of 15.6 percent. New visitors convert at 24.9 percent against 14.1 percent for returning visitors, "
          "although returning visitors make up 85 percent of sessions. Conversion peaks in November at 25.5 percent. Buyers "
          "view a median of 29 product pages against 16 for non-buyers, and all ten behavioural measures differ significantly. "
          "A random forest predicts conversion with a ROC-AUC of 0.78 from early-session behaviour (0.93 when the PageValues "
          "feature, which partly reflects the outcome, is included).")
body(doc, "A working prototype of the dashboard and AI assistant has been developed. On the real Facebook Ad Campaign data it "
          "finds that 10 percent of spend went to ad sets with no approved conversions. On synthetic test journeys with known "
          "channel roles, the data-driven attribution models correctly identify that last-click reporting under-credits "
          "channels that start journeys and over-credits channels that close them.")
body(doc, "The expected final result is a comparison of how channel credit changes across attribution models on real "
          "multi-channel data, a set of plain-language findings for marketers, and an evaluated, free tool that businesses can "
          "use on their own data. All findings will be presented as associations, not proof that a channel caused a sale.")

# ---- 10) Conclusion
heading(doc, "10) Conclusion")
body(doc, "The proposed project studies how customers move across digital channels before buying and how strongly the choice "
          "of attribution model affects the credit each channel receives. By combining public-data research with a free "
          "plug-and-play dashboard and an AI assistant, the project connects academic attribution methods with practical "
          "marketing decisions.")
body(doc, "The approach is feasible because it relies on publicly available datasets and free tools, and it is measurable "
          "through clear evaluation criteria. Overall, the project helps businesses look beyond single-platform, last-click "
          "reports and make better-informed decisions about where to spend their marketing budget.")

# ---- 11) References
heading(doc, "11) References")
refs = [
    ("H. Li and P. K. Kannan, “Attributing conversions in a multichannel online marketing environment: An empirical model "
     "and a field experiment,” ", "Journal of Marketing Research", ", vol. 51, no. 1, pp. 40–56, 2014."),
    ("X. Shao and L. Li, “Data-driven multi-touch attribution models,” in ", "Proceedings of the 17th ACM SIGKDD "
     "International Conference on Knowledge Discovery and Data Mining", ", pp. 258–264, 2011."),
    ("E. Anderl, I. Becker, F. von Wangenheim, and J. H. Schumann, “Mapping the customer journey: Lessons learned from "
     "graph-based online attribution modeling,” ", "International Journal of Research in Marketing", ", vol. 33, no. 3, "
     "pp. 457–474, 2016."),
    ("C. O. Sakar, S. O. Polat, M. Katircioglu, and Y. Kastro, “Real-time prediction of online shoppers’ purchasing "
     "intention using multilayer perceptron and LSTM recurrent neural networks,” ", "Neural Computing and Applications",
     ", vol. 31, pp. 6893–6908, 2019."),
    ("E. Diemert, J. Meynet, P. Galland, and D. Lefortier, “Attribution modeling increases efficiency of bidding in display "
     "advertising,” in ", "Proceedings of the AdKDD and TargetAd Workshop, KDD", ", 2017."),
    ("Google, “BigQuery sample dataset for Google Analytics 360 (google_analytics_sample),” ", "Google Analytics Help", "."),
    ("Criteo AI Lab, “Criteo Attribution Modeling for Bidding Dataset,” ", "Criteo AI Lab", "."),
    ("Kaggle, “Sales Conversion Optimization (Facebook ad campaign data),” ", "Kaggle Datasets", "."),
    ("J. Brooke, “SUS: A quick and dirty usability scale,” in ", "Usability Evaluation in Industry", ", Taylor & Francis, "
     "pp. 189–194, 1996."),
]
for i, (a, ital, b) in enumerate(refs, start=1):
    p = para(doc, after=5)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run(p, f"[{i}] ", bold=True)
    run(p, a)
    run(p, ital, italic=True)
    run(p, b)

# ---- Guide approval
para(doc, "Guide Approval", bold=True, after=10).paragraph_format.page_break_before = True
p = para(doc, after=10)
run(p, "Project Guide Name: ", bold=True)
run(p, HEADER["guide"])
para(doc, "Signature:", bold=True, after=10)
para(doc, "Date:", bold=True, after=10)

doc.save(OUT)
print("saved", OUT)

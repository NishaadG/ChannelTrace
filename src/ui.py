"""Shared look for ChannelTrace: typography, palette, page furniture and the Plotly template."""
from html import escape

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

INK = "#16213A"        # headings, primary text
TEXT = "#2B3345"
MUTED = "#6A7285"
RULE = "#DCE1E8"
PAPER = "#E9EDF3"      # page (cool grey-blue tint)
PANEL = "#FFFFFF"      # cards
SIDEBAR = "#14213D"    # navy
NAVY_2 = "#1B2B4F"
GOLD = "#C9A227"       # sparing highlight on navy
HEAD_BG = "#F4F6F9"
ACCENT = "#1F4E8C"     # the one data accent
ACCENT_SOFT = "#E7EDF6"
BAR_MUTED = "#C8CDD6"
GOOD, PENDING = "#2F6B4F", "#8A6414"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400&family=Source+Serif+4:opsz,wght@8..60,500;8..60,600&display=swap');

html, body, [class*="st-"], .stMarkdown, .stText, button, input, textarea {{
  font-family: 'IBM Plex Sans', system-ui, sans-serif;
}}
.stApp {{ background: {PAPER}; color: {TEXT}; }}
[data-testid="stIconMaterial"], .material-symbols-rounded {{ font-family: 'Material Symbols Rounded' !important; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stDecoration"], [data-testid="stToolbar"] {{ display: none; }}
[data-testid="stMainBlockContainer"] {{ max-width: 1180px; padding-top: 2.6rem; padding-bottom: 4rem; }}

h1, h2, h3, h4 {{ font-family: 'Source Serif 4', Georgia, serif !important; color: {INK} !important; letter-spacing: -0.01em; }}
p, li {{ color: {TEXT}; }}

/* Sidebar */
[data-testid="stSidebar"] {{ background: {SIDEBAR}; border-right: none; }}
[data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] [data-testid="stIconMaterial"] {{ color: #C3CDE0; }}
[data-testid="stSidebar"] [data-testid="stNavSectionHeader"], [data-testid="stSidebar"] [data-testid="stNavSectionHeader"] span {{ color: #7F93B8 !important; font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase; font-weight: 600; }}
[data-testid="stSidebarNav"] a:hover {{ background: {NAVY_2}; }}
[data-testid="stSidebarCollapseButton"] span, [data-testid="stSidebarCollapseButton"] svg {{ color: #C3CDE0; fill: #C3CDE0; }}
[data-testid="stSidebarContent"] {{ display: flex; flex-direction: column; }}
[data-testid="stSidebarHeader"] {{ order: 0; height: 1.2rem; min-height: 0; padding: 0; }}
[data-testid="stSidebarUserContent"] {{ order: 1; padding-top: 0.4rem; padding-bottom: 0; }}
[data-testid="stSidebarNav"] {{ order: 2; }}
[data-testid="stSidebarNavSeparator"] {{ display: none; }}
[data-testid="stSidebarNav"] a span {{ font-size: 0.92rem; }}
[data-testid="stSidebarNav"] a[aria-current="page"] {{ background: {NAVY_2}; box-shadow: inset 3px 0 0 {GOLD}; }}
[data-testid="stSidebarNav"] a[aria-current="page"] span {{ color: #FFFFFF !important; }}
.ct-brand {{ padding: 0.2rem 0 1.1rem 0; border-bottom: 1px solid #2A3A5E; margin-bottom: 0.6rem; }}
.ct-brand .name {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 1.4rem; font-weight: 600; color: #FFFFFF; }}
.ct-brand .name b {{ color: {GOLD}; font-weight: 600; }}
.ct-brand .tag {{ font-size: 0.78rem; color: #8FA0C0 !important; margin-top: 0.15rem; line-height: 1.35; }}
.ct-sidefoot {{ position: fixed; bottom: 1.2rem; font-size: 0.74rem; color: #7F93B8 !important; line-height: 1.5; }}

/* Page header */
.ct-header {{ background: {SIDEBAR}; border-radius: 8px; padding: 2rem 2.2rem 2.1rem 2.2rem; margin-bottom: 1.6rem;
  background-image: linear-gradient(90deg, {SIDEBAR} 0%, {SIDEBAR} 62%, {NAVY_2} 100%); border-bottom: 3px solid {GOLD}; }}
.ct-eyebrow {{ font-size: 0.72rem; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase; color: {GOLD}; margin-bottom: 0.45rem; }}
.ct-title {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 2.25rem; font-weight: 600; color: #FFFFFF !important; line-height: 1.15; margin: 0; }}
.ct-lead {{ font-size: 1rem; color: #C3CDE0 !important; max-width: 780px; line-height: 1.6; margin: 0.75rem 0 0 0; }}

/* Section label */
.ct-section {{ display: flex; align-items: baseline; gap: 0.75rem; margin: 2rem 0 0.9rem 0; }}
.ct-section .code {{ font-size: 0.72rem; font-weight: 600; letter-spacing: 0.1em; color: {ACCENT}; text-transform: uppercase; }}
.ct-section .text {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 1.3rem; font-weight: 600; color: {INK}; }}

/* Stat cards */
.ct-stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0; border: 1px solid {RULE}; background: {PANEL}; border-radius: 6px; margin-bottom: 1.6rem; }}
.ct-stat {{ padding: 1.05rem 1.2rem; border-right: 1px solid {RULE}; }}
.ct-stat:last-child {{ border-right: none; }}
.ct-stat .label {{ font-size: 0.78rem; color: {MUTED}; }}
.ct-stat .value {{ font-size: 1.75rem; font-weight: 500; color: {INK}; font-variant-numeric: tabular-nums; margin-top: 0.2rem; }}
.ct-stat .note {{ font-size: 0.76rem; color: {MUTED}; margin-top: 0.15rem; }}

/* Cards */
.ct-card {{ background: {PANEL}; border: 1px solid {RULE}; border-radius: 6px; padding: 1.25rem 1.3rem; height: 100%; }}
.ct-card .num {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 0.95rem; color: {ACCENT}; font-weight: 600; }}
.ct-card .head {{ font-weight: 600; color: {INK}; font-size: 1.02rem; margin: 0.25rem 0 0.4rem 0; }}
.ct-card .body {{ font-size: 0.88rem; color: {MUTED}; line-height: 1.55; }}
.ct-card ul {{ margin: 0.5rem 0 0 1rem; padding: 0; }}
.ct-card li {{ font-size: 0.88rem; color: {TEXT}; margin-bottom: 0.25rem; }}

/* Badges */
.ct-badge {{ display: inline-block; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.04em; padding: 0.12rem 0.5rem; border-radius: 3px; border: 1px solid; white-space: nowrap; }}
.ct-badge.good {{ color: {GOOD}; border-color: #BFD5C8; background: #EFF5F1; }}
.ct-badge.pending {{ color: {PENDING}; border-color: #E3D2A8; background: #FAF5E8; }}
.ct-badge.neutral {{ color: {MUTED}; border-color: {RULE}; background: {HEAD_BG}; }}
.ct-badge.bad {{ color: #9A3B26; border-color: #E7C3B8; background: #FBF0EC; }}
.ct-badge.info {{ color: {ACCENT}; border-color: #C3D2E8; background: {ACCENT_SOFT}; }}

/* Tables */
.ct-table {{ width: 100%; border-collapse: collapse; background: {PANEL}; border: 1px solid {RULE}; border-radius: 6px; overflow: hidden; font-size: 0.88rem; }}
.ct-table th {{ text-align: left; font-weight: 600; font-size: 0.72rem; letter-spacing: 0.06em; text-transform: uppercase; color: #E4E9F2; padding: 0.7rem 1rem; border-bottom: 1px solid {RULE}; background: {NAVY_2}; }}
.ct-table td {{ padding: 0.75rem 1rem; border-bottom: 1px solid {RULE}; color: {TEXT}; vertical-align: top; }}
.ct-table tr:last-child td {{ border-bottom: none; }}
.ct-table td.code {{ font-weight: 600; color: {ACCENT}; white-space: nowrap; width: 3.5rem; }}
.ct-table td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.ct-table th.num {{ text-align: right; }}

/* Finding callout */
.ct-finding {{ border-left: 3px solid {ACCENT}; background: {PANEL}; padding: 0.95rem 1.2rem; margin: 0.6rem 0 1rem 0; border-radius: 0 6px 6px 0; border-top: 1px solid {RULE}; border-right: 1px solid {RULE}; border-bottom: 1px solid {RULE}; }}
.ct-finding .k {{ font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: {ACCENT}; }}
.ct-finding .t {{ font-size: 0.95rem; color: {TEXT}; line-height: 1.6; margin-top: 0.25rem; }}
.ct-code {{ font-family: 'IBM Plex Mono', ui-monospace, monospace; font-size: 0.82em; background: {HEAD_BG}; padding: 0.08rem 0.35rem; border-radius: 3px; color: {INK}; }}
.ct-note {{ font-size: 0.8rem; color: {MUTED}; line-height: 1.55; }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{ gap: 1.6rem; border-bottom: 1px solid {RULE}; }}
.stTabs [data-baseweb="tab"] {{ padding: 0.6rem 0; font-weight: 500; color: {MUTED}; }}
.stTabs [aria-selected="true"] {{ color: {INK}; }}
.stTabs [data-baseweb="tab-highlight"] {{ background: {ACCENT}; }}

/* Chart frames */
[data-testid="stPlotlyChart"] {{ background: {PANEL}; border: 1px solid {RULE}; border-radius: 6px; padding: 0.6rem 0.4rem 0.2rem 0.4rem; }}

/* Expander, buttons, chat */
[data-testid="stExpander"] details {{ border: 1px solid {RULE}; border-radius: 6px; background: {PANEL}; }}
.stButton button {{ border-radius: 4px; border: 1px solid {RULE}; background: {PANEL}; color: {TEXT}; font-size: 0.86rem; justify-content: flex-start; padding: 0.55rem 0.9rem; }}
.stButton button:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
[data-testid="stChatMessage"] {{ background: {PANEL}; border: 1px solid {RULE}; border-radius: 6px; padding: 0.9rem 1rem; }}
[data-testid="stChatInput"] textarea {{ font-size: 0.95rem; }}
</style>
"""


def _template() -> go.layout.Template:
    t = go.layout.Template()
    t.layout = go.Layout(
        font=dict(family="IBM Plex Sans, system-ui, sans-serif", size=12, color=TEXT),
        title=dict(font=dict(family="IBM Plex Sans, sans-serif", size=14, color=INK), x=0.01, xanchor="left"),
        paper_bgcolor=PANEL, plot_bgcolor=PANEL,
        colorway=[ACCENT, BAR_MUTED],
        xaxis=dict(showgrid=False, linecolor=RULE, ticks="", tickfont=dict(color=MUTED), title_font=dict(color=MUTED, size=11)),
        yaxis=dict(showgrid=True, gridcolor="#EFEDE7", zeroline=False, linecolor=RULE, tickfont=dict(color=MUTED),
                   title_font=dict(color=MUTED, size=11)),
        hoverlabel=dict(bgcolor=INK, font=dict(color="white", family="IBM Plex Sans, sans-serif", size=12), bordercolor=INK),
        margin=dict(l=12, r=28, t=52, b=12),
        bargap=0.38,
    )
    return t


def apply() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    pio.templates["channeltrace"] = _template()
    pio.templates.default = "channeltrace"
    with st.sidebar:
        st.markdown('<div class="ct-brand"><div class="name">Channel<b>Trace</b></div>'
                    '<div class="tag">Multi-channel attribution &amp;<br>conversion research</div></div>',
                    unsafe_allow_html=True)


def sidebar_footer() -> None:
    with st.sidebar:
        st.markdown('<div class="ct-sidefoot">MDM Digital Marketing Capstone<br>BCE27MD06 · 2026–27</div>',
                    unsafe_allow_html=True)


def header(eyebrow: str, title: str, lead: str = "") -> None:
    lead_html = f'<p class="ct-lead">{lead}</p>' if lead else ""
    st.markdown(f'<div class="ct-header"><div class="ct-eyebrow">{eyebrow}</div>'
                f'<h1 class="ct-title">{title}</h1>{lead_html}</div>', unsafe_allow_html=True)


def section(code: str, text: str) -> None:
    st.markdown(f'<div class="ct-section"><span class="code">{code}</span><span class="text">{text}</span></div>',
                unsafe_allow_html=True)


def stats(items: list[tuple[str, str, str]]) -> None:
    """items: (label, value, note)."""
    cells = "".join(f'<div class="ct-stat"><div class="label">{escape(l)}</div><div class="value">{escape(v)}</div>'
                    f'<div class="note">{escape(n)}</div></div>' for l, v, n in items)
    st.markdown(f'<div class="ct-stats">{cells}</div>', unsafe_allow_html=True)


def finding(text: str, label: str = "Finding") -> None:
    st.markdown(f'<div class="ct-finding"><div class="k">{label}</div><div class="t">{text}</div></div>',
                unsafe_allow_html=True)


def badge(text: str, kind: str = "neutral") -> str:
    return f'<span class="ct-badge {kind}">{escape(text)}</span>'


def card(num: str, head: str, body: str, extra: str = "") -> str:
    return (f'<div class="ct-card"><div class="num">{num}</div><div class="head">{head}</div>'
            f'<div class="body">{body}</div>{extra}</div>')


def note(text: str) -> None:
    st.markdown(f'<p class="ct-note">{text}</p>', unsafe_allow_html=True)

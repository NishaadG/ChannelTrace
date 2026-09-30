import io
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src import ads, attribution, ui

SAMPLES = Path(__file__).resolve().parent.parent / "data" / "samples"
AD_SAMPLES = {
    "Facebook Ads · real anonymised data (Kaggle, 1,143 ads)": "facebook_ads_kaggle.csv",
    "Google Ads · synthetic sample (6 campaigns, 60 days)": "google_ads_synthetic_sample.csv",
}
JOURNEY_SAMPLES = {"Customer journeys · synthetic sample (4,000 users)": "journeys_synthetic_sample.csv"}
VERDICT_KIND = {"Scale candidate": "good", "On track": "info", "Expensive": "bad", "No conversions": "bad"}
BAD = "#B4533C"
GRID = "#EEF1F5"

st.session_state.setdefault("data_facts", {})


@st.cache_data(show_spinner=False)
def run_ads(raw: bytes):
    df, platform, mapping = ads.load(raw)
    return df, platform, mapping, ads.summarise(df)


@st.cache_data(show_spinner="Rebuilding journeys and running seven attribution models")
def run_journeys(raw: bytes):
    paths = attribution.build_paths(attribution.load(io.BytesIO(raw)))
    return paths, attribution.attribute(paths), attribution.journey_stats(paths)


def pick_input(key: str, samples: dict, help_text: str):
    c1, c2 = st.columns([3, 2], gap="medium")
    up = c1.file_uploader(help_text, type=["csv", "tsv", "txt"], key=f"{key}_up")
    choice = c2.selectbox("Or try a sample file", ["None"] + list(samples), key=f"{key}_sample")
    if up is not None:
        return up.getvalue(), up.name
    if choice != "None":
        return (SAMPLES / samples[choice]).read_bytes(), choice
    return None, None


def money(x):
    return "–" if pd.isna(x) else f"{x:,.2f}"


def cpa_colour(verdict):
    if verdict in ("Expensive", "No conversions"):
        return BAD
    return ui.ACCENT if verdict == "Scale candidate" else ui.BAR_MUTED


ui.header(
    "Tools · Your data",
    "Run the analysis on your own numbers",
    "Upload an export from Google Ads, Meta Ads Manager or your analytics tool. ChannelTrace recognises the format, "
    "builds the dashboard and passes the results to the assistant. Files stay in this session and are not stored.",
)

tab_ads, tab_journey = st.tabs(["Ad performance", "Customer journeys and attribution"])

# ---------------------------------------------------------------- Ad performance
with tab_ads:
    raw, name = pick_input("ads", AD_SAMPLES, "Upload a Google Ads or Meta Ads CSV export")
    if raw is None:
        ui.finding("Export a campaign, ad set or ad report as CSV. Google Ads: Campaigns → Download → CSV. "
                   "Meta: Ads Manager → Reports → Export table data → CSV. Needed columns: campaign, cost or amount "
                   "spent, clicks and conversions (or results); impressions, conversion value, date, age and gender "
                   "are used when present.", label="What to upload")
    else:
        try:
            df, platform, mapping, s = run_ads(raw)
        except Exception as e:
            st.error(f"Could not read this file. {e}")
            st.stop()
        st.session_state.data_facts["ads"] = ads.fact_sheet(s, platform)
        t, camp = s["totals"], s["campaigns"]

        n_rows, n_camps = f"{s['rows']:,} rows", f"{len(camp)} campaigns"
        st.markdown(f"{ui.badge('Detected: ' + platform, 'info')} &nbsp; {ui.badge(n_rows)} &nbsp; {ui.badge(n_camps)}",
                    unsafe_allow_html=True)
        if "synthetic" in name.lower():
            ui.note("This sample is synthetic: generated to look like a Google Ads export, not real business data.")
        st.write("")
        items = [("Spend", money(t["spend"]), f"{t['impressions']:,.0f} impressions"),
                 ("Conversions", f"{t['conversions']:,.0f}", f"{t['cvr']:.2%} of clicks"),
                 ("Cost per acquisition", money(t["cpa"]), "spend ÷ conversions"),
                 ("Click-through rate", f"{t['ctr']:.2%}", f"CPC {money(t['cpc'])}")]
        if s["has_revenue"]:
            items.append(("Return on ad spend", f"{t['roas']:.2f}x", f"revenue {money(t['revenue'])}"))
        ui.stats(items)

        ui.finding(f"<strong>{s['zero_conv_share']:.1%} of spend ({money(s['zero_conv_spend'])})</strong> went to "
                   f"{s['zero_conv_groups']} {s['waste_unit']} that produced no conversions. That is the first place to look "
                   "for savings.", label="Spend with no return")

        c1, c2 = st.columns(2, gap="medium")
        share = camp.assign(conv_share=camp["conversions"] / camp["conversions"].sum()).head(10).iloc[::-1]
        fig = go.Figure()
        fig.add_bar(y=share["campaign"], x=share["spend_share"], name="Share of spend", orientation="h",
                    marker_color=ui.BAR_MUTED, hovertemplate="%{y}: %{x:.1%} of spend<extra></extra>")
        fig.add_bar(y=share["campaign"], x=share["conv_share"], name="Share of conversions", orientation="h",
                    marker_color=ui.ACCENT, hovertemplate="%{y}: %{x:.1%} of conversions<extra></extra>")
        fig.update_layout(title_text="Share of spend vs share of conversions", barmode="group",
                          height=380, legend=dict(orientation="h", y=-0.12, x=0), bargap=0.3, bargroupgap=0.08)
        fig.update_xaxes(tickformat=".0%", showgrid=True, gridcolor=GRID)
        fig.update_yaxes(showgrid=False, type="category")
        c1.plotly_chart(fig, use_container_width=True)

        cpa = camp.dropna(subset=["cpa"]).head(10).sort_values("cpa")
        fig = px.bar(cpa, x="cpa", y="campaign", orientation="h")
        fig.update_traces(marker_color=[cpa_colour(v) for v in cpa["verdict"]],
                          hovertemplate="%{y}: CPA %{x:,.2f}<extra></extra>")
        fig.add_vline(x=t["cpa"], line_dash="dot", line_color=ui.INK, line_width=1,
                      annotation_text=f"account CPA {money(t['cpa'])}", annotation_position="top",
                      annotation_font=dict(size=11, color=ui.MUTED))
        fig.update_layout(title_text="Cost per acquisition by campaign", height=380, xaxis_title=None, yaxis_title=None)
        fig.update_xaxes(showgrid=True, gridcolor=GRID)
        fig.update_yaxes(showgrid=False, type="category")
        c2.plotly_chart(fig, use_container_width=True)
        ui.note("Blue: well below the account CPA, a candidate to scale. Red: well above it, or no conversions. "
                "Grey: within the normal range.")

        ui.section("Campaigns", "Performance and verdict")
        roas_cell = lambda r: (f"<td class='num'>{'–' if pd.isna(r.roas) else f'{r.roas:.2f}x'}</td>"
                               if s["has_revenue"] else "")
        rows = "".join(
            f"<tr><td><strong>{r.campaign}</strong></td><td class='num'>{money(r.spend)}</td>"
            f"<td class='num'>{r.spend_share:.0%}</td><td class='num'>{r.clicks:,.0f}</td>"
            f"<td class='num'>{r.conversions:,.0f}</td><td class='num'>{money(r.cpa)}</td>"
            f"<td class='num'>{'–' if pd.isna(r.cvr) else f'{r.cvr:.1%}'}</td>{roas_cell(r)}"
            f"<td>{ui.badge(r.verdict, VERDICT_KIND[r.verdict])}</td></tr>" for r in camp.itertuples())
        roas_h = "<th class='num'>ROAS</th>" if s["has_revenue"] else ""
        st.markdown("<table class='ct-table'><thead><tr><th>Campaign</th><th class='num'>Spend</th><th class='num'>Share</th>"
                    "<th class='num'>Clicks</th><th class='num'>Conv.</th><th class='num'>CPA</th><th class='num'>CVR</th>"
                    f"{roas_h}<th>Verdict</th></tr></thead><tbody>{rows}</tbody></table>", unsafe_allow_html=True)
        ui.note("Verdicts compare each campaign's CPA with the account average: below 75% is a scale candidate, "
                "above 150% is expensive.")

        segs = [d for d in ("age", "gender") if d in s]
        if segs:
            ui.section("Audience", "Which segments convert cheaply")
            cols = st.columns(len(segs), gap="medium")
            for col, d in zip(cols, segs):
                seg = s[d]
                fig = px.bar(seg, x=d, y="cpa", text_auto=",.2f")
                fig.update_traces(marker_color=[ui.ACCENT if v == seg["cpa"].min() else ui.BAR_MUTED for v in seg["cpa"]],
                                  textposition="outside", cliponaxis=False, textfont=dict(size=11, color=ui.MUTED),
                                  hovertemplate="%{x}: CPA %{y:,.2f}<extra></extra>")
                fig.update_layout(title_text=f"Cost per acquisition by {d}", height=320, xaxis_title=None, yaxis_title=None)
                fig.update_xaxes(type="category")
                col.plotly_chart(fig, use_container_width=True)

        if "daily" in s:
            ui.section("Trend", "Daily spend and conversions")
            d = s["daily"]
            c1, c2 = st.columns(2, gap="medium")
            for col, y, title in [(c1, "spend", "Spend per day"), (c2, "conversions", "Conversions per day")]:
                fig = px.line(d, x="date", y=y)
                fig.update_traces(line_color=ui.ACCENT, line_width=2, hovertemplate="%{x|%d %b}: %{y:,.0f}<extra></extra>")
                fig.update_layout(title_text=title, height=280, xaxis_title=None, yaxis_title=None)
                col.plotly_chart(fig, use_container_width=True)

        acts = [l for l in st.session_state.data_facts["ads"].splitlines() if l.startswith("ACTION")]
        if acts:
            body = acts[0].split(":", 1)[1].strip()
            ui.finding("<br>".join(f"– {a.strip().rstrip('.')}." for a in body.split(";")), label="Suggested next steps")
        st.page_link("views/assistant.py", label="Ask the assistant about this data", icon=":material/arrow_forward:")

        with st.expander("Columns detected"):
            st.markdown("  \n".join(f"**{k}** ← `{v}`" for k, v in mapping.items()))

# ---------------------------------------------------------------- Journeys
with tab_journey:
    raw, name = pick_input("journey", JOURNEY_SAMPLES,
                           "Upload a journey CSV with columns user_id, timestamp, channel, converted")
    if raw is None:
        ui.finding("One row per touchpoint: <span class='ct-code'>user_id, timestamp, channel, converted</span>. "
                   "Set converted to 1 on the touch just before a purchase and 0 elsewhere. GA4 exports, CRM logs "
                   "or UTM-tagged visit logs can all be reshaped into this format.", label="What to upload")
    else:
        try:
            paths, table, jst = run_journeys(raw)
        except Exception as e:
            st.error(f"Could not read this file. {e}")
            st.stop()
        st.session_state.data_facts["journeys"] = attribution.fact_sheet(table, jst)
        if "synthetic" in name.lower():
            ui.note("This sample is synthetic: journeys generated with known channel roles to demonstrate and test the "
                    "attribution models. Social and Display were built to start journeys; Email and Paid Search to close them.")
        ui.stats([
            ("Journeys", f"{jst['journeys']:,}", f"{len(table)} channels"),
            ("Conversions", f"{jst['conversions']:,}", f"{jst['conv_rate']:.1%} of journeys"),
            ("Touches before buying", f"{jst['avg_len_conv']:.1f}", f"vs {jst['avg_len_nonconv']:.1f} for non-buyers"),
            ("Single-touch conversions", f"{jst['single_touch_share']:.0%}", "the rest need an attribution rule"),
        ])

        share = table / table.sum()
        share = share.loc[share["Markov chain"].sort_values(ascending=False).index]
        fig = go.Figure(go.Heatmap(
            z=share.values, x=list(share.columns), y=list(share.index), colorscale=[[0, "#F4F6F9"], [1, "#86A6D4"]],
            text=[[f"{v:.0%}" for v in row] for row in share.values], texttemplate="%{text}",
            textfont=dict(size=12, color=ui.INK), hovertemplate="%{y} · %{x}: %{z:.1%} of credit<extra></extra>", showscale=False,
            xgap=2, ygap=2))
        fig.update_layout(title_text="Share of conversion credit by channel and attribution model", height=410,
                          margin=dict(t=92))
        fig.update_xaxes(side="top", showgrid=False)
        fig.update_yaxes(autorange="reversed", showgrid=False)
        st.plotly_chart(fig, use_container_width=True)

        diff = (share["Markov chain"] - share["Last touch"]).sort_values()
        c1, c2 = st.columns([3, 2], gap="medium")
        fig = go.Figure()
        for ch in diff.index:
            fig.add_trace(go.Scatter(x=[share.loc[ch, "Last touch"], share.loc[ch, "Markov chain"]], y=[ch, ch],
                                     mode="lines", line=dict(color=ui.BAR_MUTED, width=2), showlegend=False,
                                     hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=share.loc[diff.index, "Last touch"], y=diff.index, mode="markers", name="Last touch",
                                 marker=dict(size=11, color="#9AA1AE"),
                                 hovertemplate="%{y}: %{x:.1%} (last touch)<extra></extra>"))
        fig.add_trace(go.Scatter(x=share.loc[diff.index, "Markov chain"], y=diff.index, mode="markers", name="Markov chain",
                                 marker=dict(size=11, color=ui.ACCENT),
                                 hovertemplate="%{y}: %{x:.1%} (Markov)<extra></extra>"))
        fig.update_layout(title_text="Last-click credit vs data-driven credit", height=360,
                          legend=dict(orientation="h", y=-0.12, x=0))
        fig.update_xaxes(tickformat=".0%", showgrid=True, gridcolor=GRID)
        fig.update_yaxes(showgrid=False)
        c1.plotly_chart(fig, use_container_width=True)
        with c2:
            under, over = diff.index[-1], diff.index[0]
            ui.finding(f"Last-click gives <strong>{under}</strong> {share.loc[under, 'Last touch']:.0%} of the credit, but "
                       f"the data-driven Markov model gives it {share.loc[under, 'Markov chain']:.0%}: it does more work early "
                       f"in journeys than last-click shows. <strong>{over}</strong> is the opposite, at "
                       f"{share.loc[over, 'Last touch']:.0%} under last-click against {share.loc[over, 'Markov chain']:.0%} "
                       "under Markov.", label="Last-click bias")
            rows = "".join(f"<tr><td>{p}</td><td class='num'>{n}</td></tr>" for p, n in jst["top_paths"].head(6).items())
            st.markdown(f"<table class='ct-table'><thead><tr><th>Most common converting paths</th>"
                        f"<th class='num'>Journeys</th></tr></thead><tbody>{rows}</tbody></table>", unsafe_allow_html=True)

        st.page_link("views/assistant.py", label="Ask the assistant about these journeys", icon=":material/arrow_forward:")
        with st.expander("How each model assigns credit"):
            st.markdown(
                "- **First touch / Last touch**: all credit to the first or last interaction.\n"
                "- **Linear**: credit split equally across every interaction.\n"
                "- **Time decay**: more credit to interactions closer to the purchase (7-day half-life).\n"
                "- **Position based**: 40% first, 40% last, 20% shared across the middle.\n"
                "- **Markov chain** (data-driven): how much the conversion rate falls if a channel is removed from all "
                "journeys (Anderl et al., 2016).\n"
                "- **Shapley value** (data-driven): each channel's average marginal contribution across all combinations "
                "of channels (Shao & Li, 2011).\n\n"
                "Every model distributes exactly the total number of conversions. There is no single correct model; "
                "comparing them shows how much a channel's apparent value depends on the rule used."
            )

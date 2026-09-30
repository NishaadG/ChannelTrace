import plotly.express as px
import streamlit as st

from src import ui
from src.state import research

f = research()


def bar(df, x, y, highlight, title, horizontal=False):
    """Single-series bar: highlighted bars in the accent, the rest muted, values labelled."""
    colors = [ui.ACCENT if h else ui.BAR_MUTED for h in highlight]
    fig = px.bar(df, x=y if horizontal else x, y=x if horizontal else y,
                 orientation="h" if horizontal else "v", text_auto=".1%")
    fig.update_traces(marker_color=colors, marker_line_width=0, textposition="outside", cliponaxis=False,
                      textfont=dict(size=11, color=ui.MUTED),
                      hovertemplate=("%{y}: %{x:.1%}" if horizontal else "%{x}: %{y:.1%}") + "<extra></extra>")
    fig.update_layout(title_text=title, height=350, xaxis_title=None, yaxis_title=None)
    if horizontal:
        fig.update_xaxes(tickformat=".0%", showgrid=True, gridcolor="#EFEDE7", range=[0, df[y].max() * 1.14])
        fig.update_yaxes(showgrid=False)
    else:
        fig.update_yaxes(tickformat=".0%")
    return fig


ui.header(
    "Research findings · UCI Online Shoppers",
    "What separates a visit that converts",
    f"{f['sessions']:,} sessions from one year of an online store (Sakar &amp; Kastro, 2018). "
    "Channel journey and attribution results from the Google Analytics 360 sample and Criteo will follow.",
)

v = f["visitor"].set_index("VisitorType")["conversion_rate"]
mo, mw = f["models"]["without_page_values"], f["models"]["with_page_values"]
peak = f["month"].loc[f["month"]["conversion_rate"].idxmax()]
ui.stats([
    ("Overall conversion rate", f"{f['conversion_rate']:.1%}", f"{f['df']['Revenue'].sum():,} purchasing sessions"),
    ("New visitors", f"{v['New_Visitor']:.1%}", f"vs {v['Returning_Visitor']:.1%} for returning visitors"),
    ("Peak month", f"{peak['Month']}", f"{peak['conversion_rate']:.1%} conversion rate"),
    ("Model accuracy (ROC-AUC)", f"{mo['rf_auc']:.2f}", "early-session signals only"),
])

tab_who, tab_when, tab_how, tab_model = st.tabs(
    ["Who converts", "When they convert", "RQ2 · How buyers behave", "RQ4 · What predicts a purchase"])

with tab_who:
    c1, c2 = st.columns(2, gap="medium")
    vis = f["visitor"].replace({"VisitorType": {"New_Visitor": "New", "Returning_Visitor": "Returning"}})
    c1.plotly_chart(bar(vis, "VisitorType", "conversion_rate", vis["conversion_rate"] == vis["conversion_rate"].max(),
                        "Conversion rate by visitor type"), use_container_width=True)
    t = f["traffic"].assign(TrafficType=lambda d: "Source " + d["TrafficType"].astype(str)).iloc[::-1]
    c2.plotly_chart(bar(t, "TrafficType", "conversion_rate", t["conversion_rate"] >= t["conversion_rate"].nlargest(3).min(),
                        "Conversion rate by traffic source", horizontal=True), use_container_width=True)
    returning_share = f["visitor"].set_index("VisitorType").loc["Returning_Visitor", "sessions"] / f["sessions"]
    ui.finding(f"Returning visitors make up {returning_share:.0%} of traffic but convert at only "
               f"{v['Returning_Visitor']:.1%}, against {v['New_Visitor']:.1%} for new visitors. The returning group "
               "is the largest re-engagement opportunity. Conversion also varies almost five-fold between traffic sources, "
               "though the dataset codes sources as numbers rather than named channels.")

with tab_when:
    m = f["month"].assign(Month=lambda d: d["Month"].astype(str))
    st.plotly_chart(bar(m, "Month", "conversion_rate", m["conversion_rate"] == m["conversion_rate"].max(),
                        "Conversion rate by month"), use_container_width=True)
    w = f["weekend"].set_index("Weekend")["conversion_rate"]
    ui.finding(f"Conversion peaks in November at {m['conversion_rate'].max():.1%}, ahead of the holiday season, and is "
               f"lowest in February at {m.set_index('Month').loc['Feb', 'conversion_rate']:.1%}. Weekend sessions convert "
               f"only slightly better than weekdays ({w[True]:.1%} against {w[False]:.1%}), so season matters far more "
               "than day of the week.")
    ui.note("January and April are not present in the dataset.")

with tab_how:
    g = f["groups"].set_index("Behaviour")
    order = ["Product pages viewed", "Time on product pages (s)", "Account/admin pages viewed", "Info pages viewed",
             "Bounce rate", "Exit rate", "Page value"]
    pval = lambda p: "&lt; 1e-300" if p == 0 else f"{p:.1e}"
    fmt = lambda b, x: f"{x / 60:.1f} min" if "(s)" in b else (f"{x:.3f}" if "rate" in b else f"{x:,.1f}")
    rows = "".join(
        f"<tr><td>{b.replace(' (s)', '')}</td><td class='num'>{fmt(b, g.loc[b, 'Mean (converted)'])}</td>"
        f"<td class='num'>{fmt(b, g.loc[b, 'Mean (not converted)'])}</td>"
        f"<td class='num'>{pval(g.loc[b, 'p-value'])}</td></tr>" for b in order)
    st.markdown("<table class='ct-table'><thead><tr><th>Behaviour (mean per session)</th><th class='num'>Converted</th>"
                "<th class='num'>Not converted</th><th class='num'>p-value</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>", unsafe_allow_html=True)
    ui.note("Two-sided Mann-Whitney U test. All ten behaviours measured differ at p &lt; 0.05; seven are shown.")
    st.write("")
    df = f["df"].assign(Outcome=lambda d: d["Revenue"].map({True: "Converted", False: "Not converted"}),
                        minutes=lambda d: d["ProductRelated_Duration"] / 60 + 0.1)
    fig = px.box(df, x="minutes", y="Outcome", log_x=True, points=False, color="Outcome",
                 color_discrete_map={"Converted": ui.ACCENT, "Not converted": "#9AA1AE"})
    fig.update_layout(title_text="Time on product pages per session", showlegend=False, height=270,
                      xaxis_title="Minutes (log scale)", yaxis_title=None)
    fig.update_xaxes(showgrid=True, gridcolor="#EFEDE7")
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True)
    ui.finding(f"Buying sessions view a median of {g.loc['Product pages viewed', 'Median (converted)']:.0f} product pages "
               f"against {g.loc['Product pages viewed', 'Median (not converted)']:.0f}, spend about twice as long on them, "
               "and bounce and exit far less. Depth of product browsing is the clearest behavioural sign of purchase intent.")

with tab_model:
    ui.stats([
        ("With PageValues", f"{mw['rf_auc']:.3f}", "random forest, ROC-AUC"),
        ("Without PageValues", f"{mo['rf_auc']:.3f}", "random forest, ROC-AUC"),
        ("Logistic regression", f"{mo['logit_auc']:.3f}", "without PageValues"),
    ])
    imp = mo["importance"].head(8).iloc[::-1].assign(feature=lambda d: d["feature"].str.replace(" (s)", "", regex=False))
    fig = px.bar(imp, x="importance", y="feature", orientation="h")
    fig.update_traces(marker_color=[ui.ACCENT if i >= len(imp) - 3 else ui.BAR_MUTED for i in range(len(imp))],
                      hovertemplate="%{y}: %{x:.4f}<extra></extra>")
    fig.update_layout(title_text="Strongest conversion signals, without PageValues", height=360,
                      xaxis_title="Drop in ROC-AUC when the feature is shuffled", yaxis_title=None)
    fig.update_xaxes(showgrid=True, gridcolor="#EFEDE7")
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True)
    ui.finding("PageValues is calculated from pages seen before a purchase, so it partly contains the answer; we report "
               "both models. Without it, time on product pages, exit rate and the November season carry most of the signal. "
               "For marketers, that points to landing paid traffic directly on product pages and reducing exits there.")

st.write("")
with st.expander("Method notes"):
    st.markdown(
        "- 125 exact-duplicate rows removed (12,330 → 12,205 sessions).\n"
        "- Group differences: Mann-Whitney U for numeric measures, chi-square for visitor type and month.\n"
        "- Models: logistic regression and random forest, stratified 75/25 split, class-balanced weights, "
        "evaluated by ROC-AUC on the held-out 25%.\n"
        "- Feature importance: permutation importance on the test set, 5 repeats.\n"
        "- All results are associations, not causal effects."
    )

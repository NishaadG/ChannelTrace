import plotly.express as px
import streamlit as st

from src.state import research

ACCENT, MUTED = "#2563EB", "#CBD5E1"
f = research()


def bar(df, x, y, highlight, title, horizontal=False, text_fmt=".1%"):
    """Single-series bar: one highlighted bar in the accent, the rest muted."""
    colors = [ACCENT if h else MUTED for h in highlight]
    fig = px.bar(df, x=y if horizontal else x, y=x if horizontal else y,
                 orientation="h" if horizontal else "v", text_auto=text_fmt)
    fig.update_traces(marker_color=colors, marker_line_width=0, textposition="outside", cliponaxis=False,
                      hovertemplate="%{x}: %{y:.1%}<extra></extra>" if not horizontal else "%{y}: %{x:.1%}<extra></extra>")
    fig.update_layout(title=dict(text=title, font_size=15), height=340, margin=dict(l=8, r=24, t=48, b=8),
                      plot_bgcolor="white", xaxis_title=None, yaxis_title=None, bargap=0.35)
    axis = fig.update_xaxes if horizontal else fig.update_yaxes
    axis(tickformat=".0%", showgrid=True, gridcolor="#EEF2F7", zeroline=False)
    return fig


st.title("Research Findings")
st.caption("Dataset: UCI Online Shoppers Purchasing Intention (Sakar & Kastro, 2018), one year of "
           "sessions on an online store. Criteo (attribution) and GA4 (journeys) results will be added here.")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Sessions analysed", f"{f['sessions']:,}")
k2.metric("Overall conversion rate", f"{f['conversion_rate']:.1%}")
v = f["visitor"].set_index("VisitorType")["conversion_rate"]
k3.metric("New vs returning conversion", f"{v['New_Visitor']:.1%} vs {v['Returning_Visitor']:.1%}")
mo = f["models"]["without_page_values"]
k4.metric("Prediction accuracy (AUC)", f"{mo['rf_auc']:.2f}", help="Random forest on early-session "
          "behaviour, without the PageValues feature. 0.5 = guessing, 1.0 = perfect.")

tab_who, tab_when, tab_how, tab_model = st.tabs(
    ["Who converts", "When they convert", "How converters behave (RQ2)", "What predicts conversion (RQ4)"])

with tab_who:
    c1, c2 = st.columns(2)
    vis = f["visitor"].replace({"VisitorType": {"New_Visitor": "New visitor", "Returning_Visitor": "Returning visitor"}})
    c1.plotly_chart(bar(vis, "VisitorType", "conversion_rate", vis["conversion_rate"] == vis["conversion_rate"].max(),
                        "New visitors convert far more often than returning ones"), use_container_width=True)
    t = f["traffic"].assign(TrafficType=lambda d: "Source " + d["TrafficType"].astype(str)).iloc[::-1]
    c2.plotly_chart(bar(t, "TrafficType", "conversion_rate", t["conversion_rate"] >= t["conversion_rate"].nlargest(3).min(),
                        "Conversion varies 5x across traffic sources", horizontal=True), use_container_width=True)
    returning_share = f["visitor"].set_index("VisitorType").loc["Returning_Visitor", "sessions"] / f["sessions"]
    st.info(f"**Takeaway.** Returning visitors are {returning_share:.0%} "
            f"of traffic but convert at only {v['Returning_Visitor']:.1%}. That group is the biggest re-engagement "
            "opportunity. Traffic sources are anonymised codes in this dataset, so the source chart shows spread, "
            "not named channels.", icon=":material/lightbulb:")

with tab_when:
    m = f["month"].assign(Month=lambda d: d["Month"].astype(str))
    st.plotly_chart(bar(m, "Month", "conversion_rate", m["conversion_rate"] == m["conversion_rate"].max(),
                        "November converts best, ahead of the holiday season"), use_container_width=True)
    w = f["weekend"].set_index("Weekend")["conversion_rate"]
    st.info(f"**Takeaway.** Conversion peaks in November ({m['conversion_rate'].max():.1%}) and is lowest in "
            f"February ({m.set_index('Month').loc['Feb','conversion_rate']:.1%}). Weekend sessions convert slightly better "
            f"({w[True]:.1%} vs {w[False]:.1%}). Timing campaigns around peak season matters more than day of week. "
            "January and April are missing from the dataset.", icon=":material/lightbulb:")

with tab_how:
    g = f["groups"].copy()
    show = g[["Behaviour", "Median (converted)", "Median (not converted)", "Mean (converted)", "Mean (not converted)", "p-value"]]
    st.markdown("**Converted vs not-converted sessions.** All ten behaviours differ significantly (Mann-Whitney U, p < 0.05).")
    st.dataframe(show.style.format({c: "{:,.3f}" for c in show.columns if c not in ("Behaviour", "p-value")} | {"p-value": "{:.1e}"}),
                 hide_index=True, use_container_width=True)
    df = f["df"].assign(Outcome=lambda d: d["Revenue"].map({True: "Converted", False: "Not converted"}),
                        minutes=lambda d: d["ProductRelated_Duration"] / 60 + 0.1)
    fig = px.box(df, x="minutes", y="Outcome", log_x=True, points=False, color="Outcome",
                 color_discrete_map={"Converted": ACCENT, "Not converted": "#94A3B8"})
    fig.update_layout(title=dict(text="Buyers spend about twice as long on product pages", font_size=15),
                      showlegend=False, height=280, plot_bgcolor="white", margin=dict(l=8, r=24, t=48, b=8),
                      xaxis_title="Minutes on product pages (log scale)", yaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)
    gi = g.set_index("Behaviour")
    st.info(f"**Takeaway.** Converting sessions view a median of {gi.loc['Product pages viewed','Median (converted)']:.0f} product pages "
            f"(vs {gi.loc['Product pages viewed','Median (not converted)']:.0f}) and have much lower bounce and exit rates. "
            "Deep product browsing is the clearest behavioural sign of purchase intent.", icon=":material/lightbulb:")

with tab_model:
    mw = f["models"]["with_page_values"]
    a, b = st.columns(2)
    a.metric("AUC with PageValues", f"{mw['rf_auc']:.3f}")
    b.metric("AUC without PageValues", f"{mo['rf_auc']:.3f}", delta=f"{mo['rf_auc'] - mw['rf_auc']:.3f}")
    st.caption("PageValues is computed from pages seen before a transaction, so it partly leaks the outcome. "
               "We report both models. The one without it shows which early-session signals really matter.")
    imp = mo["importance"].head(8).iloc[::-1]
    fig = px.bar(imp, x="importance", y="feature", orientation="h")
    fig.update_traces(marker_color=[ACCENT if i >= len(imp) - 3 else MUTED for i in range(len(imp))],
                      hovertemplate="%{y}: %{x:.4f}<extra></extra>")
    fig.update_layout(title=dict(text="Top conversion signals (without PageValues)", font_size=15), height=340,
                      plot_bgcolor="white", margin=dict(l=8, r=24, t=48, b=8),
                      xaxis_title="Drop in AUC when the feature is shuffled", yaxis_title=None)
    fig.update_xaxes(showgrid=True, gridcolor="#EEF2F7")
    st.plotly_chart(fig, use_container_width=True)
    st.info("**Takeaway.** Time spent on product pages, exit rate and the November season carry most of the signal. "
            "For marketers, this suggests landing traffic straight onto product pages and reducing exits there.",
            icon=":material/lightbulb:")

with st.expander("Method notes"):
    st.markdown(
        "- 125 exact-duplicate rows removed (12,330 → 12,205 sessions).\n"
        "- Group differences: Mann-Whitney U (numeric), chi-square (visitor type, month).\n"
        "- Models: logistic regression and random forest, stratified 75/25 split, class-balanced weights, "
        "evaluated by ROC-AUC on the held-out 25%.\n"
        "- Importance: permutation importance on the test set (5 repeats).\n"
        "- All results are associations, not causal effects."
    )

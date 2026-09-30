import streamlit as st

from src import ui

ui.header(
    "Tools · Your data",
    "Run the analysis on your own numbers",
    "Export a report from your ad platform or analytics tool, upload it here, and ChannelTrace builds the dashboard. "
    "No account, no API setup, and nothing is stored.",
)
st.markdown(ui.badge("In development", "pending"), unsafe_allow_html=True)
st.write("")

c1, c2 = st.columns(2, gap="medium")
c1.markdown(ui.card(
    "A", "Ad performance export", "From Google Ads or Meta Ads Manager: one row per campaign, ad set or ad.",
    "<ul><li>Recognises Google and Meta column names automatically</li>"
    "<li>Spend, CTR, CPC, CPA, conversion rate and ROAS per campaign</li>"
    "<li>Flags spend with no return and campaigns worth scaling</li>"
    "<li>Assistant suggests where to move budget</li></ul>"), unsafe_allow_html=True)
c2.markdown(ui.card(
    "B", "Customer journey export", "From GA4, a CRM or UTM logs: <span class='ct-code'>user_id, timestamp, channel, converted</span>.",
    "<ul><li>Rebuilds each customer's path to purchase</li>"
    "<li>Seven attribution models side by side, including Markov chain and Shapley value</li>"
    "<li>Shows which channels last-click over- or under-credits</li>"
    "<li>Confidence ranges on every channel's share</li></ul>"), unsafe_allow_html=True)

st.write("")
ui.finding("Ad-platform exports hold totals per campaign, not individual paths, so they can show cost efficiency "
           "but not multi-touch attribution. Journey-level data is needed for that, which is why both formats are supported.",
           label="Why two formats")

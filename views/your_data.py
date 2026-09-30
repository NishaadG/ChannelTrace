import streamlit as st

st.title("Your Data")
st.info("Plug-and-play upload is the next milestone. This page shows what it will do.", icon=":material/construction:")

c1, c2 = st.columns(2)
with c1, st.container(border=True):
    st.markdown("**A. Ad performance CSV**")
    st.caption("Exported from Google Ads or Meta Ads Manager")
    st.markdown(
        "- Auto-detects Google / Meta column names\n"
        "- Spend, CTR, CPC, CPA, conversion rate, ROAS per campaign\n"
        "- Flags wasted spend and campaigns worth scaling\n"
        "- Assistant suggests budget moves"
    )
with c2, st.container(border=True):
    st.markdown("**B. Customer-journey CSV**")
    st.caption("From GA4 export, CRM or UTM logs: `user_id, timestamp, channel, converted`")
    st.markdown(
        "- Rebuilds each customer's path to purchase\n"
        "- Six attribution models side by side: first touch, last touch, linear, "
        "time decay, position based, Markov chain\n"
        "- Shows which channels are over- or under-credited by last-click"
    )
st.caption("Why two formats: ad-platform exports only hold campaign totals, so true multi-touch "
           "attribution needs journey-level data.")

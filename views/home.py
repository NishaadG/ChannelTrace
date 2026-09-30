import streamlit as st

st.title("ChannelTrace")
st.markdown("#### Multi-channel digital marketing attribution & conversion analysis")
st.write(
    "Customers rarely buy after one ad. They see a social post, search on Google, open an email, "
    "and only then purchase. ChannelTrace studies those journeys, compares how different attribution "
    "models share the credit, and turns the findings into plain-language advice."
)

c1, c2, c3 = st.columns(3)
with c1, st.container(border=True):
    st.markdown("**1 · Research Findings**")
    st.caption("What public e-commerce and advertising data says about journeys, attribution and conversion.")
    st.page_link("views/research.py", label="Open findings", icon=":material/insights:")
with c2, st.container(border=True):
    st.markdown("**2 · AI Assistant**")
    st.caption("Ask questions in plain English. Answers are grounded only in the computed results.")
    st.page_link("views/assistant.py", label="Ask the assistant", icon=":material/smart_toy:")
with c3, st.container(border=True):
    st.markdown("**3 · Your Data** · _coming next_")
    st.caption("Upload a Google Ads / Meta Ads export or a customer-journey CSV and get your own dashboard.")
    st.page_link("views/your_data.py", label="See what's planned", icon=":material/upload_file:")

st.divider()
st.markdown("##### Research questions")
st.markdown(
    "- **RQ1** What touchpoint journeys commonly come before a conversion?\n"
    "- **RQ2** How do converting and non-converting journeys differ?\n"
    "- **RQ3** Does a channel's importance change under different attribution models?\n"
    "- **RQ4** Which session and visitor characteristics are associated with conversion?\n"
    "- **RQ5** Can these methods give small businesses useful insight from their own ad data?"
)

st.markdown("##### Data sources")
st.dataframe(
    {
        "Dataset": ["UCI Online Shoppers Purchasing Intention", "Criteo Attribution Modeling for Bidding",
                    "Google Merchandise Store GA4 sample (BigQuery)"],
        "Used for": ["RQ2, RQ4: session behaviour vs conversion", "RQ3: attribution model comparison",
                     "RQ1: customer journeys by traffic source"],
        "Status": ["✅ Analysed", "⏳ In progress", "⏳ In progress"],
    },
    hide_index=True, use_container_width=True,
)
st.caption("Built entirely with free, open-source tools. Findings show associations, not proof of cause.")

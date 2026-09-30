import streamlit as st

from src import ui

ui.header(
    "Capstone research project · 2026–27",
    "Which channels really lead to a sale?",
    "Customers rarely buy after a single ad. They find a brand through search, come back through social, "
    "return directly and only then purchase. ChannelTrace reconstructs those journeys from public data, "
    "compares how attribution models divide the credit, and turns the results into advice a small business can act on.",
)

c1, c2, c3 = st.columns(3, gap="medium")
c1.markdown(ui.card("01", "Research findings",
                    "What public e-commerce and advertising data shows about journeys, attribution and conversion.",
                    f'<div style="margin-top:.9rem">{ui.badge("First results in", "good")}</div>'),
            unsafe_allow_html=True)
c2.markdown(ui.card("02", "Marketing assistant",
                    "Plain-language answers grounded only in the computed results, never in guesswork.",
                    f'<div style="margin-top:.9rem">{ui.badge("Prototype", "good")}</div>'),
            unsafe_allow_html=True)
c3.markdown(ui.card("03", "Your data",
                    "Upload a Google Ads, Meta Ads or customer-journey export and get the same analysis on your own numbers.",
                    f'<div style="margin-top:.9rem">{ui.badge("Working prototype", "good")}</div>'),
            unsafe_allow_html=True)
b1, b2, b3 = st.columns([1, 1, 1], gap="medium")
b1.page_link("views/research.py", label="Read the findings", icon=":material/arrow_forward:")
b2.page_link("views/assistant.py", label="Open the assistant", icon=":material/arrow_forward:")
b3.page_link("views/your_data.py", label="Analyse your data", icon=":material/arrow_forward:")

ui.section("Scope", "Research questions")
rqs = [
    ("RQ1", "What channel journeys commonly come before a conversion?", "GA360 sample", ("In progress", "pending")),
    ("RQ2", "How do converting and non-converting sessions differ?", "UCI Online Shoppers", ("Answered", "good")),
    ("RQ3", "Does a channel's importance change under different attribution models?", "GA360 sample, Criteo", ("In progress", "pending")),
    ("RQ4", "Which session and visitor characteristics are associated with conversion?", "UCI Online Shoppers", ("Answered", "good")),
    ("RQ5", "Can these methods give small businesses correct, usable insight from their own data?", "Facebook Ads (Kaggle), user study", ("Tool built", "pending")),
]
rows = "".join(f'<tr><td class="code">{c}</td><td>{q}</td><td>{d}</td><td>{ui.badge(*s)}</td></tr>' for c, q, d, s in rqs)
st.markdown(f'<table class="ct-table"><thead><tr><th></th><th>Question</th><th>Evidence</th><th>Status</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>', unsafe_allow_html=True)

ui.section("Evidence", "Data sources")
src = [
    ("Google Analytics 360 sample", "Google Merchandise Store, Aug 2016 – Aug 2017", "Multi-session journeys with named channels"),
    ("UCI Online Shoppers Purchasing Intention", "12,330 sessions, one year", "Session behaviour and purchase outcome"),
    ("Criteo Attribution Modeling for Bidding", "16.5M display impressions, 30 days", "Credit across repeated impressions; last-click gap"),
    ("Facebook Ad Campaign (Kaggle)", "1,143 ads, three campaigns", "Validating the upload tool on real ad data"),
]
rows = "".join(f"<tr><td><strong>{a}</strong><br><span class='ct-note'>{b}</span></td><td>{c}</td></tr>" for a, b, c in src)
st.markdown(f'<table class="ct-table"><thead><tr><th>Dataset</th><th>Used for</th></tr></thead><tbody>{rows}</tbody></table>',
            unsafe_allow_html=True)

st.write("")
ui.note("Built with free and open-source tools. Results describe associations in the data, not proof that a channel caused a sale.")

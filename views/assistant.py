import streamlit as st

from src import assistant, ui
from src.state import research

f = research()
data_facts = st.session_state.get("data_facts", {})
facts = "\n".join([f["facts"], *data_facts.values()])
backend = assistant.backend_name()
generative = not backend.startswith("Built-in")

ui.header(
    "Tools · Marketing assistant",
    "Ask the data",
    "Answers come only from ChannelTrace's computed results: the research findings and any file you analyse on the "
    "Your data page. Raw rows never leave the app, and every recommendation is a suggestion, not a guarantee.",
)
tags = [ui.badge(backend, "good" if generative else "info"), ui.badge("Research findings loaded", "neutral")]
if "ads" in data_facts:
    tags.append(ui.badge("Your ad data loaded", "good"))
if "journeys" in data_facts:
    tags.append(ui.badge("Your journey data loaded", "good"))
st.markdown(" &nbsp; ".join(tags), unsafe_allow_html=True)
if not generative:
    ui.note("The built-in model finds the most relevant computed facts for each question using TF-IDF text similarity, "
            "so it works offline with no key. Add a free Gemini or Groq key in "
            "<span class='ct-code'>.streamlit/secrets.toml</span> for full conversational answers.")

st.session_state.setdefault("chat", [])

SUGGESTIONS = ["Summarise the key research findings", "How can a store convert more returning visitors?",
               "When should we run our biggest campaigns?", "What are the limitations of this analysis?"]
if "ads" in data_facts:
    SUGGESTIONS = ["Which campaigns should I cut or scale?", "Where is money being wasted?",
                   "Which audience converts most cheaply?"] + SUGGESTIONS[:1]
if "journeys" in data_facts:
    SUGGESTIONS = ["Which channel does last-click undervalue?", "What are the most common paths to purchase?"] + SUGGESTIONS[:2]

if not st.session_state.chat and "pending" not in st.session_state:
    ui.section("Start with", "Suggested questions")
    cols = st.columns(2, gap="small")
    for i, s in enumerate(SUGGESTIONS):
        if cols[i % 2].button(s, use_container_width=True, key=f"sugg{i}"):
            st.session_state.pending = s
            st.rerun()

AVATAR = {"user": ":material/person:", "assistant": ":material/insights:"}
for m in st.session_state.chat:
    with st.chat_message(m["role"], avatar=AVATAR[m["role"]]):
        st.markdown(m["content"])

prompt = st.chat_input("Ask about campaigns, channels, audiences, timing or methods") or st.session_state.pop("pending", None)
if prompt:
    st.session_state.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=AVATAR["user"]):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar=AVATAR["assistant"]), st.spinner("Reading the results"):
        reply = assistant.answer(facts, st.session_state.chat[-10:])
        st.markdown(reply)
    st.session_state.chat.append({"role": "assistant", "content": reply})

if st.session_state.chat and st.button("Clear conversation", icon=":material/restart_alt:"):
    st.session_state.chat = []
    st.rerun()

st.write("")
with st.expander("What the assistant knows"):
    st.text(facts)

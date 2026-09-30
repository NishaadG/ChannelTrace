import streamlit as st

from src import assistant, ui
from src.state import research

f = research()
backend = assistant.backend_name()
live = not backend.startswith("Offline")

ui.header(
    "Tools · Marketing assistant",
    "Ask the data",
    "Questions are answered from ChannelTrace's computed results only. Raw data never leaves the app, "
    "and every recommendation is a suggestion, not a guarantee.",
)
st.markdown(f"{ui.badge(backend, 'good' if live else 'neutral')}", unsafe_allow_html=True)
if not live:
    ui.note("No API key configured, so answers quote the relevant findings directly. "
            "Add a free Gemini or Groq key in <span class='ct-code'>.streamlit/secrets.toml</span> for full answers.")

if "chat" not in st.session_state:
    st.session_state.chat = []

SUGGESTIONS = [
    "Summarise the key findings in three points",
    "How can a store convert more returning visitors?",
    "When should we run our biggest campaigns?",
    "What are the limitations of this analysis?",
]
if not st.session_state.chat:
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

prompt = st.chat_input("Ask about conversion, visitors, timing or methods") or st.session_state.pop("pending", None)
if prompt:
    st.session_state.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=AVATAR["user"]):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar=AVATAR["assistant"]), st.spinner("Reading the findings"):
        reply = assistant.answer(f["facts"], st.session_state.chat[-10:])
        st.markdown(reply)
    st.session_state.chat.append({"role": "assistant", "content": reply})

if st.session_state.chat and st.button("Clear conversation", icon=":material/restart_alt:"):
    st.session_state.chat = []
    st.rerun()

st.write("")
with st.expander("What the assistant knows"):
    st.text(f["facts"])

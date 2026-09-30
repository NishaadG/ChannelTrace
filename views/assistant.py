import streamlit as st

from src import assistant
from src.state import research

f = research()

st.title("AI Assistant")
st.caption(f"Backend: **{assistant.backend_name()}** · Answers are grounded only in ChannelTrace's computed "
           "results. Raw data is never sent to the AI.")

with st.expander("What the assistant knows (its fact sheet)"):
    st.text(f["facts"])

if "chat" not in st.session_state:
    st.session_state.chat = []

SUGGESTIONS = [
    "Summarise the key findings in 3 points",
    "How can a store improve conversion for returning visitors?",
    "When should we run our biggest campaigns?",
    "What are the limitations of this analysis?",
]
if not st.session_state.chat:
    cols = st.columns(len(SUGGESTIONS))
    for col, s in zip(cols, SUGGESTIONS):
        if col.button(s, use_container_width=True):
            st.session_state.pending = s
            st.rerun()

for m in st.session_state.chat:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("Ask about the findings...") or st.session_state.pop("pending", None)
if prompt:
    st.session_state.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"), st.spinner("Thinking..."):
        reply = assistant.answer(f["facts"], st.session_state.chat[-10:])
        st.markdown(reply)
    st.session_state.chat.append({"role": "assistant", "content": reply})

if st.session_state.chat and st.button("Clear chat", icon=":material/delete:"):
    st.session_state.chat = []
    st.rerun()

import streamlit as st

st.set_page_config(page_title="ChannelTrace", page_icon="🧭", layout="wide")

nav = st.navigation({
    "ChannelTrace": [st.Page("views/home.py", title="Overview", icon=":material/home:", default=True)],
    "Research": [st.Page("views/research.py", title="Research Findings", icon=":material/insights:")],
    "Tools": [
        st.Page("views/assistant.py", title="AI Assistant", icon=":material/smart_toy:"),
        st.Page("views/your_data.py", title="Your Data (upload)", icon=":material/upload_file:"),
    ],
})
nav.run()

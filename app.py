import streamlit as st

from src import ui

st.set_page_config(page_title="ChannelTrace", page_icon=":material/conversion_path:", layout="wide")
ui.apply()

nav = st.navigation({
    "": [st.Page("views/home.py", title="Overview", icon=":material/home:", default=True)],
    "Research": [st.Page("views/research.py", title="Findings", icon=":material/insights:")],
    "Tools": [
        st.Page("views/assistant.py", title="Assistant", icon=":material/forum:"),
        st.Page("views/your_data.py", title="Your data", icon=":material/upload_file:"),
    ],
})
ui.sidebar_footer()
nav.run()

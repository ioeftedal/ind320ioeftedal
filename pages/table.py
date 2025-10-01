# page2.py
import streamlit as st

st.write(st.session_state["shared"])  # If page1 already executed, this writes True

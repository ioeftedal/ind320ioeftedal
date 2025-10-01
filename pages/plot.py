# page1.py
import streamlit as st

if "shared" not in st.session_state:
    st.session_state["shared"] = True

import streamlit as st

ss = st.session_state


def init_state():
    if "submit" not in ss:
        ss["submit"] = False
    if "base_mode" not in ss:
        ss["base_mode"] = False
    if "full_data" not in ss:
        ss["full_data"] = True
    if "username" not in ss:
        ss["username"] = None
    if "history" not in ss:
        ss["history"] = []

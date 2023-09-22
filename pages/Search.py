import streamlit as st
import functions.gui as gui
import functions.friendtech as ft
import functions.utils as ut

ss = st.session_state

st.set_page_config(
    page_title="friend.tech Dashboard",
    page_icon="🐇",
    layout="wide"
)

# Initialize session state
ut.init_state()

# Disables Header and Footer, customizable over css, js and html
# You can cache css when calling them inside a function
gui.load_css_cache("footer")
gui.load_css_cache("header")

# Loads sidebar
with st.sidebar:
    progress = st.empty()
    gui.load_ft_df(ss["history"][:10], hide=True)
    gui.load_sidebar_ft()

# Header
st.header("friend.tech Dashboard")

# Columns for responsive Page layout and page structure
h_l_col, h_r_col = st.columns([1, 1])  # Columns header
left_col, right_col = st.columns([1, 1])  # Columns Search

with h_r_col:
    h_l_2_col, h_r_2_col, _ = st.columns([1, 2, 3])
    home = h_l_2_col.button("Home", on_click=ut.home(), help="Navigates or Refreshes Home.")
    refresh = h_r_2_col.button("Refresh/Reload User", on_click=ut.submit(), help="Refresh or Reloads last User-Profiles!")


# Submit Form to handle the submit process
with h_l_col.form(key="search", clear_on_submit=True):
    ss["username"] = st.text_input(label="Look up a Twitter-Handle or friend.tech wallet")
    button = st.form_submit_button("Search User", on_click=ut.submit())

# Search User
if button or refresh and ss.get("submit"):
    if ss["username"]:
        target = ss["username"]
        if len(target) == 42 and target.startswith("0x"):
            target_address = target.lower()
            target = ft.addr_to_user(target_address, convert=True)
        else:
            target_address = ft.user_to_addr(target)

        ss["username"] = target.lower()
        # runs only if wallet address gets returned
        if target_address and target_address != "N/A":
            if "history" in ss:
                for item in ss["history"]:
                    if item["History"] == target.lower():
                        ss["history"].remove(item)

                # Insert at the beginning of the list
                ss["history"].insert(0, {"History": target.lower()})
            gui.load_ft_stats(target_address.lower(), target, progress)
            progress.empty()

        else:
            with right_col:
                st.write("# USER NOT FOUND")

    ss["submit"] = False  # reset submit

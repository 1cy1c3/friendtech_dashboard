import streamlit as st
import functions.gui as gui
import functions.friendtech as ft
import functions.basescan as bs
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
    gui.load_ft_df(ss["history"], hide=True)
    gui.load_sidebar_ft()

# Header
st.header("friend.tech Dashboard")

# Columns for responsive Page layout and page structure
h_l_col, h_r_col = st.columns([1, 1])  # Columns header
left_col, right_col = st.columns([1, 1])  # Columns Search

# Load Status message
with h_r_col:
    gui.load_status()

# Button  and Toggle Columns
h_l_2_col, h_r_2_col = h_r_col.columns([1, 1])

home = h_l_2_col.button("Home", on_click=ut.home(), help="Navigates or Refreshes Home.")
refresh = h_r_2_col.button("Refresh/Reload User", on_click=ut.submit(), help="Refresh or Reloads last User-Profiles!")

with h_l_2_col:
    ss['base_mode'] = st.toggle("Base Scan Trending")

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
            for item in ss["history"]:
                if item["History"] == target.lower():
                    ss["history"].remove(item)

            # Insert at the beginning of the list
            ss["history"].insert(0, {"History": target.lower()})
            gui.load_ft_stats(target_address.lower(), target)

        else:
            with right_col:
                st.write("# USER NOT FOUND")

    ss["submit"] = False  # reset submit

# Friendtech General Data
elif not button and not refresh and not ss['base_mode']:
    with left_col:
        st.markdown("# Top 50")
        gui.load_ft_df(ft.get_top_50(), hide=False)
    with right_col:
        st.markdown("# Trending")
        gui.load_ft_df(ft.get_trending(), hide=False)
    st.markdown("")  # Spacer for columns
    st.markdown("# Global Activity")
    gui.load_ft_df(ft.get_global_activity(), hide=True)

# Display Base Scan data
elif ss['base_mode'] and not button and not refresh:
    winners, losers = bs.get_trending(st.secrets['friendtech_contract'])
    with left_col:
        st.markdown("# Trending Gaining 15 min")
        gui.load_ft_df(winners, hide=False)
    with right_col:
        st.markdown("# Trending Losing 15 min")
        gui.load_ft_df(losers, hide=False)

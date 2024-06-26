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
    h_l_2_col, h_m_2_col, h_r_2_col = st.columns([1, 1, 2])
    pfp_img = h_l_2_col.empty()
    refresh = h_m_2_col.button("Refresh/Reload User", on_click=ut.submit(),
                               help="Refresh or Reloads last User-Profiles!", use_container_width=True)
    base_scan = h_r_2_col.empty()
    twitter = h_r_2_col.empty()
    friendtech = h_r_2_col.empty()

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
            target, pfp = ft.addr_to_user(target_address, convert=True)

        else:
            target_address, pfp = ft.user_to_addr(target)

        ss["username"] = target.lower()

        # runs only if wallet address gets returned
        if target_address and target_address != "N/A":
            if "history" in ss:
                for item in ss["history"]:
                    if item["History"] == target.lower():
                        ss["history"].remove(item)

                # Insert at the beginning of the list
                ss["history"].insert(0, {"History": target.lower()})

            if pfp is not None:
                pfp_img.image(pfp, width=150)

            friendtech.link_button("friend.tech", url=f"https://friend.tech/{target.lower()}", use_container_width=True)
            twitter.link_button("Twitter", url=f"https://twitter.com/{target.lower()}", use_container_width=True)
            base_scan.link_button("Base Scan", url=f"https://basescan.org/address/{target_address}", use_container_width=True)

            with st.spinner("Loading Stats"):
                gui.load_ft_stats(target_address.lower(), target, progress)
            progress.empty()

        else:
            with right_col:
                st.write("# USER NOT FOUND")

    ss["submit"] = False  # reset submit

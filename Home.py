import streamlit as st
import functions.gui as gui
import functions.friendtech as ft
import functions.basescan as bs

ss = st.session_state

st.set_page_config(
    page_title="friend.tech Dashboard",
    page_icon="🐇",
    layout="wide"
)

# Initialize session state
if "submit" not in ss:
    ss["submit"] = False
    ss["base_mode"] = False


# Approve Submit
def submit():
    ss["submit"] = True


# Disables Header and Footer, customizable over css, js and html
# You can cache css when calling them inside a function
gui.load_css_cache("footer")
gui.load_css_cache("header")

# Loads sidebar
with st.sidebar:
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

home = h_l_2_col.button("Home")
ss['base_mode'] = h_l_2_col.toggle("Base Scan Trending")

# Submit Form to handle the submit process
with h_l_col.form(key="search", clear_on_submit=True):
    target = st.text_input(label="Look up a Twitter-Handle or friend.tech wallet")
    button = st.form_submit_button("Search User", on_click=submit())

# Friendtech General Data
if not button and not ss['base_mode']:
    with left_col:
        st.markdown("# Top 50")
        gui.load_ft_df(ft.get_top_50(), hide=False)
    with right_col:
        st.markdown("# Trending")
        gui.load_ft_df(ft.get_trending(), hide=False)
    st.markdown("")  # Spacer for columns
    st.markdown("# Global Activity")
    gui.load_ft_df(ft.get_global_activity(), hide=True)

# Search User
if button and ss.get("submit"):
    if len(target) == 42 and target.startswith("0x"):
        target_address = target.lower()
        target = ft.addr_to_user(target_address, convert=True)
    else:
        target_address = ft.user_to_addr(target)

    # runs only if wallet address gets returned
    if target_address and target_address != "N/A":
        activity = ft.get_personal_activity(target_address)
        key_activity, key_volume, share_price = ft.get_token_activity(target_address)
        with right_col:
            st.markdown("# Activity")
            gui.load_ft_df(activity, hide=True)

        st.markdown("# Key Activity")
        gui.load_ft_graph(share_price)
        gui.load_ft_df(key_activity, hide=True)

        with left_col:
            st.markdown(f"# {target}")
            st.write(f"**Wallet:** {target_address}")
            with st.spinner("Loading Stats"):
                gui.load_ft_stats(target_address)

    else:
        with right_col:
            st.write("User not found")

    ss["submit"] = False  # reset submit


# Display Base Scan data
elif ss['base_mode'] and not button:
    winners, losers = bs.get_trending(st.secrets['friendtech_contract'])
    with left_col:
        st.markdown("# Trending Gaining 15 min")
        gui.load_ft_df(winners, hide=False)
    with right_col:
        st.markdown("# Trending Losing 15 min")
        gui.load_ft_df(losers, hide=False)

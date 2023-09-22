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
    progress = st.empty()
    gui.load_ft_df(ss["history"][:10], hide=True)
    gui.load_sidebar_ft()

# Header
st.header("Home Page")

# Columns for responsive Page layout and page structure
h_l_col, h_r_col = st.columns([1, 1])  # Columns header
left_col, right_col = st.columns([1, 1])  # Columns Search
b_l_c, b_r_c = st.columns([1, 1])


# Load Status message
with h_r_col:
    gui.load_status()

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
winners, losers = bs.get_trending(st.secrets['friendtech_contract'])
with b_l_c:
    st.markdown("# Basescan Gaining 15 min")
    gui.load_ft_df(winners, hide=False)
with b_r_c:
    st.markdown("# Basescan Losing 15 min")
    gui.load_ft_df(losers, hide=False)

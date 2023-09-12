import streamlit as st
import functions.gui as gui
import functions.friendtech as ft
import functions.basescan as bs

from streamlit_login_auth_ui.widgets import __login__

ss = st.session_state


# Approve Submit
def submit():
    ss["submit"] = True


# Initialize session state
if "submit" not in ss:
    ss["submit"] = False
    ss["base_mode"] = False
    ss["full_data"] = False


st.set_page_config(
    page_title="friend.tech Dashboard",
    page_icon="🐇",
    layout="wide"
)

# Disables Header and Footer, customizable over css, js and html
# You can cache css when calling them inside a function
gui.load_css_cache("footer")
gui.load_css_cache("header")

# Header
st.header("friend.tech Dashboard")


__login__obj = __login__(auth_token="courier_auth_token",
                         nav_sidebar=False,
                         company_name="Shims",
                         width=200, height=250,
                         logout_button_name='Logout', hide_menu_bool=False,
                         hide_footer_bool=False,
                         lottie_url='https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json')

LOGGED_IN = __login__obj.build_login_ui()

# Loads sidebar
with st.sidebar:
    gui.load_sidebar_ft()

if LOGGED_IN is True:

    st.markdown(f"Welcome {name}")

    # Columns for responsive Page layout and page structure
    h_l_col, h_r_col = st.columns([1, 1])  # Columns header
    left_col, right_col = st.columns([1, 1])  # Columns Search

    # Load Status message
    with h_r_col:
        gui.load_status()

    # Button  and Toggle Columns
    h_l_2_col, h_r_2_col = h_r_col.columns([1, 1])

    home = h_l_2_col.button("Home")
    with h_l_2_col:
        ss['base_mode'] = st.toggle("Base Scan Trending")
        ss['full_data'] = st.toggle("Complete Price History")

    # Submit Form to handle the submit process
    with h_l_col.form(key="search", clear_on_submit=True):
        target = st.text_input(label="Look up a Twitter-Handle or friend.tech wallet")
        button = st.form_submit_button("Search User", on_click=submit())

    # Search User
    if button and ss.get("submit"):
        if len(target) == 42 and target.startswith("0x"):
            target_address = target.lower()
            target = ft.addr_to_user(target_address, convert=True)
        else:
            target_address = ft.user_to_addr(target)

        # runs only if wallet address gets returned
        if target_address and target_address != "N/A":
            gui.load_ft_stats(target_address, target)

        else:
            with right_col:
                st.write("# USER NOT FOUND")

        ss["submit"] = False  # reset submit

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

    # Display Base Scan data
    elif ss['base_mode'] and not button:
        winners, losers = bs.get_trending(st.secrets['friendtech_contract'])
        with left_col:
            st.markdown("# Trending Gaining 15 min")
            gui.load_ft_df(winners, hide=False)
        with right_col:
            st.markdown("# Trending Losing 15 min")
            gui.load_ft_df(losers, hide=False)
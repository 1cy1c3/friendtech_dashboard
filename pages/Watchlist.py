import streamlit as st
import functions.gui as gui
import functions.friendtech as ft
import functions.database as db
import functions.utils as ut

from streamlit_login_auth_ui.widgets import __login__

ss = st.session_state

ut.init_state()


# Approve Submit
def submit():
    ss["submit"] = True


st.set_page_config(
    page_title="friend.tech Dashboard",
    page_icon="🐇",
    layout="wide"
)

# Disables Header and Footer, customizable over css, js and html
# You can cache css when calling them inside a function
gui.load_css_cache("footer")
gui.load_css_cache("header")

st.header("Build your personal watchlist")
try:
    __login__obj = __login__(auth_token="courier_auth_token",
                             company_name="Shims",
                             width=200, height=250,
                             logout_button_name='Logout', hide_menu_bool=False,
                             hide_footer_bool=False,
                             lottie_url='https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json')
except Exception:
    st.error("Reload Page, if error persist, please contact me!")
    __login__obj = None

if __login__obj:
    LOGGED_IN = __login__obj.build_login_ui()

    # Loads sidebar
    with st.sidebar:
        gui.load_ft_df(ss["history"], hide=True)
        gui.load_sidebar_ft()

    if LOGGED_IN is True:
        try:
            username = __login__obj.get_username()
        except Exception:
            st.error("Reload Page, if error persist, please contact me!")
            username = None

        if username:
            header_l, header_r = st.columns([1, 1])

            with header_l:
                st.header(f"{username}'s Watchlist")
                st.button("Home")

            with header_r:
                # Submit Form to handle the submit process
                with st.form(key="search", clear_on_submit=True):
                    target = st.text_input(label="Look up a Twitter-Handle or friend.tech wallet")
                    button = st.form_submit_button("Search User", on_click=submit())

            target_name_list = []
            target_list = db.get_watchlist(username)

            left_col, right_col = st.columns([1, 1])  # Columns Search

            if button and ss.get("submit"):
                if len(target) == 42 and target.startswith("0x"):
                    target_address = target.lower()
                    target = ft.addr_to_user(target_address, convert=True)
                else:
                    target_address = ft.user_to_addr(target)

                # runs only if wallet address gets returned
                if target_address and target_address != "N/A":
                    add_remove = st.button("**+ / -** Watchlist", on_click=db.add_remove_wl(target_address, username))
                    gui.load_ft_stats(target_address, target, dashboard=True)

                else:
                    with right_col:
                        st.write("# USER NOT FOUND")
                ss["submit"] = False

            elif not button:
                if target_list:
                    for target_address in target_list:
                        target = ft.addr_to_user(target_address[0].lower(), convert=True)
                        target_name_list.append((target_address[0].lower(), target))

                    watchlist = ft.get_watchlist_activity(target_name_list)

                    st.markdown("# Activity [24h]")
                    st.dataframe(gui.filter_dataframe(watchlist), use_container_width=True, hide_index=True)

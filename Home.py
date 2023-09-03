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

# Initialize Submit
if "submit" not in ss:
    ss["submit"] = False
    ss["base_mode"] = False


# Approve Submit
def submit():
    ss["submit"] = True

locked = True
gui.load_header()
gui.load_footer()

with st.sidebar:
    gui.load_sidebar_ft()
    gui.load_button("ref_buttons")

st.header("friend.tech Dashboard")
h_l_col, h_r_col = st.columns([1, 1])
left_col, right_col = st.columns([1, 1])

with open("text/status.txt", "r") as f:
    status_txt = f.read()
h_r_col.write(status_txt)

h_l_2_col, h_r_2_col = h_r_col.columns([1, 1])

home = h_l_2_col.button("Home")
ss['base_mode'] = h_l_2_col.toggle("Base Scan Mode")

with h_l_col.form(key="search", clear_on_submit=True):
    target = st.text_input(label="Look up a Twitter-Handle or friend.tech wallet")
    button = st.form_submit_button("Search User", on_click=submit())

if not button and not ss['base_mode']:
    with left_col:
        st.markdown("# Top 50")
        gui.load_ft_top50()
    with right_col:
        st.markdown("# Trending")
        gui.load_ft_df(ft.get_trending(), hide=False)
    st.markdown("")  # Spacer for columns
    st.markdown("# Global Activity")
    gui.load_ft_df(ft.get_global_activity(), hide=True)


if button and ss.get("submit"):
    if len(target) == 42 and target.startswith("0x"):
        target_address = target.lower()
        target = ft.addr_to_user(target_address, convert=True)
    else:
        target_address = ft.user_to_addr(target)
    if target_address:  # and not ss['base_mode']:
        share_price = ft.get_share_price(target_address, target)
        activity = ft.get_personal_activity(target_address)
        key_activity, key_volume = ft.get_token_activity(target_address)

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
                stats = gui.load_ft_stats(target_address)

    elif target_address and ss['base_mode'] and not locked:
        with left_col:
            st.markdown(f"# {target}")
            st.write(f"**Wallet:** {target_address}")

        with st.spinner("Loading Stats"):
            share_price = gui.load_ft_stats(target_address)
            gui.load_ft_graph(share_price)

        with right_col:
            st.markdown("# Activity")
    else:
        with right_col:
            st.write("User not found")
    ss["submit"] = False

elif ss['base_mode'] and not button:
    winners, losers = bs.get_trending(st.secrets['friendtech_contract'])
    with left_col:
        st.markdown("# Trending Gaining 15 min")
        gui.load_ft_df(winners, hide=False)
    with right_col:
        st.markdown("# Trending Losing 15 min")
        gui.load_ft_df(losers, hide=False)

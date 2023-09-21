import streamlit as st
import functions.gui as gui
import functions.friendtech as ft
import functions.utils as ut

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

st.header(f"Get your Portfolio-Dump-Value")

header_l, header_r = st.columns([1, 1])
left_col, right_col = st.columns([1, 1])

# Loads sidebar
with st.sidebar:
    progress = st.empty()
    gui.load_ft_df(ss["history"], hide=True)
    gui.load_sidebar_ft()

with header_l:
    st.write("Drop in any friend.tech name and get a full portfolio breakdown!\nThis process might take some time,"
             " depending on the targets Portfolio")

with header_r:
    # Submit Form to handle the submit process
    with st.form(key="search", clear_on_submit=True):
        target = st.text_input(label="Look up a Twitter-Handle or friend.tech wallet")
        button = st.form_submit_button("Get Dump-Value", on_click=submit())

if button and ss.get("submit"):
    if len(target) == 42 and target.startswith("0x"):
        target_address = target.lower()
        target = ft.addr_to_user(target_address, convert=True)
    else:
        target_address = ft.user_to_addr(target)

    # runs only if wallet address gets returned
    if target_address and target_address != "N/A":
        progress.progress(value=0, text="Loading Stats")
        with st.spinner("Getting Account Balance"):
            portfolio_value, _ = ft.get_portfolio_value(target_address)
        progress.progress(value=33, text="Loading Stats")
        with st.spinner("Getting Account Portfolio"):
            portfolio = ft.get_holdings(target_address)
        progress.progress(value=67, text="Loading Stats")
        with st.spinner("Collection Portfolio Data"):
            dump_data, dump_value = ft.get_dump_values(portfolio, target_address.lower())
        progress.progress(value=100, text="Completed")

        progress.empty()

        left_col.markdown(f"# {target}'s Portfolio-Value:\n# {portfolio_value} ETH")
        right_col.markdown(f"# {target}'s Total Dump-Value:\n# {dump_value} ETH")
        gui.load_ft_df(dump_data, hide=True)
        ss["submit"] = False

    else:
        with right_col:
            st.write("# USER NOT FOUND")

from datetime import timedelta, datetime

import functions.friendtech as ft
import functions.basescan as bs
import streamlit as st
import pandas as pd

import datetime


ss = st.session_state


def load_ft_graph(data):
    raw = False
    if len(data) > 1:
        # Sort the transactions by date
        data.sort(key=lambda x: datetime.datetime.strptime(x["time"], "%d/%m/%Y"))
        count = sum(1 for item in data if item['time'] == data[0]['time'])
        # Create a dictionary to store average values per date
        date_to_values = {}
        if len(data) == count:
            for item in data:
                item['time'] = item['raw_time']
            raw = True
        for trans in data:
            if raw:
                date = datetime.datetime.strptime(trans["time"], "%d/%m/%Y %H:%M")
            else:
                date = datetime.datetime.strptime(trans["time"], "%d/%m/%Y")

            if date in date_to_values:
                date_to_values[date].append(float(trans["price"]))
            else:
                date_to_values[date] = [float(trans["price"])]

        # Now compute average for each date
        for date in date_to_values:
            date_to_values[date] = sum(date_to_values[date]) / len(date_to_values[date])

        # Get today's date as a datetime.date object
        today = datetime.datetime.now()

        # Fill in dates without transactions
        current_date = min(date_to_values.keys())
        end_date = max(max(date_to_values.keys()), today)

        while current_date <= end_date:
            if current_date not in date_to_values:
                # Use the last available value
                prev_date = current_date - timedelta(days=1)
                while prev_date not in date_to_values:
                    prev_date -= timedelta(days=1)
                date_to_values[current_date] = date_to_values[prev_date]
            current_date += timedelta(days=1)

        # Convert the result to a DataFrame
        df = pd.DataFrame({
            "time": sorted(date_to_values.keys()),
            "price": [date_to_values[date] for date in sorted(date_to_values.keys())]
        })
        if raw:
            st.write(f'{data[0]["time"][:-6]} UTC')
        st.line_chart(df.set_index('time')['price'], use_container_width=True)
    else:
        st.write("No Data found")


def load_button(name):
    if name == "ref_buttons":
        with open("style/ref_buttons.css", "r") as f:
            ref_buttons_css = f.read()
        st.markdown(ref_buttons_css, unsafe_allow_html=True)


def load_ft_stats(address):
    left_col, right_col = st.columns([1, 1])
    with st.spinner("Fetching friend.tech user info..."):
        holder, holdings, keys, price = ft.addr_to_user(address, convert=False)

    if holder is not None and keys is not None:
        unique_holder = min(100, (100 * holder) / keys)
    else:
        unique_holder = 0
    if price is not None and keys is not None:
        market_cap = keys * price
    else:
        market_cap = 0

    with right_col:
        if holdings is None:
            st.write(f"**Holdings:** N/A")
        else:
            st.write(f"**Holdings:** {holdings}")
        if holder is None:
            st.write(f"**Holder:** N/A")
        else:
            st.write(f"**Holder:** {holder}")
        if keys is None:
            st.write(f"**Keys:** N/A")
        else:
            st.write(f"**Keys:** {keys}")
        if unique_holder == 0:
            st.write(f"**Unique Holder:** N/A")
        else:
            st.write(f"**Unique Holder:** {round(unique_holder, 2)}%")
        if price is None:
            st.write(f"**Key Price:** N/A")
        else:
            st.write(f"**Key Price:** {price}")
        if market_cap == 0:
            st.write(f"**Market Cap:** N/A")
        else:
            st.write(f"**Market Cap:** {round(market_cap, 3)}")

    with left_col:
        with st.spinner("Fetching friend.tech rank..."):
            try:
                points, tier = ft.get_user_points(address)
            except RuntimeError:
                points, tier = "N/A", "N/A"

        st.write(f"**{tier}:** {points} Points")
        with st.spinner("Fetching friend.tech wallet info..."):
            portfolio_value, fees_collected = ft.get_portfolio_value(address)
        if fees_collected:
            fees = fees_collected / 2
        else:
            fees = "N/A"

        st.write(f"**Portfolio Value:** {portfolio_value}")
        st.write(f"**Collected Fees:** {fees}")

        with st.spinner("Fetching Base-Scan..."):
            created_at, profit, volume, buys, sells, share_price = bs.account_stats(address)
            if profit is not None and portfolio_value is not None and fees_collected is not None:
                total = round((profit + portfolio_value + fees), 3)
            else:
                total = "N/A"
            if created_at is None:
                created_at = "N/A"

        st.write(f"**Unrealized Profit:** {profit}")
        st.write(f"**Trading Volume:** {volume}")
        st.write(f"**Total Profit: {total}**")
        st.write(f"**Created: {created_at}**")

    with right_col:
        st.write(f"**Buys:Sells:** {buys} : {sells}")

    return share_price


def load_ft_top50():
    event_data = ft.get_top_50()
    df = pd.DataFrame(event_data)
    df.index += 1
    st.dataframe(df, use_container_width=True)


def load_ft_df(data, hide):
    df = pd.DataFrame(data)
    df.index += 1
    if not hide:
        st.dataframe(df, use_container_width=True, hide_index=False)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


def load_sidebar_ft():
    with open("text/sidebar_ft.txt") as file:
        sidebar_txt = file.read()
    with st.sidebar:
        st.write(sidebar_txt, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_header():
    with open("style/header.css") as f:
        header_css = f.read()
    st.markdown(header_css, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_footer():
    with open("style/footer.css") as f:
        footer_css = f.read()
    st.markdown(footer_css, unsafe_allow_html=True)

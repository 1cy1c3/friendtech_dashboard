from datetime import timedelta, datetime

import functions.friendtech as ft
import functions.basescan as bs
import streamlit as st
import pandas as pd

import datetime
import csv

from io import StringIO
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)


ss = st.session_state


def load_ft_graph(data):
    raw = False
    if data and len(data) > 1:
        # Sort the transactions by date
        data.sort(key=lambda x: datetime.datetime.strptime(x["time"], "%d/%m/%Y"))
        count = sum(1 for item in data if item['time'] == data[0]['time'])  # Count distinct dates
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
            st.write(data[0]["time"][:-6])
        st.line_chart(df.set_index('time')['price'], use_container_width=True)
    else:
        st.write("No Data found")


def load_ft_stats(address, target, dashboard=False):
    left_col, right_col = st.columns([1, 1])
    with left_col:
        st.markdown(f"# {target}")
        st.write(f"**Wallet:** {address}")

    if not dashboard:
        with right_col:
            st.markdown("# Activity")
    with st.spinner("Fetching key activity..."):
        key_activity, key_volume, share_price, keys = ft.get_token_activity(address)

    if not dashboard:
        st.markdown("# Key Activity")
        load_ft_graph(share_price)
        load_ft_df(key_activity, hide=True)
    elif dashboard:
        with right_col:
            st.markdown("# Key Activity")
            load_ft_graph(share_price)
        load_ft_df(key_activity, hide=True)

    with st.spinner("Fetching friend.tech user info..."):
        holder, holdings, total_keys, price = ft.addr_to_user(address, convert=False)

    with left_col:
        lc_2, rc_2 = st.columns([1, 1])
        if holder != "N/A" and keys != "N/A":
            unique_holder = min(100, (100 * holder) / total_keys)
        else:
            unique_holder = 0

        if price != "N/A" and keys != "N/A":
            market_cap = total_keys * price

        else:
            market_cap = 0

        with rc_2:
            st.write(f"**Holdings:** {holdings}")
            st.write(f"**Holder:** {holder}")
            st.write(f"**Keys:** {total_keys}")
            st.write(f"**Unofficial Buys:** {total_keys - keys} **or** {round(100 * ((total_keys - keys) / total_keys), 2)}%")
            st.write(f"**Unique Holder:** {round(unique_holder, 2)}%")
            st.write(f"**Key Price:** {price}")
            st.write(f"**Market Cap:** {round(market_cap, 3)}")

        with lc_2:
            with st.spinner("Fetching friend.tech rank..."):
                points, tier = ft.get_user_points(address)

            st.write(f"**{tier}:** {points} Points")
            with st.spinner("Fetching friend.tech wallet info..."):
                portfolio_value, fees_collected = ft.get_portfolio_value(address)
            if fees_collected == "N/A":
                fees = "N/A"
            else:
                fees = fees_collected / 2

            st.write(f"**Portfolio Value:** {portfolio_value}")
            st.write(f"**Collected Fees:** {fees}")

            if not dashboard:
                with st.spinner("Fetching friend.tech user activity..."):
                    activity, created_at, profit, volume, buys, sells = ft.get_personal_activity(address)
                if profit != "N/A" and portfolio_value != "N/A" and fees_collected != "N/A":
                    total = round((profit + portfolio_value + fees), 3)
                else:
                    total = "N/A"
                st.write(f"**Unrealized:** {portfolio_value - profit}")
                st.write(f"**Trading Volume:** {volume}")
                st.write(f"**Total Profit: {total}**")
                st.write(f"**Account Balance:** {bs.balance(address)}")
                st.write(f"**Created: {created_at}**")
        if not dashboard:
            with rc_2:
                st.write(f"**Buys:Sells:** {buys} : {sells}")

    if not dashboard:
        with right_col:
            if activity != "N/A":
                load_ft_df(activity, hide=True)


def load_ft_df(data, hide):
    if data:
        df = pd.DataFrame(data)
        df.index += 1
        if not hide:
            st.dataframe(df, use_container_width=True, hide_index=False)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        pass


def load_sidebar_ft():
    with open("text/sidebar_ft.txt") as file:
        sidebar_txt = file.read()
    st.write(sidebar_txt, unsafe_allow_html=True)

    with open("style/ref_buttons.css", "r") as f:
        ref_buttons_css = f.read()
    st.markdown(ref_buttons_css, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_css_cache(element):
    with open(f"style/{element}.css") as f:
        element_css = f.read()
    st.markdown(element_css, unsafe_allow_html=True)


@st.cache_data(show_spinner=False, ttl="1d")
def load_status():
    with open("text/status.txt") as f:
        status_txt = f.read()
    st.write(status_txt, unsafe_allow_html=True)


def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    modify = st.checkbox("Add filters")

    if not modify:
        return df

    keys = df[0].keys()

    csv_data = StringIO()
    csv_writer = csv.DictWriter(csv_data, fieldnames=keys)
    csv_writer.writeheader()
    csv_writer.writerows(df)

    csv_data.seek(0)  # Set the file pointer to the beginning of the file

    df = pd.read_csv(csv_data)
    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]

    return df

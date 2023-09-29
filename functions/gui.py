from datetime import timedelta, datetime

import matplotlib.pyplot as plt
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
    metric_data = []
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
        now = datetime.datetime.now()
        last_week = now - datetime.timedelta(days=7)
        last_month = now - datetime.timedelta(days=30)
        week_date = last_week.strftime("%d/%m/%Y")
        month_date = last_month.strftime("%d/%m/%Y")

        today = df.iloc[-1]['price']
        try:
            yesterday = df.iloc[-2]['price']
        except:
            yesterday = 0
        try:
            week = df[df["time"] == week_date].iloc[0]['price']
        except:
            week = 0

        try:
            month = df[df["time"] == month_date].iloc[0]['price']
        except:
            month = 0

        metric_data.append({
            'today': today,
            'yesterday': yesterday,
            'week': week,
            'month': month
        })

        st.line_chart(df.set_index('time')['price'], use_container_width=True, height=700)
        return metric_data
    else:
        st.write("No Data found")


def load_ft_scatter(data):
    raw = False
    if data and len(data) > 1:
        # Sort the transactions by date
        data.sort(key=lambda x: datetime.datetime.strptime(x["time"], "%d/%m/%Y"))
        count = sum(1 for item in data if item['time'] == data[0]['time'])  # Count distinct dates

        if len(data) == count:
            for item in data:
                item['time'] = item['raw_time']
            raw = True

        for trans in data:
            if raw:
                trans['time'] = datetime.datetime.strptime(trans["time"], "%d/%m/%Y %H:%M")
            else:
                trans['time'] = datetime.datetime.strptime(trans["time"], "%d/%m/%Y")

        df = pd.DataFrame(data, columns=["time", "buy_price", "sell_price"])
        st.scatter_chart(df, x="time", y=["buy_price", "sell_price"], color=["#008000", "#FF0000"],
                         use_container_width=True, height=700)

    else:
        st.write("No Data found")


def load_pie_chart_holders(data):
    if data:
        # Convert data to a DataFrame
        df = pd.DataFrame(data)
        df['Balance'] = df['Balance'].astype(int)  # Convert 'Balance' column to integers

        # Calculate the percentages
        total_balance = df['Balance'].sum()
        df['Percentage'] = df['Balance'] / total_balance * 100

        fig, ax = plt.subplots()

        patches, labels, percents = ax.pie(df['Balance'], labels=df['Holder'], autopct='%1.1f%%', startangle=90)

        # Set text color to white for labels with percentage > 10%
        for i, patch in enumerate(patches):
            percentage = df['Percentage'].iloc[i]
            holder = df['Holder'].iloc[i]
            if percentage >= 5 or holder == 'BOTS':
                labels[i].set_color('white')
            else:
                labels[i].set_text('')

        # Set text color to white
        for text in labels:
            text.set_color('white')

        for i, text in enumerate(percents):
            percents[i].set_text('')

        ax.set_ylabel("")  # Remove the 'Balance' label on the pie chart
        fig.set_facecolor('#0e1117')
        fig.set_size_inches(5, 5)
        st.pyplot(fig)
    else:
        st.write("No Data Found")


def load_pie_chart_holdings(data):
    if data:
        # Convert data to a DataFrame
        df = pd.DataFrame(data)
        df['Balance'] = df['Balance'].astype(int)  # Convert 'Balance' column to integers

        # Calculate the percentages
        total_balance = df['Balance'].sum()
        df['Percentage'] = df['Balance'] / total_balance * 100

        fig, ax = plt.subplots()

        patches, labels, percents = ax.pie(df['Balance'], labels=df['Holding'], autopct='%1.1f%%', startangle=90)

        # Set text color to white for labels with percentage > 10%
        for i, patch in enumerate(patches):
            percentage = df['Percentage'].iloc[i]
            holder = df['Holding'].iloc[i]
            if percentage >= 5 or holder == 'BOTS':
                labels[i].set_color('white')
            else:
                labels[i].set_text('')

        # Set text color to white
        for text in labels:
            text.set_color('white')

        for i, text in enumerate(percents):
            percents[i].set_text('')

        ax.set_ylabel("")  # Remove the 'Balance' label on the pie chart
        fig.set_facecolor('#0e1117')
        fig.set_size_inches(5, 5)
        st.pyplot(fig)
    else:
        st.write("No Data Found")


def load_ft_stats(address, target, progress, watchlist=False):
    with st.sidebar:
        progress.progress(value=0, text="Loading Stats")
        load_ft_df(ss["history"][:10], hide=True)
        load_sidebar_ft()

    left_col, right_col = st.columns([1, 1])
    st.markdown("")
    left_stats, right_stats = st.columns([1, 1])
    st.markdown("")
    left_stats2, right_stats2 = st.columns([1, 1])
    st.markdown("")
    left_df, mid_df, right_df = st.columns([2, 1, 1])

    with left_col:
        st.markdown(f"# {target}")
        st.write(f"**Wallet:** {address}")
    progress.progress(value=5, text="Loading Stats")
    if not watchlist:
        with right_col:
            st.markdown("# Activity")

    with left_col:
        lc_2, rc_2 = st.columns([1, 1])
        metric_l, metric_m, metric_r = st.columns([1, 1, 1])

        with lc_2:
            try:
                balance = bs.balance(address)
            except Exception:
                balance = "N/A"
            progress.progress(value=15, text="Loading Stats")
            with st.spinner("Fetching friend.tech rank..."):
                points, tier, rank = ft.get_user_points(address)
            if tier.lower() == "bronze":
                st.write(f"**Weekly Rank:** {rank} **Points:** {points}")
            elif tier.lower() == "silver":
                st.write(f":gray[**Weekly Rank:** {rank}] **Points:** {points}")
            elif tier.lower() == "gold":
                st.write(f":orange[**Weekly Rank:** {rank}] **Points:** {points}")
            elif tier.lower() == "diamond":
                st.write(f":violet[**Weekly Rank:** {rank}] **Points:** {points}")
            else:
                st.write(f"**Rank:** {rank} **Points:** {points}")

            st.write(f"**Account Balance:** {balance} ETH")
            
            with st.spinner("Fetching friend.tech wallet info..."):
                portfolio_value, fees_collected = ft.get_portfolio_value(address)
            if fees_collected == "N/A":
                fees = "N/A"
            else:
                fees = fees_collected / 2
            progress.progress(value=25, text="Loading Stats")
            st.write(f"**Portfolio Value:** {portfolio_value} ETH")
            st.write(f"**Collected Fees:** {fees} ETH")

            if not watchlist:
                with st.spinner("Fetching friend.tech user activity..."):
                    activity, created_at, profit, volume, buys, sells, investment = ft.get_personal_activity(address)
                if profit != "N/A" and portfolio_value != "N/A" and fees_collected != "N/A":
                    total = round((profit + portfolio_value + fees), 3)
                else:
                    total = "N/A"

                if total != "N/A" and investment != "N/A" and investment != 0:
                    capital_efficiency = round(100 * total / investment, 2)
                else:
                    capital_efficiency = "N/A"

                st.write(f"**Investment:** {investment} ETH")
                st.write(f"**Trading Profit:** {profit} ETH")
                st.write(f"**Trading Volume:** {volume} ETH")
                st.write(f"**Total Profit: {total}**")
                st.write(f"**Capital Efficiency:** {capital_efficiency}%")
                st.write(f"**Created: {created_at}**")
        progress.progress(value=35, text="Loading Stats")
        if not watchlist:
            with rc_2:
                st.write(f"**Buys:Sells:** {buys} : {sells}")

        with st.spinner("Fetching key activity..."):
            key_activity, key_volume, share_price, keys, scatter_data = ft.get_token_activity(address)
            if keys is None:
                keys = "N/A"
        progress.progress(value=45, text="Loading Stats")
        if not watchlist:
            with left_stats:
                st.subheader("Key Price Chart")
                metrics = load_ft_graph(share_price)
            with left_stats2:
                st.subheader("Buys/Sells Chart")
                load_ft_scatter(scatter_data)

        progress.progress(value=55, text="Loading Stats")
        if watchlist:
            with right_col:
                load_ft_graph(share_price)
            load_ft_df(key_activity, hide=True, image=True)

        with st.spinner("Fetching friend.tech user info..."):
            holder, holdings, total_keys, price = ft.addr_to_user(address, convert=False)
        if not watchlist:
            progress.progress(value=65, text="Loading Stats")
        else:
            progress.progress(value=50, text="Loading Stats")
        with rc_2:
            st.write(f"**Holdings:** {holdings}")
            st.write(f"**Holder:** {holder}")
            st.write(f"**Keys:** {total_keys}")
            self_count, key_holders = ft.get_holders(address)
            progress.progress(value=75, text="Loading Stats")
            if self_count is None:
                self_count = "N/A"

            if holder != "N/A" and total_keys != "N/A" and keys != "N/A":
                unique_holder = round(min(100, (100 * holder) / total_keys), 2)
                if total_keys < keys:
                    total_keys = keys
                bots = total_keys - keys
                bot_percent = round(100 * (bots / total_keys), 2)
                if bots > 0:
                    key_holders.append({
                        'PFP': None,
                        'Holder': 'BOTS',
                        'Balance': bots
                    })
            else:
                unique_holder = "N/A"
                bots = "N/A"
                bot_percent = "N/A"

            if price != "N/A" and keys != "N/A":
                market_cap = round(total_keys * price, 3)

            else:
                market_cap = "N/A"

            if not watchlist:
                if bot_percent == "N/A":
                    st.markdown(f"**Bots:** {bots} **or** {bot_percent}%")
                elif bot_percent <= 10:
                    st.markdown(f":green[**Bots:** {bots} **or** {bot_percent}%]")
                elif 10 < bot_percent <= 25:
                    st.markdown(f":orange[**Bots:** {bots} **or** {bot_percent}%]")
                elif bot_percent > 25:
                    st.markdown(f":red[**Bots:** {bots} **or** {bot_percent}%]")

                if unique_holder == "N/A":
                    st.markdown(f"**Unique Holder:** {unique_holder}%")
                elif unique_holder > 75:
                    st.markdown(f":green[**Unique Holder:** {unique_holder}%]")
                elif 75 >= unique_holder > 50:
                    st.markdown(f":orange[**Unique Holder:** {unique_holder}%]")
                elif unique_holder <= 50:
                    st.markdown(f":red[**Unique Holder:** {unique_holder}%]")

                if self_count == "N/A":
                    st.markdown(f"**Own Keys:** {self_count}")
                elif self_count <= 3:
                    st.markdown(f":green[**Own Keys:** {self_count}]")
                elif 3 < self_count <= 10:
                    st.markdown(f":orange[**Own Keys:** {self_count}]")
                elif self_count > 10:
                    st.markdown(f":red[**Own Keys:** {self_count}]")

            st.write(f"**Key Price:** {price} ETH")
            st.write(f"**Market Cap:** {market_cap} ETH")

    if not watchlist:
        if price != "N/A":
            with metric_l:
                if metrics[0]['yesterday'] > 0.0:
                    st.metric(label="day to day",
                              value=f"{round(metrics[0]['yesterday'], 3)}ETH",
                              delta=f"{round(100 * (price - metrics[0]['yesterday']) / metrics[0]['yesterday'], 2)}%")

            with metric_m:
                if metrics[0]['week'] > 0.0:
                    st.metric(label="day to week",
                              value=f"{round(metrics[0]['week'], 3)}ETH",
                              delta=f"{round(100 * (price - metrics[0]['week']) / metrics[0]['week'], 2)}%")
            with metric_r:
                if metrics[0]['month'] > 0.0:
                    st.metric(label="day to month",
                              value=f"{round(metrics[0]['month'])}ETH",
                              delta=f"{round(100 * (price - metrics[0]['month']) / metrics[0]['month'], 2)}%")

        progress.progress(value=85, text="Loading Stats")
        with st.spinner("Getting Portfolio"):
            portfolio = ft.get_holdings(address)
        progress.progress(value=95, text="Loading Stats")
        with right_col:
            if activity != "N/A":
                load_ft_df(activity, hide=True, image=True)

        with right_stats:
            st.subheader("Holder Pie Chart")
            load_pie_chart_holders(key_holders)
        with right_stats2:
            st.subheader("Holdings Pie Chart")
            load_pie_chart_holdings(portfolio)

        with left_df:
            st.markdown("# Key Activity")
            load_ft_df(key_activity, hide=True, image=True)

        with mid_df:
            st.markdown("# Holdings")
            load_ft_df(portfolio, hide=True, image=True)
        with right_df:
            st.markdown("# Key Holders")
            load_ft_df(key_holders, hide=True, image=True)

    progress.progress(value=100, text="Completed")


def load_ft_df(data, hide, image=False):
    if data:
        if image is False:
            df = pd.DataFrame(data)
            df.index += 1
            st.dataframe(df, use_container_width=True, hide_index=hide)
        else:
            df = pd.DataFrame(data)
            st.data_editor(
                df,
                column_config={
                    "PFP": st.column_config.ImageColumn(
                        "PFP"
                    )
                },
                hide_index=True,
                use_container_width=True
            )
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

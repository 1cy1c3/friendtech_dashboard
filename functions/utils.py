import streamlit as st
from datetime import datetime

ss = st.session_state


def init_state():
    if "submit" not in ss:
        ss["submit"] = False
    if "base_mode" not in ss:
        ss["base_mode"] = False
    if "username" not in ss:
        ss["username"] = None
    if "history" not in ss:
        ss["history"] = []


def submit():
    if ss["username"] is None:
        ss["submit"] = False
    else:
        ss["submit"] = True


def home():
    ss["username"] = None


def timestamp_to_date(unix_timestamp):
    dt = datetime.utcfromtimestamp(int(unix_timestamp))
    return dt.strftime('%d/%m/%Y')


def timestamp_to_datetime(unix_timestamp):
    dt = datetime.utcfromtimestamp(int(unix_timestamp))
    return dt.strftime('%d/%m/%Y %H:%M')


def time_ago(timestamp_ms):
    # Convert the timestamp to a datetime object
    dt_object = datetime.utcfromtimestamp(timestamp_ms / 1000.0)  # converting milliseconds to seconds
    current_time = datetime.utcnow()
    difference = current_time - dt_object

    seconds_in_day = 86400  # 60 seconds * 60 minutes * 24 hours
    seconds_in_hour = 3600  # 60 seconds * 60 minutes
    seconds_in_minute = 60  # 60 seconds

    if difference.total_seconds() < seconds_in_minute:
        return f"{int(difference.total_seconds())} secs ago"
    elif difference.total_seconds() < seconds_in_hour:
        return f"{int(difference.total_seconds() / seconds_in_minute)} mins ago"
    elif difference.total_seconds() < seconds_in_day:
        return f"{int(difference.total_seconds() / seconds_in_hour)} hours ago"
    else:
        return f"{int(difference.total_seconds() / seconds_in_day)} days ago"


def get_supply(price):
    if price > 0.0:
        price = float(price * 16000)
        summation = 0.0
        supply = 0

        while price > summation:
            supply += 1
            sum1 = (supply - 1) * supply * (2 * (supply - 1) + 1) // 6
            sum2 = (supply + 1) * supply * (2 * supply + 1) // 6
            summation = float(sum2 - sum1)

        return supply
    else:
        return "N/A"


def get_value(supply, amount):
    if supply != "N/A":
        sum1 = 0 if supply == 0 else (supply - 1) * supply * (2 * (supply - 1) + 1) // 6
        sum2 = 0 if supply == 0 and amount == 1 else (supply - 1 + amount) * (supply + amount) * (2 * (supply - 1 + amount) + 1) // 6
        summation = float(sum2 - sum1)
        return round(0-(summation / 16000), 3)
    else:
        return 0.0


def list_unity(list1, list2):
    count = 0
    c_hodl = 0
    if list1 is not None and list2 is not None:
        c_hodl = len(list1)
        if len(list1) > 0 and len(list2) > 0:
            if 'Holder' in list1[0] and 'Holding' in list2[0]:
                # Get a list of 'twitterUsername' values from portfolio
                portfolio_usernames = [item['Holding'] for item in list2]

                # Get a list of 'twitterUsername' values from holder_total
                holder_total_usernames = [item['Holder'] for item in list1]

                # Find the matching usernames
                matching_usernames = set(portfolio_usernames) & set(holder_total_usernames)

                # Count the number of matching usernames
                count = len(matching_usernames)
    return count, c_hodl

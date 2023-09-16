import streamlit as st
from datetime import datetime

ss = st.session_state


def init_state():
    if "submit" not in ss:
        ss["submit"] = False
    if "base_mode" not in ss:
        ss["base_mode"] = False
    if "full_data" not in ss:
        ss["full_data"] = True
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

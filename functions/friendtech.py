import requests
import streamlit as st
from datetime import datetime
from web3 import Web3


def timestamp_to_string(unix_timestamp):
    dt = datetime.utcfromtimestamp(int(unix_timestamp))
    return dt.strftime('%d/%m/%Y')


def _timestamp_to_string(unix_timestamp):
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


def get_global_activity():
    url = f'https://prod-api.kosetto.com/global-activity'
    headers = {
        'Authorization': st.secrets["auth_token"],
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Referer': 'https://www.friend.tech/'
    }
    response = requests.get(url, headers=headers)
    try:
        data = response.json()
        response.raise_for_status()
        filtered_data = []
        if data["events"]:
            for item in data["events"]:
                if item["isBuy"]:
                    activity = "buy"
                else:
                    activity = "sell"
                time_delta = time_ago(int(item["createdAt"]))
                filtered_data.append({
                    'Timedelta': time_delta,
                    'Trader': item["trader"]['username'],
                    'Activity': activity,
                    'Subject': item['subject']['username'],
                    'Keys': item['shareAmount'],
                    'Eth': round((int(item['ethAmount']) * 10 ** -18), 3)
                })
        return filtered_data
    except requests.exceptions.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return None


def get_trending():
    url = f'https://prod-api.kosetto.com/lists/trending'
    headers = {
        'Authorization': st.secrets["auth_token"],
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Referer': 'https://www.friend.tech/'
    }
    response = requests.get(url, headers=headers)
    try:
        data = response.json()
        filtered_data = []
        for item in data["users"]:
            if "." in item["displayPrice"]:
                temp_p = item["displayPrice"].split(".")
                item["displayPrice"] = temp_p[0]
            if "." in item["volume"]:
                temp_p = item["volume"].split(".")
                item["volume"] = temp_p[0]
            filtered_data.append({
                'Subject': item['twitterUsername'],
                'Volume': round((int(item['volume']) * 10 ** -18), 3),
                'Price': round((int(item['displayPrice']) * 10 ** -18), 3)
            })
        return filtered_data
    except requests.exceptions.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return None


@st.cache_data(show_spinner=False)
def get_portfolio_value(address):
    url = f'https://prod-api.kosetto.com/wallet-info/{address}'
    response = requests.get(url)

    try:
        data = response.json()
        if data["portfolioValue"] and data["feesCollected"]:
            if "." in data["portfolioValue"]:
                temp_p = data["portfolioValue"].split(".")
                data["portfolioValue"] = temp_p[0]
            if "+" in str(data["feesCollected"]):
                temp_f = data["feesCollected"].split("+")
                data["feesCollected"] = str(temp_f[0])[:6]
                data["feesCollected"] = data["feesCollected"].replace(".", "")
                exp = int(temp_f[1]) - len(data["feesCollected"]) + 1
                data["feesCollected"] = int(data["feesCollected"]) * 10 ** exp  # This calculation lol

            return round((int(data["portfolioValue"]) * 10 ** -18), 3), round((int(data["feesCollected"]) * 10 ** -19),
                                                                              3)
        else:
            return None, None
    except requests.exceptions.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return None, None


@st.cache_data(show_spinner=False)
def get_top_50():
    url = f'https://prod-api.kosetto.com/lists/top-by-price'
    response = requests.get(url)
    try:
        data = response.json()
        top50 = []

        for rank in data["users"]:
            name = rank["twitterUsername"]
            if "." in rank["displayPrice"]:
                temp_p = rank["displayPrice"].split(".")
                rank["displayPrice"] = temp_p[0]
            price = round((int(rank["displayPrice"]) * 10 ** -18), 3)
            holder = rank["holderCount"]
            supply = rank["shareSupply"]

            user = {
                "Name": name,
                "Price": price,
                "Holder": holder,
                "Supply": supply
            }
            top50.append(user)
        return top50
    except requests.exceptions.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return None


def get_share_price(address, target):
    url = f'https://prod-api.kosetto.com/holdings-activity/{address}'
    response = requests.get(url)
    try:
        data = response.json()
        share_price = []
        for item in data["events"]:
            if item["subject"]['username'].lower() == target.lower():
                _time = timestamp_to_string(int(item['createdAt'] / 1000))
                raw_time = _timestamp_to_string(int(item['createdAt'] / 1000))
                share_price.append({
                    'time': _time,
                    'raw_time': raw_time,
                    'price': round((int(item['ethAmount']) * 10 ** -18), 3)
                })
        return share_price
    except requests.exceptions.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return None


def get_token_activity(target):
    url = f'https://prod-api.kosetto.com/users/{target}/token/trade-activity'
    response = requests.get(url)
    token_activity = []
    total_eth = 0  # initialize a counter to store the sum of ethAmounts

    try:
        data = response.json()
        for item in data["users"]:
            if item["isBuy"]:
                activity = "buy"
            else:
                activity = "sell"

            eth_value = round((int(item['ethAmount']) * 10 ** -18), 3)
            total_eth += eth_value  # increment the counter with each loop iteration

            token_activity.append({
                'Trader': item['twitterUsername'],
                'Activity': activity,
                'Keys': item['shareAmount'],
                'Eth': eth_value
            })

        return token_activity, round(total_eth, 3)
    except requests.exceptions.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return None, None


def get_user_points(address):
    url = f'https://prod-api.kosetto.com/points/{address}'
    response = requests.get(url)
    try:
        data = response.json()
        return data["totalPoints"], data["tier"]
    except requests.exceptions.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return None, None


def user_to_addr(user):
    url = 'https://prod-api.kosetto.com/search/users?'

    headers = {
        'Authorization': st.secrets["auth_token"],
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Referer': 'https://www.friend.tech/'
    }

    params = {
        'username': user
    }

    response = requests.get(url, headers=headers, params=params)
    try:
        data = response.json()
        if 'users' in data and len(data['users']) > 0:
            address = data['users'][0]['address']
            return Web3.to_checksum_address(address)  # Convert to checksum address
        else:
            return None
    except requests.exceptions.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return None


def addr_to_user(address, convert):
    url = f'https://prod-api.kosetto.com/users/{address}'
    response = requests.get(url)

    try:
        data = response.json()
        if convert and data["twitterUsername"]:
            return data["twitterUsername"]

        elif convert and not data["twitterUsername"]:
            return None

        else:
            if "." in data["displayPrice"]:
                temp_p = data["displayPrice"].split(".")
                data["displayPrice"] = temp_p[0]
            return (data["holderCount"], data["holdingCount"],
                    data["shareSupply"], round((int(data["displayPrice"]) * 10 ** -18), 3))
    except requests.exceptions.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        if convert:
            return None
        return None, None, None, None


def get_personal_activity(target):
    url = f'https://prod-api.kosetto.com/users/{target}/trade-activity'
    response = requests.get(url)
    account_activity = []
    try:
        data = response.json()
        for item in data["users"]:
            if item["isBuy"]:
                activity = "buy"
            else:
                activity = "sell"

            account_activity.append({
                'Subject': item['twitterUsername'],
                'Activity': activity,
                'Keys': item['shareAmount'],
                'Eth': round((int(item['ethAmount']) * 10 ** -18), 3)
            })
        return account_activity
    except requests.exceptions.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return None

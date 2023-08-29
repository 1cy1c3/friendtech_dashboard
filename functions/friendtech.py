import requests
import streamlit as st
from datetime import datetime
from web3 import Web3
import json


def timestamp_to_string(unix_timestamp):
    dt = datetime.utcfromtimestamp(int(unix_timestamp / 1000))
    return dt.strftime('%d/%m/%Y')


def _timestamp_to_string(unix_timestamp):
    dt = datetime.utcfromtimestamp(int(unix_timestamp / 1000))
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
                time = timestamp_to_string(int(item['createdAt']))
                raw_time = _timestamp_to_string(int(item['createdAt']))
                share_price.append({
                    'time': time,
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


@st.cache_data(show_spinner=False)
def account_stats(wallet: str):
    url = f"""https://api.basescan.org/api?module=account&action=txlist&address={wallet}
    &startblock=0&endblock=99999999&apikey={st.secrets['basescan_api_key']}"""
    response = requests.get(url)
    response.raise_for_status()  # Raises a HTTPError if the response status is 4XX or 5XX
    data = json.loads(response.text)

    if data['status'] != '1':
        print('Anfrage fehlgeschlagen')
        return None, None, None, None, None

    transactions = data['result']

    # Initial profit/loss value
    profit = 0
    volume = 0
    total_gas_fees = 0
    buys = 0
    sells = 0
    date = None

    tx_url = f"""https://api.basescan.org/api?module=account&action=txlistinternal&address={wallet}
    &startblock=0&endblock=99999999&apikey={st.secrets['basescan_api_key']}"""
    response = requests.get(tx_url)
    response.raise_for_status()

    data_tx = response.json()

    # Iterate over each transaction in the data
    for tx in transactions:
        # If the transaction is a buyShares transaction, subtract the value from profit
        if tx['functionName'].startswith('buyShares') and tx['isError'] != "1":
            profit -= int(tx['value']) / (10 ** 18)
            volume += int(tx['value']) / (10 ** 18)
            buys += 1

            if tx['value'] == "0":
                creation_block = int(tx["blockNumber"])
                block_url = f"""https://api.basescan.org/api?module=block&action=getblockcountdown&blockno=
                {creation_block}&apikey={st.secrets['basescan_api_key']}"""

                response = requests.get(block_url)
                response.raise_for_status()  # Raises a HTTPError if the response status is 4XX or 5XX
                data_block = json.loads(response.text)

                if data_block['status'] != '1':
                    print('Anfrage fehlgeschlagen')
                else:
                    timestamp = timestamp_to_string(int(data_block["result"]["timeStamp"]))
                    date = str(timestamp[:-3] + " (UTC)")

        elif (tx['functionName'].startswith('sellShares') and tx['hash'] in
              [item["hash"] for item in data_tx["result"]] and tx['isError'] != "1"):

            matched_values = [item["value"] for item in data_tx["result"] if item["hash"] == tx["hash"]]
            tx_value = matched_values[0] if matched_values else None
            profit += int(tx_value) / (10 ** 18)
            volume += int(tx['value']) / (10 ** 18)
            sells += 1

        # Calculate gas fee for the transaction
        gas_fee = int(tx['gasUsed']) / (10 ** 9)
        total_gas_fees += gas_fee

    # Convert profit from wei to ether (assuming Ethereum transactions, 1 ether = 10^18 wei)
    volume = round(volume, 3)
    profit_in_ether = round((profit - total_gas_fees), 3)
    return date, profit_in_ether, volume, buys, sells

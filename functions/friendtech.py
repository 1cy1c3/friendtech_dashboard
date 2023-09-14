import requests
import mysql.connector
import streamlit as st
from datetime import datetime
from web3 import Web3

ss = st.session_state
sc = st.secrets


def get_watchlist(name):
    conn = mysql.connector.connect(
        host=sc["db_host"],
        user=sc["db_user"],
        password=sc["db_pw"],
        database=sc["db_name"],
        autocommit=True
    )
    cursor = conn.cursor()

    create_table_query = f"""
        SELECT wallet FROM watchlist WHERE user = %s
        """

    cursor.execute(create_table_query, (name,))
    watchlist = cursor.fetchall()
    return watchlist


def add_remove_wl(wallet, name):
    values = (name, wallet)
    conn = mysql.connector.connect(
        host=sc["db_host"],
        user=sc["db_user"],
        password=sc["db_pw"],
        database=sc["db_name"],
        autocommit=True
    )
    cursor = conn.cursor()

    create_table_query = f"""
        SELECT wallet FROM watchlist WHERE user = %s
        """

    cursor.execute(create_table_query, (name,))
    watchlist = [item[0] for item in cursor.fetchall()]

    if wallet not in watchlist:
        create_table_query = f"""
        INSERT INTO watchlist (user, wallet) VALUES (%s, %s)
        """

    else:
        create_table_query = f"""
            DELETE FROM watchlist WHERE user = %s AND wallet = %s
            """

    cursor.execute(create_table_query, values)
    conn.commit()

    cursor.close()
    conn.close()


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


def get_global_activity():
    url = f'https://prod-api.kosetto.com/global-activity'
    headers = {
        'Authorization': sc["auth_token"],
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
        return None


def get_trending():
    url = f'https://prod-api.kosetto.com/lists/trending'
    headers = {
        'Authorization': sc["auth_token"],
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Referer': 'https://www.friend.tech/'
    }
    response = requests.get(url, headers=headers)
    try:
        data = response.json()
        filtered_data = []
        for item in data["users"]:
            if "displayPrice" in item and "." in item["displayPrice"]:
                temp_p = item["displayPrice"].split(".")
                item["displayPrice"] = temp_p[0]
            if "volume" in item and "." in item["volume"]:
                temp_p = item["volume"].split(".")
                item["volume"] = temp_p[0]
            filtered_data.append({
                'Subject': item['twitterUsername'],
                'Volume': round((int(item['volume']) * 10 ** -18), 3),
                'Price': round((int(item['displayPrice']) * 10 ** -18), 3)
            })
        return filtered_data
    except requests.exceptions.JSONDecodeError as e:
        return None


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
            return "N/A", "N/A"
    except requests.exceptions.JSONDecodeError as e:
        return "N/A", "N/A"


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
        return None


def get_token_activity(target):
    url = f'https://prod-api.kosetto.com/users/{target}/token/trade-activity'
    headers = {
        'Authorization': sc["auth_token"],
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Referer': 'https://www.friend.tech/'
    }

    response = requests.get(url, headers=headers)
    token_activity = []
    chart_data = []

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
            _time = timestamp_to_date(int(item['createdAt'] / 1000))
            raw_time = timestamp_to_datetime(int(item['createdAt'] / 1000))
            time_delta = time_ago(int(item["createdAt"]))

            if int(item['shareAmount']) > 1:
                item['ethAmount'] = int(int(item['ethAmount']) / int(item['shareAmount']))

            token_activity.append({
                'Trader': item['twitterUsername'],
                'Activity': activity,
                'Keys': item['shareAmount'],
                'Eth': eth_value,
                'Timedelta': time_delta
            })
            chart_data.append({
                'time': _time,
                'raw_time': raw_time,
                'price': round((int(item['ethAmount']) * 10 ** -18), 3)
            })
    except requests.exceptions.JSONDecodeError as e:
        return None, None, None

    # Search for next page start and make more requests untill the full history is loaded
    if data['nextPageStart'] != "0" and ss['full_data'] is True:
        next_page = data['nextPageStart']
        while next_page != "0":
            url = f'https://prod-api.kosetto.com/users/{target}/token/trade-activity?pageStart={next_page}'
            headers = {
                'Authorization': sc["auth_token"],
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Referer': 'https://www.friend.tech/'
            }
            response = requests.get(url, headers=headers)

            try:
                data = response.json()
                for item in data["users"]:
                    if item["isBuy"]:
                        activity = "buy"
                    else:
                        activity = "sell"

                    eth_value = round((int(item['ethAmount']) * 10 ** -18), 3)
                    total_eth += eth_value  # increment the counter with each loop iteration
                    _time = timestamp_to_date(int(item['createdAt'] / 1000))
                    raw_time = timestamp_to_datetime(int(item['createdAt'] / 1000))
                    time_delta = time_ago(int(item["createdAt"]))

                    if int(item['shareAmount']) > 1:
                        item['ethAmount'] = int(int(item['ethAmount']) / int(item['shareAmount']))

                    token_activity.append({
                        'Trader': item['twitterUsername'],
                        'Activity': activity,
                        'Keys': item['shareAmount'],
                        'Eth': eth_value,
                        'Timedelta': time_delta
                    })
                    chart_data.append({
                        'time': _time,
                        'raw_time': raw_time,
                        'price': round((int(item['ethAmount']) * 10 ** -18), 3)
                    })

                if data['nextPageStart'] is None:
                    next_page = "0"
                else:
                    next_page = data['nextPageStart']

            except requests.exceptions.JSONDecodeError as e:
                return token_activity, round(total_eth, 3), chart_data
        return token_activity, round(total_eth, 3), chart_data
    else:
        return token_activity, round(total_eth, 3), chart_data


def get_user_points(address):
    url = f'https://prod-api.kosetto.com/points/{address}'
    response = requests.get(url)
    try:
        data = response.json()
        return data["totalPoints"], data["tier"]
    except requests.exceptions.JSONDecodeError as e:
        return "N/A", "N/A"


def user_to_addr(user):
    url = 'https://prod-api.kosetto.com/search/users?'

    headers = {
        'Authorization': sc["auth_token"],
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
        return None


def addr_to_user(address, convert):
    url = f'https://prod-api.kosetto.com/users/{address}'
    response = requests.get(url)

    try:
        data = response.json()
        if convert and "twitterUsername" in data:
            return data["twitterUsername"]

        elif convert and "twitterUsername" not in data:
            return "N/A"

        else:
            if "displayPrice" in data and "." in data["displayPrice"]:
                temp_p = data["displayPrice"].split(".")
                data["displayPrice"] = temp_p[0]
            return (data["holderCount"], data["holdingCount"],
                    data["shareSupply"], round((int(data["displayPrice"]) * 10 ** -18), 3))
    except requests.exceptions.JSONDecodeError as e:
        if convert:
            return "N/A"
        return "N/A", "N/A", "N/A", "N/A"


def get_personal_activity(target):
    profit = 0
    volume = 0
    buys = 0
    sells = 0
    date = None

    url = f'https://prod-api.kosetto.com/users/{target}/trade-activity'
    response = requests.get(url)
    account_activity = []

    try:
        data = response.json()
        for item in data["users"]:
            if item["isBuy"]:
                activity = "buy"
                profit -= int(item['ethAmount']) / (10 ** 18)
                volume += int(item['ethAmount']) / (10 ** 18)
                buys += 1

                if item['ethAmount'] == "0":
                    date = str(timestamp_to_datetime(int(item["createdAt"]) / 1000) + " (UTC)")
            else:
                activity = "sell"
                profit += int(item['ethAmount']) / (10 ** 18)
                volume += int(item['ethAmount']) / (10 ** 18)
                sells += 1

            time_delta = time_ago(int(item["createdAt"]))
            account_activity.append({
                'Subject': item['twitterUsername'],
                'Activity': activity,
                'Keys': item['shareAmount'],
                'Eth': round((int(item['ethAmount']) * 10 ** -18), 3),
                'Timedelta': time_delta
            })

        volume = round(volume, 3)
        profit_in_ether = round(profit, 3)

    except requests.exceptions.JSONDecodeError as e:
        return "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"

    # Search for next page start and make more requests until the full history is loaded
    if data['nextPageStart'] != "0":
        next_page = data['nextPageStart']
        while next_page != "0":
            url = f'https://prod-api.kosetto.com/users/{target}/trade-activity?pageStart={next_page}'
            response = requests.get(url)

            try:
                data = response.json()
                for item in data["users"]:
                    if item["isBuy"]:
                        activity = "buy"
                        profit -= int(item['ethAmount']) / (10 ** 18)
                        volume += int(item['ethAmount']) / (10 ** 18)
                        buys += 1

                        if item['ethAmount'] == "0":
                            date = str(timestamp_to_datetime(int(item["createdAt"]) / 1000) + " (UTC)")
                    else:
                        activity = "sell"
                        profit += int(item['ethAmount']) / (10 ** 18)
                        volume += int(item['ethAmount']) / (10 ** 18)
                        sells += 1

                    time_delta = time_ago(int(item["createdAt"]))
                    account_activity.append({
                        'Subject': item['twitterUsername'],
                        'Activity': activity,
                        'Keys': item['shareAmount'],
                        'Eth': round((int(item['ethAmount']) * 10 ** -18), 3),
                        'Timedelta': time_delta
                    })

                if data['nextPageStart'] is None:
                    next_page = "0"
                else:
                    next_page = str(data['nextPageStart'])
                volume = round(volume, 3)
                profit_in_ether = round(profit, 3)

            except requests.exceptions.JSONDecodeError as e:
                return account_activity, date, profit_in_ether, volume, buys, sells
        return account_activity, date, profit_in_ether, volume, buys, sells
    else:
        return account_activity, date, profit_in_ether, volume, buys, sells


def get_watchlist_activity(target_list):
    watchlist_buy = []
    watchlist_sell = []

    for target in target_list:
        url = f'https://prod-api.kosetto.com/users/{target[0]}/trade-activity'
        response = requests.get(url)
        try:
            data = response.json()
            for item in data["users"]:
                if item["isBuy"]:
                    activity = "buy"
                    time_delta = time_ago(int(item["createdAt"]))
                    if "days ago" not in time_delta:
                        watchlist_buy.append({
                            'Timedelta': time_delta,
                            'Trader': target[1],
                            'Subject': item['twitterUsername'],
                            'Activity': activity,
                            'Keys': item['shareAmount'],
                            'Eth': round((int(item['ethAmount']) * 10 ** -18), 3),
                            'BuyerWallet': target[0]
                        })
                    else:
                        continue

                else:
                    activity = "sell"
                    time_delta = time_ago(int(item["createdAt"]))
                    if "days ago" not in time_delta:
                        watchlist_sell.append({
                            'Timedelta': time_delta,
                            'Trader': target[1],
                            'Subject': item['twitterUsername'],
                            'Activity': activity,
                            'Keys': item['shareAmount'],
                            'Eth': round((int(item['ethAmount']) * 10 ** -18), 3),
                            'BuyerWallet': target[0]
                        })
                    else:
                        continue

        except requests.exceptions.JSONDecodeError:
            continue

        # Search for next page start and make more requests until the full history is loaded
        if data['nextPageStart'] != "0":
            next_page = data['nextPageStart']
            if "days ago" not in watchlist_buy and "days ago" not in watchlist_sell:
                next_page = "0"
            while next_page != "0":
                url = f'https://prod-api.kosetto.com/users/{target[0]}/trade-activity?pageStart={next_page}'
                response = requests.get(url)
                try:
                    data = response.json()
                    for item in data["users"]:
                        if item["isBuy"]:
                            activity = "buy"
                            time_delta = time_ago(int(item["createdAt"]))
                            if "days ago" not in time_delta:
                                watchlist_buy.append({
                                    'BuyerWallet': target[0],
                                    'BuyerName': target[1],
                                    'Subject': item['twitterUsername'],
                                    'Keys': item['shareAmount'],
                                    'Eth': round((int(item['ethAmount']) * 10 ** -18), 3),
                                    'Timedelta': time_delta
                                })
                            else:
                                continue

                        else:
                            activity = "sell"
                            time_delta = time_ago(int(item["createdAt"]))
                            if "days ago" not in time_delta:
                                watchlist_sell.append({
                                    'BuyerWallet': target[0],
                                    'BuyerName': target[1],
                                    'Subject': item['twitterUsername'],
                                    'Keys': item['shareAmount'],
                                    'Eth': round((int(item['ethAmount']) * 10 ** -18), 3),
                                    'Timedelta': time_delta
                                })
                            else:
                                continue

                    if data['nextPageStart'] is None:
                        next_page = "0"
                    else:
                        next_page = str(data['nextPageStart'])

                except requests.exceptions.JSONDecodeError:
                    continue
        else:
            return watchlist_buy, watchlist_sell
    return watchlist_buy, watchlist_sell

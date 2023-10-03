import requests

import streamlit as st
import functions.utils as ut
from web3 import Web3

ss = st.session_state
sc = st.secrets


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
                time_delta = ut.time_ago(int(item["createdAt"]))
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
        if "users" in data:
            for item in data["users"]:
                if "displayPrice" in item and "." in item["displayPrice"]:
                    temp_p = item["displayPrice"].split(".")
                    item["displayPrice"] = temp_p[0]
                if "volume" in item and "." in item["volume"]:
                    temp_p = item["volume"].split(".")
                    item["volume"] = temp_p[0]
                filtered_data.append({
                    'PFP': item["twitterPfpUrl"],
                    'Subject': item['twitterUsername'],
                    'Volume': round((int(item['volume']) * 10 ** -18), 3),
                    'Price': round((int(item['displayPrice']) * 10 ** -18), 3)
                })
            return filtered_data
        else:
            return None
    except requests.exceptions.JSONDecodeError:
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
    except requests.exceptions.JSONDecodeError:
        return "N/A", "N/A"


def get_top_50():
    top50 = []
    url = f'https://prod-api.kosetto.com/lists/top-by-price'
    response = requests.get(url)
    try:
        data = response.json()
        if "users" in data:
            for rank in data["users"]:
                name = rank["twitterUsername"]
                if "." in rank["displayPrice"]:
                    temp_p = rank["displayPrice"].split(".")
                    rank["displayPrice"] = temp_p[0]
                price = round((int(rank["displayPrice"]) * 10 ** -18), 3)
                holder = rank["holderCount"]
                supply = rank["shareSupply"]

                user = {
                    "PFP": rank["twitterPfpUrl"],
                    "Name": name,
                    "Price": price,
                    "Holder": holder,
                    "Supply": supply
                }
                top50.append(user)
            return top50
        else:
            return None
    except requests.exceptions.JSONDecodeError:
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
    scatter_data = []

    keys = 0
    total_eth = 0  # initialize a counter to store the sum of ethAmounts

    try:
        data = response.json()
        if "users" in data:
            for item in data["users"]:
                eth_value = round((int(item['ethAmount']) * 10 ** -18), 3)
                total_eth += eth_value  # increment the counter with each loop iteration
                _time = ut.timestamp_to_date(int(item['createdAt'] / 1000))
                raw_time = ut.timestamp_to_datetime(int(item['createdAt'] / 1000))
                time_delta = ut.time_ago(int(item["createdAt"]))
                if int(item['shareAmount']) > 1:
                    item['ethAmount'] = int(int(item['ethAmount']) / int(item['shareAmount']))

                if item["isBuy"]:
                    activity = "buy"
                    keys += int(item['shareAmount'])
                    scatter_data.append({
                        'time': _time,
                        'raw_time': raw_time,
                        'buy_price': round((int(item['ethAmount']) * 10 ** -18), 3)
                    })
                else:
                    activity = "sell"
                    keys -= int(item['shareAmount'])
                    scatter_data.append({
                        'time': _time,
                        'raw_time': raw_time,
                        'sell_price': round((int(item['ethAmount']) * 10 ** -18), 3)
                    })

                token_activity.append({
                    'PFP': item["twitterPfpUrl"],
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
        else:
            return None, None, None, None, None
    except requests.exceptions.JSONDecodeError:
        return None, None, None, None, None

    # Search for next page start and make more requests untill the full history is loaded
    if data['nextPageStart'] != "0":
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
                if "users" in data:
                    for item in data["users"]:
                        eth_value = round((int(item['ethAmount']) * 10 ** -18), 3)
                        total_eth += eth_value  # increment the counter with each loop iteration
                        _time = ut.timestamp_to_date(int(item['createdAt'] / 1000))
                        raw_time = ut.timestamp_to_datetime(int(item['createdAt'] / 1000))
                        time_delta = ut.time_ago(int(item["createdAt"]))
                        if int(item['shareAmount']) > 1:
                            item['ethAmount'] = int(int(item['ethAmount']) / int(item['shareAmount']))

                        if item["isBuy"]:
                            activity = "buy"
                            keys += int(item['shareAmount'])
                            scatter_data.append({
                                'time': _time,
                                'raw_time': raw_time,
                                'buy_price': round((int(item['ethAmount']) * 10 ** -18), 3)
                            })
                        else:
                            activity = "sell"
                            keys -= int(item['shareAmount'])
                            scatter_data.append({
                                'time': _time,
                                'raw_time': raw_time,
                                'sell_price': round((int(item['ethAmount']) * 10 ** -18), 3)
                            })

                        token_activity.append({
                            'PFP': item["twitterPfpUrl"],
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
                else:
                    return token_activity, round(total_eth, 3), chart_data, keys, scatter_data
            except requests.exceptions.JSONDecodeError:
                return token_activity, round(total_eth, 3), chart_data, keys, scatter_data
        return token_activity, round(total_eth, 3), chart_data, keys, scatter_data
    else:
        return token_activity, round(total_eth, 3), chart_data, keys, scatter_data


def get_user_points(address):
    url = f'https://prod-api.kosetto.com/points/{address}'
    response = requests.get(url)
    try:
        data = response.json()
        if "leaderboard" in data:
            return data["totalPoints"], data["tier"], data["leaderboard"]
        elif "totalPoints" in data and "tier" in data:
            return data["totalPoints"], data["tier"], "N/A"
        else:
            return "N/A", "N/A", "N/A"
    except requests.exceptions.JSONDecodeError:
        return "N/A", "N/A", "N/A"


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
            for item in data['users']:
                if item['twitterUsername'].lower() == user.lower():
                    address = item['address']
                    return address, item['twitterPfpUrl']  # Convert to checksum address
        else:
            return None, None
        return None, None
    except requests.exceptions.JSONDecodeError:
        return None, None


def addr_to_user(address, convert):
    url = f'https://prod-api.kosetto.com/users/{address}'
    response = requests.get(url)

    try:
        data = response.json()
        if convert and "twitterUsername" in data:
            return data["twitterUsername"], data["twitterPfpUrl"]

        elif convert and "twitterUsername" not in data:
            return "N/A", None

        else:
            if "displayPrice" in data and "." in data["displayPrice"]:
                temp_p = data["displayPrice"].split(".")
                data["displayPrice"] = temp_p[0]
            if "holderCount" in data and "holdingCount" in data and "shareSupply" in data and "displayPrice" in data:
                return (data["holderCount"], data["holdingCount"],
                        data["shareSupply"], round((int(data["displayPrice"]) * 10 ** -18), 3))
            else:
                return "N/A", "N/A", "N/A", "N/A"
    except requests.exceptions.JSONDecodeError:
        if convert:
            return "N/A", None
        return "N/A", "N/A", "N/A", "N/A"


def get_personal_activity(target):
    profit = 0
    volume = 0
    buys = 0
    sells = 0
    investment = 0
    date = None

    url = f'https://prod-api.kosetto.com/users/{target}/trade-activity'
    response = requests.get(url)
    account_activity = []

    try:
        data = response.json()
        if "users" in data:
            for item in data["users"]:
                if item["isBuy"]:
                    activity = "buy"
                    profit -= int(item['ethAmount']) / (10 ** 18) * 1.1
                    volume += int(item['ethAmount']) / (10 ** 18) * 1.1
                    investment += int(item['ethAmount']) / (10 ** 18) * 1.1
                    buys += 1

                    if item['ethAmount'] == "0":
                        date = str(ut.timestamp_to_datetime(int(item["createdAt"]) / 1000) + " (UTC)")
                else:
                    activity = "sell"
                    profit += int(item['ethAmount']) / (10 ** 18) * 0.9
                    volume += int(item['ethAmount']) / (10 ** 18) * 0.9
                    sells += 1

                time_delta = ut.time_ago(int(item["createdAt"]))
                account_activity.append({
                    'PFP': item["twitterPfpUrl"],
                    'Subject': item['twitterUsername'],
                    'Activity': activity,
                    'Keys': item['shareAmount'],
                    'Eth': round((int(item['ethAmount']) * 10 ** -18), 3),
                    'Timedelta': time_delta
                })

            volume = round(volume, 3)
            profit_in_ether = round(profit, 3)
            investment = round(investment, 3)
        else:
            return "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"
    except requests.exceptions.JSONDecodeError:
        return "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"

    # Search for next page start and make more requests until the full history is loaded
    if data['nextPageStart'] != "0":
        next_page = data['nextPageStart']
        while next_page != "0":
            url = f'https://prod-api.kosetto.com/users/{target}/trade-activity?pageStart={next_page}'
            response = requests.get(url)

            try:
                data = response.json()
                if "users" in data:
                    for item in data["users"]:
                        if item["isBuy"]:
                            activity = "buy"
                            profit -= int(item['ethAmount']) / (10 ** 18) * 1.1
                            volume += int(item['ethAmount']) / (10 ** 18) * 1.1
                            investment += int(item['ethAmount']) / (10 ** 18) * 1.1
                            buys += 1

                            if item['ethAmount'] == "0":
                                date = str(ut.timestamp_to_datetime(int(item["createdAt"]) / 1000) + " (UTC)")
                        else:
                            activity = "sell"
                            profit += int(item['ethAmount']) / (10 ** 18) * 0.9
                            volume += int(item['ethAmount']) / (10 ** 18) * 0.9
                            sells += 1

                        time_delta = ut.time_ago(int(item["createdAt"]))
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
                    investment = round(investment, 3)
                else:
                    return account_activity, date, profit_in_ether, volume, buys, sells, investment
            except requests.exceptions.JSONDecodeError:
                return account_activity, date, profit_in_ether, volume, buys, sells, investment
        return account_activity, date, profit_in_ether, volume, buys, sells, investment
    else:
        return account_activity, date, profit_in_ether, volume, buys, sells, investment


@st.cache_data(show_spinner=False, ttl="5m")
def get_watchlist_activity(target_list):
    watchlist = []

    for target in target_list:
        url = f'https://prod-api.kosetto.com/users/{target[0]}/trade-activity'
        response = requests.get(url)
        try:
            data = response.json()
            if "users" in data:
                for item in data["users"]:
                    if item["isBuy"]:
                        activity = "buy"
                    else:
                        activity = "sell"

                    time_delta = ut.time_ago(int(item["createdAt"]))
                    if "days ago" not in time_delta:
                        watchlist.append({
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
                    continue

        except requests.exceptions.JSONDecodeError:
            continue

        # Search for next page start and make more requests until the full history is loaded
        if data['nextPageStart'] != "0":
            next_page = data['nextPageStart']
            if "days ago" not in watchlist:
                next_page = "0"
            while next_page != "0":
                url = f'https://prod-api.kosetto.com/users/{target[0]}/trade-activity?pageStart={next_page}'
                response = requests.get(url)
                try:
                    data = response.json()
                    if "users" in data:
                        for item in data["users"]:
                            if item["isBuy"]:
                                activity = "buy"
                            else:
                                activity = "sell"

                            time_delta = ut.time_ago(int(item["createdAt"]))
                            if "days ago" not in time_delta:
                                watchlist.append({
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

                        if data['nextPageStart'] is None:
                            next_page = "0"
                        else:
                            next_page = str(data['nextPageStart'])
                    else:
                        continue
                except requests.exceptions.JSONDecodeError:
                    continue
        else:
            return watchlist
    return watchlist


def get_holders(target):
    url = f'https://prod-api.kosetto.com/users/{target}/token/holders'
    response = requests.get(url)

    self_count = 0
    holder_total = []

    try:
        data = response.json()
        if 'users' in data:
            for item in data['users']:
                if item['address'].lower() == target:
                    self_count = int(item['balance'])

                holder_total.append({
                    'PFP': item["twitterPfpUrl"],
                    'Holder': item['twitterUsername'],
                    'Balance': int(item['balance'])
                })

        else:
            return None, holder_total
    except requests.exceptions.JSONDecodeError:
        return None, holder_total

    # Search for next page start and make more requests until the full history is loaded
    if data['nextPageStart'] != "0":
        next_page = data['nextPageStart']
        while next_page != "0":
            url = f'https://prod-api.kosetto.com/users/{target}/token/holders?pageStart={next_page}'
            response = requests.get(url)
            try:
                data = response.json()
                if 'users' in data:
                    for item in data['users']:
                        if item['address'] == target.lower():
                            self_count = int(item['balance'])

                        holder_total.append({
                            'Holder': item['twitterUsername'],
                            'Balance': int(item['balance'])
                        })

                    if data['nextPageStart'] is None:
                        next_page = "0"
                    else:
                        next_page = str(data['nextPageStart'])

                else:
                    return self_count, holder_total

                return self_count, holder_total
            except requests.exceptions.JSONDecodeError:
                return self_count, holder_total
        return self_count, holder_total


def get_holdings(target, dump_value=False):
    url = f'https://prod-api.kosetto.com/users/{target}/token-holdings'
    response = requests.get(url)

    portfolio = []
    try:
        data = response.json()

        if 'users' in data:
            for item in data['users']:
                if dump_value is True:
                    portfolio.append({
                        'PFP': item["twitterPfpUrl"],
                        'Holding': item['twitterUsername'],
                        'Balance': int(item['balance']),
                        'Wallet': item['address']
                    })
                else:
                    portfolio.append({
                        'PFP': item["twitterPfpUrl"],
                        'Holding': item['twitterUsername'],
                        'Balance': int(item['balance'])
                    })

        else:
            return None
    except requests.exceptions.JSONDecodeError:
        return None

    # Search for next page start and make more requests until the full history is loaded
    if data['nextPageStart'] != "0":
        next_page = data['nextPageStart']
        while next_page != "0":
            url = f'https://prod-api.kosetto.com/users/{target}/token-holdings?pageStart={next_page}'
            response = requests.get(url)
            try:
                data = response.json()
                if 'users' in data:
                    for item in data['users']:
                        portfolio.append({
                            'Holding': item['twitterUsername'],
                            'Balance': int(item['balance'])
                        })

                    if data['nextPageStart'] is None:
                        next_page = "0"
                    else:
                        next_page = str(data['nextPageStart'])

                else:
                    return portfolio

                return portfolio
            except requests.exceptions.JSONDecodeError:
                return portfolio
        return portfolio


@st.cache_resource(show_spinner=False, ttl="1h")
def get_dump_values(data, address):
    dump_data = []
    dump_value = 0
    x = 0
    if data:
        for item in data:
            if 'Wallet' in item:
                _, _, _, price = addr_to_user(item['Wallet'], convert=False)
                supply = ut.get_supply(price)
                if price != "N/A" and supply != "N/A":
                    value = ut.get_value(supply - int((item['Balance'])) - 1, int((item['Balance'])))
                    if value != "N/A":
                        if item['Balance'] == 1:
                            x = .1
                        if item['Wallet'].lower() == address:
                            dump_data.append({
                                'Holding': item['Holding'],
                                'Balance': item['Balance'],
                                'ShownValue': round(price * item['Balance'], 3),
                                'DumpValue': round(-value * (.95 + x), 3)
                            })
                            dump_value += round(-value * (.95 + x), 3)
                        else:
                            dump_data.append({
                                'Holding': item['Holding'],
                                'Balance': item['Balance'],
                                'ShownValue': round(price * item['Balance'], 3),
                                'DumpValue': round(-value * (.9 + x), 3)
                            })
                            dump_value += round(-value * (.9 + x), 3)

    return dump_data, round(dump_value, 3)

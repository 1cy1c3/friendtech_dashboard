import requests

import streamlit as st
import functions.utils as ut
import functions.database as db

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
        if "events" in data:
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
    except requests.exceptions.JSONDecodeError:
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
                try:
                    pfp = item["twitterPfpUrl"]
                except:
                    pfp = None
                if "displayPrice" in item and "." in item["displayPrice"]:
                    temp_p = item["displayPrice"].split(".")
                    item["displayPrice"] = temp_p[0]
                if "volume" in item and "." in item["volume"]:
                    temp_p = item["volume"].split(".")
                    item["volume"] = temp_p[0]
                filtered_data.append({
                    'PFP': pfp,
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
        if "portfolioValue" in data and "feesCollected" in data:
            if data["portfolioValue"] is not None and data["feesCollected"] is not None:
                if "." in data["portfolioValue"]:
                    temp_p = data["portfolioValue"].split(".")
                    data["portfolioValue"] = temp_p[0]
                if "+" in str(data["feesCollected"]):
                    temp_f = data["feesCollected"].split("+")
                    data["feesCollected"] = str(temp_f[0])[:6]
                    data["feesCollected"] = data["feesCollected"].replace(".", "")
                    exp = int(temp_f[1]) - len(data["feesCollected"]) + 1
                    data["feesCollected"] = int(data["feesCollected"]) * 10 ** exp  # This calculation lol

                return round((int(data["portfolioValue"]) * 10 ** -18), 3), round(
                    (int(data["feesCollected"]) * 10 ** -19),
                    3)
            else:
                return "N/A", "N/A"
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

                try:
                    pfp = rank["twitterPfpUrl"]
                except:
                    pfp = None

                user = {
                    "PFP": pfp,
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
    token_activity = []
    # Fetch User Data and set last timestamp
    fetch_db = db.get_data(target, "key_activity")
    if fetch_db:
        last_entry_ts = fetch_db[0]['Timestamp']
    else:
        last_entry_ts = 0

    url = f'https://prod-api.kosetto.com/users/{target}/token/trade-activity'
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
            try:
                last_ft_ts = int(data['users'][0]['createdAt'] / 1000)
            except:
                last_ft_ts = 0
            for item in data["users"]:
                if last_ft_ts <= last_entry_ts:
                    break
                eth_value = round((int(item['ethAmount']) * 10 ** -18), 3)
                time_delta = ut.time_ago(int(item["createdAt"]))
                if int(item['shareAmount']) > 1:
                    item['ethAmount'] = int(int(item['ethAmount']) / int(item['shareAmount']))

                if item["isBuy"]:
                    activity = "buy"

                else:
                    activity = "sell"
                try:
                    pfp = item["twitterPfpUrl"]
                except:
                    pfp = None

                token_activity.append({
                    'Timestamp': int(item["createdAt"] / 1000),
                    'Wallet': target,
                    'PFP': pfp,
                    'Trader': item['twitterUsername'],
                    'Activity': activity,
                    'Keys': item['shareAmount'],
                    'Eth': eth_value,
                    'Timedelta': time_delta
                })
                last_ft_ts = int(item["createdAt"] / 1000)

        else:
            return None
    except requests.exceptions.JSONDecodeError:
        return None

    # Search for next page start and make more requests until the full history is loaded
    if data['nextPageStart'] != "null" and last_ft_ts > last_entry_ts:
        next_page = data['nextPageStart']
        while next_page != "null":
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
                        if last_ft_ts <= last_entry_ts:
                            break
                        eth_value = round((int(item['ethAmount']) * 10 ** -18), 3)
                        time_delta = ut.time_ago(int(item["createdAt"]))
                        if int(item['shareAmount']) > 1:
                            item['ethAmount'] = int(int(item['ethAmount']) / int(item['shareAmount']))

                        if item["isBuy"]:
                            activity = "buy"

                        else:
                            activity = "sell"

                        try:
                            pfp = item["twitterPfpUrl"]
                        except:
                            pfp = None

                        token_activity.append({
                            'Timestamp': int(item["createdAt"] / 1000),
                            'Wallet': target,
                            'PFP': pfp,
                            'Trader': item['twitterUsername'],
                            'Activity': activity,
                            'Keys': item['shareAmount'],
                            'Eth': eth_value,
                            'Timedelta': time_delta
                        })

                        last_ft_ts = int(item["createdAt"] / 1000)
                    next_page = str(data['nextPageStart'])
                else:
                    if token_activity:
                        try:
                            db.post_data_key_activity(token_activity, target)
                        except ConnectionError:
                            pass
                    token_activity += fetch_db
                    return token_activity

            except requests.exceptions.JSONDecodeError:
                if token_activity:
                    try:
                        db.post_data_key_activity(token_activity, target)
                    except ConnectionError:
                        pass
                token_activity += fetch_db
                return token_activity
        if token_activity:
            try:
                db.post_data_key_activity(token_activity, target)
            except ConnectionError:
                pass
        token_activity += fetch_db
        return token_activity

    else:
        if token_activity:
            try:
                db.post_data_key_activity(token_activity, target)
            except ConnectionError:
                pass
        token_activity += fetch_db
        return token_activity


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
                try:
                    pfp = item["twitterPfpUrl"]
                except:
                    pfp = None
                if item['twitterUsername'].lower() == user.lower():
                    address = item['address']
                    return address, pfp  # Convert to checksum address
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
            try:
                pfp = data["twitterPfpUrl"]
            except:
                pfp = None
            return data["twitterUsername"], pfp

        elif convert and "twitterUsername" not in data:
            return "N/A", None

        else:
            if "displayPrice" in data and "." in data["displayPrice"]:
                temp_p = data["displayPrice"].split(".")
                data["displayPrice"] = temp_p[0]
            if "holderCount" in data and "holdingCount" in data and "shareSupply" in data and "displayPrice" in data:
                rank = data["rank"]
                if rank != "N/A":
                    rank = int(data["rank"])
                return (data["holderCount"], data["holdingCount"], data["shareSupply"],
                        round((int(data["displayPrice"]) * 10 ** -18), 3), rank, int(data["watchlistCount"]))
            else:
                return "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"
    except requests.exceptions.JSONDecodeError:
        if convert:
            return "N/A", None
        return "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"


def get_personal_activity(target):
    # Fetch User Data and set last timestamp
    fetch_db = db.get_data(target, "user_activity")
    if fetch_db:
        last_entry_ts = fetch_db[0]['Timestamp']
    else:
        last_entry_ts = 0

    url = f'https://prod-api.kosetto.com/users/{target}/trade-activity'
    response = requests.get(url)
    account_activity = []
    try:
        data = response.json()
        if "users" in data:
            try:
                last_ft_ts = int(data['users'][0]['createdAt'] / 1000)
            except:
                last_ft_ts = 0
            for item in data["users"]:
                if last_ft_ts <= last_entry_ts:
                    break
                if item["isBuy"]:
                    activity = "buy"

                else:
                    activity = "sell"

                time_delta = ut.time_ago(int(item["createdAt"]))
                try:
                    pfp = item["twitterPfpUrl"]
                except:
                    pfp = None

                account_activity.append({
                    'Timestamp': int(item["createdAt"] / 1000),
                    'Wallet': target,
                    'PFP': pfp,
                    'Subject': item['twitterUsername'],
                    'Activity': activity,
                    'Keys': item['shareAmount'],
                    'Eth': round((int(item['ethAmount']) * 10 ** -18), 3),
                    'Timedelta': time_delta
                })

                last_ft_ts = int(item["createdAt"] / 1000)
        else:
            return "N/A"
    except requests.exceptions.JSONDecodeError:
        return "N/A"

    # Search for next page start and make more requests until the full history is loaded
    if data['nextPageStart'] != "null" and last_ft_ts > last_entry_ts:
        next_page = data['nextPageStart']
        while next_page != "null":
            url = f'https://prod-api.kosetto.com/users/{target}/trade-activity?pageStart={next_page}'
            response = requests.get(url)

            try:
                data = response.json()
                if "users" in data:
                    for item in data["users"]:
                        if last_ft_ts <= last_entry_ts:
                            break
                        if item["isBuy"]:
                            activity = "buy"

                        else:
                            activity = "sell"

                        time_delta = ut.time_ago(int(item["createdAt"]))
                        try:
                            pfp = item["twitterPfpUrl"]
                        except:
                            pfp = None
                        account_activity.append({
                            'Timestamp': int(item["createdAt"] / 1000),
                            'Wallet': target,
                            'PFP': pfp,
                            'Subject': item['twitterUsername'],
                            'Activity': activity,
                            'Keys': item['shareAmount'],
                            'Eth': round((int(item['ethAmount']) * 10 ** -18), 3),
                            'Timedelta': time_delta
                        })

                        last_ft_ts = int(item["createdAt"] / 1000)
                    next_page = str(data['nextPageStart'])

                else:
                    if account_activity:
                        try:
                            db.post_data_user_activity(account_activity, target)
                        except ConnectionError:
                            pass
                    account_activity += fetch_db
                    account_activity = [item for item in account_activity if len(item) == 8]
                    return account_activity

            except requests.exceptions.JSONDecodeError:
                if account_activity:
                    try:
                        db.post_data_user_activity(account_activity, target)
                    except ConnectionError:
                        pass
                account_activity += fetch_db
                account_activity = [item for item in account_activity if len(item) == 8]
                return account_activity

        if account_activity:
            try:
                db.post_data_user_activity(account_activity, target)
            except ConnectionError:
                pass
        account_activity += fetch_db
        account_activity = [item for item in account_activity if len(item) == 8]
        return account_activity

    else:
        if account_activity:
            try:
                db.post_data_user_activity(account_activity, target)
            except ConnectionError:
                pass
        account_activity += fetch_db
        account_activity = [item for item in account_activity if len(item) == 8]
        return account_activity


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
        if data['nextPageStart'] != "null":
            next_page = data['nextPageStart']
            if "days ago" in watchlist:
                next_page = "null"
            while next_page != "null":
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

                try:
                    pfp = item["twitterPfpUrl"]
                except:
                    pfp = None

                holder_total.append({
                    'PFP': pfp,
                    'Holder': item['twitterUsername'],
                    'Balance': int(item['balance'])
                })

        else:
            return None, holder_total
    except requests.exceptions.JSONDecodeError:
        return None, holder_total

    # Search for next page start and make more requests until the full history is loaded
    if data['nextPageStart'] != "null":
        next_page = data['nextPageStart']
        while next_page != "null":
            url = f'https://prod-api.kosetto.com/users/{target}/token/holders?pageStart={next_page}'
            response = requests.get(url)
            try:
                data = response.json()
                if 'users' in data:
                    for item in data['users']:
                        if item['address'] == target.lower():
                            self_count = int(item['balance'])

                        try:
                            pfp = item["twitterPfpUrl"]
                        except:
                            pfp = None
                        holder_total.append({
                            'PFP': pfp,
                            'Holder': item['twitterUsername'],
                            'Balance': int(item['balance'])
                        })

                else:
                    return self_count, holder_total
                next_page = str(data['nextPageStart'])

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
                try:
                    pfp = item["twitterPfpUrl"]
                except:
                    pfp = None
                if dump_value is True:
                    portfolio.append({
                        'PFP': pfp,
                        'Holding': item['twitterUsername'],
                        'Balance': int(item['balance']),
                        'Wallet': item['address']
                    })
                else:
                    portfolio.append({
                        'PFP': pfp,
                        'Holding': item['twitterUsername'],
                        'Balance': int(item['balance'])
                    })

        else:
            return None
    except requests.exceptions.JSONDecodeError:
        return None

    # Search for next page start and make more requests until the full history is loaded
    if data['nextPageStart'] != "null":
        next_page = data['nextPageStart']
        while next_page != "null":
            url = f'https://prod-api.kosetto.com/users/{target}/token-holdings?pageStart={next_page}'
            response = requests.get(url)
            try:
                data = response.json()
                if 'users' in data:
                    for item in data['users']:
                        try:
                            pfp = item["twitterPfpUrl"]
                        except:
                            pfp = None
                        if dump_value is True:
                            portfolio.append({
                                'PFP': pfp,
                                'Holding': item['twitterUsername'],
                                'Balance': int(item['balance']),
                                'Wallet': item['address']
                            })
                        else:
                            portfolio.append({
                                'PFP': pfp,
                                'Holding': item['twitterUsername'],
                                'Balance': int(item['balance'])
                            })

                else:
                    return portfolio

                next_page = str(data['nextPageStart'])

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
                _, _, _, price, _, _ = addr_to_user(item['Wallet'], convert=False)
                if price != "N/A":
                    supply = ut.get_supply(price)
                    if supply != "N/A":
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

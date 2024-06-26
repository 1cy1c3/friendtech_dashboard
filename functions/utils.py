import streamlit as st
from datetime import datetime
from collections import defaultdict

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
    return dt.strftime('%Y/%m/%d')


def timestamp_to_datetime(unix_timestamp):
    dt = datetime.utcfromtimestamp(int(unix_timestamp))
    return dt.strftime('%Y/%m/%d %H:%M')


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
        sum2 = 0 if supply == 0 and amount == 1 else (supply - 1 + amount) * (supply + amount) * (
                2 * (supply - 1 + amount) + 1) // 6
        summation = float(sum2 - sum1)
        return round(0 - (summation / 16000), 3)
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
                portfolio_usernames = [item['Holding'].lower() for item in list2]

                # Get a list of 'twitterUsername' values from holder_total
                holder_total_usernames = [item['Holder'].lower() for item in list1]

                # Find the matching usernames
                matching_usernames = set(portfolio_usernames) & set(holder_total_usernames)

                # Count the number of matching usernames
                count = len(matching_usernames)
    return count, c_hodl


def get_holdings(data):
    profit = 0
    volume = 0
    buys = 0
    sells = 0
    investment = 0
    holdings_raw = []

    if data:
        for item in data:
            if "Activity" in item:
                if item["Activity"].lower() == "buy":
                    profit -= item['Eth']
                    volume += item['Eth']
                    investment += item['Eth']
                    buys += int(item['Keys'])
                    for _ in range(int(item['Keys'])):
                        holdings_raw.append({
                            'PFP': item["PFP"],
                            'Holding': item['Subject'],
                            'Balance': 1
                        })

                else:
                    profit += item['Eth']
                    volume += item['Eth']
                    sells += int(item['Keys'])
                    for _ in range(int(item['Keys'])):
                        holdings_raw.append({
                            'PFP': item["PFP"],
                            'Holding': item['Subject'],
                            'Balance': -1
                        })
        date = str(timestamp_to_datetime(data[-1]["Timestamp"]) + " (UTC)")
        holdings = combine_duplicates_holding(holdings_raw)
        holdings = sorted(holdings, key=lambda x: x['Balance'], reverse=True)
        return date, round(profit, 3), round(volume, 3), buys, sells, round(investment, 3), holdings
    else:
        return None, None, None, None, None, None, None


def get_holders(data, target):
    chart_data = []
    scatter_data = []
    holders_raw = []
    keys = 0
    total_eth = 0
    self_count = 0
    if data:
        for item in data:
            total_eth += item['Eth']  # increment the counter with each loop iteration
            _time = timestamp_to_date(item['Timestamp'])
            raw_time = timestamp_to_datetime(item['Timestamp'])
            price = round((float(item['Eth']) / int(item['Keys'])), 3)
            if "Activity" in item:
                if item["Activity"] == "buy":
                    if target.lower() == item['Trader'].lower():
                        self_count += int(item['Keys'])

                    keys += int(item['Keys'])
                    scatter_data.append({
                        'time': _time,
                        'raw_time': raw_time,
                        'buy_price': price
                    })
                    for _ in range(int(item['Keys'])):
                        holders_raw.append({
                            'PFP': item["PFP"],
                            'Holder': item['Trader'],
                            'Balance': 1
                        })

                else:
                    if target.lower() == item['Trader'].lower():
                        self_count -= int(item['Keys'])
                    keys -= int(item['Keys'])
                    scatter_data.append({
                        'time': _time,
                        'raw_time': raw_time,
                        'sell_price': price
                    })
                    for _ in range(int(item['Keys'])):
                        holders_raw.append({
                            'PFP': item["PFP"],
                            'Holder': item['Trader'],
                            'Balance': -1
                        })

                chart_data.append({
                    'time': _time,
                    'raw_time': raw_time,
                    'price': price
                })

        holders = combine_duplicates_holder(holders_raw)
        holders = sorted(holders, key=lambda x: x['Balance'], reverse=True)
        return round(total_eth, 3), chart_data, keys, scatter_data, holders, self_count
    else:
        return None, None, None, None, None, None


def combine_duplicates_holding(items):
    combined_dict = defaultdict(lambda: {'Balance': 0, 'PFP': None})
    for entry in items:
        username = entry['Holding']
        balance = entry['Balance']
        pfp = entry['PFP']
        combined_dict[username]['Balance'] += balance
        combined_dict[username]['PFP'] = pfp

    combined_list = []
    for username, data in combined_dict.items():
        balance = data['Balance']
        pfp = data['PFP']
        for _ in range(balance):
            if balance > 0:
                entry = {'PFP': pfp, 'Holding': username, 'Balance': balance}
                combined_list.append(entry)

    # Convert each dictionary to a frozenset and store them in a set to remove duplicates
    combined_list = set(frozenset(d.items()) for d in combined_list)

    # Convert the frozensets back to dictionaries
    combined_list = [dict(fs) for fs in combined_list]

    return combined_list


def combine_duplicates_holder(items):
    combined_dict = defaultdict(lambda: {'Balance': 0, 'PFP': None})
    for entry in items:
        username = entry['Holder']
        balance = entry['Balance']
        pfp = entry['PFP']
        combined_dict[username]['Balance'] += balance
        combined_dict[username]['PFP'] = pfp

    combined_list = []
    for username, data in combined_dict.items():
        balance = data['Balance']
        pfp = data['PFP']
        for _ in range(balance):
            if balance > 0:
                entry = {'PFP': pfp, 'Holder': username, 'Balance': balance}
                combined_list.append(entry)

    # Convert each dictionary to a frozenset and store them in a set to remove duplicates
    combined_list = set(frozenset(d.items()) for d in combined_list)

    # Convert the frozensets back to dictionaries
    combined_list = [dict(fs) for fs in combined_list]

    return combined_list

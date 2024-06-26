import requests
import streamlit as st
import functions.utils as ut
import json
import time

ss = st.session_state


@st.cache_resource(show_spinner="Fetching Base Scan", ttl="15m")
def balance(wallet: str):
    url = (f"https://api.basescan.org/api?module=account&action=balance&address="
           f"{wallet}&apikey={st.secrets['basescan_api_key']}")

    response = requests.get(url)
    response.raise_for_status()  # Raises a HTTPError if the response status is 4XX or 5XX
    try:
        data = json.loads(response.text)
        if data['status'] != '1':
            return "N/A"
        return round(float(int(data['result']) * 10 ** -18), 3)
    except requests.exceptions.JSONDecodeError:
        return "N/A"


# Substituted by ft now
def account_stats(wallet: str):
    # Initial profit/loss value
    profit = 0
    volume = 0
    total_gas_fees = 0
    buys = 0
    sells = 0
    date = None

    url = (f"https://api.basescan.org/api?module=account&action=txlist&address={wallet}"
           f"&startblock=0&endblock=99999999&apikey={st.secrets['basescan_api_key']}")

    response = requests.get(url)
    response.raise_for_status()  # Raises a HTTPError if the response status is 4XX or 5XX
    data = json.loads(response.text)
    if data['status'] != '1':
        return "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"

    txs = data['result']
    tx_url = (f"https://api.basescan.org/api?module=account&action=txlistinternal&address={wallet}"
              f"&startblock=0&endblock=99999999&apikey={st.secrets['basescan_api_key']}")

    response = requests.get(tx_url)
    response.raise_for_status()
    data_int = response.json()
    txs_int = data_int['result']

    for tx in txs:
        # If the transaction is a buyShares transaction, subtract the value from profit
        if tx['functionName'].startswith('buyShares') and tx['isError'] != "1":
            profit -= int(tx['value']) / (10 ** 18)
            volume += int(tx['value']) / (10 ** 18)
            buys += 1

            if tx['value'] == "0":  # Filter for first share buy
                creation_block = str(tx["blockNumber"])
                block_url = (f"https://api.basescan.org/api?module=block&action=getblockreward&blockno="
                             f"{creation_block}&apikey={st.secrets['basescan_api_key']}")

                response = requests.get(block_url)
                response.raise_for_status()  # Raises a HTTPError if the response status is 4XX or 5XX
                data_block = json.loads(response.text)

                if data_block['status'] == '1':
                    timestamp = ut.timestamp_to_datetime(int(data_block["result"]["timeStamp"]))
                    date = str(timestamp + " (UTC)")

        # If the transaction is a sellShares transaction, add the value from profit
        elif (tx['functionName'].startswith('sellShares') and tx['hash'] in
              [item["hash"] for item in txs_int] and tx['isError'] != "1"):

            # search for matching tx hashes
            matched_values = [item["value"] for item in txs_int if item["hash"] == tx["hash"]]
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


def get_trending(wallet: str):
    input_time = int(time.time()) - (15 * 60)
    start_block = get_block_by_timestamp(input_time)

    url = (f"https://api.basescan.org/api?module=account&action=txlist&address={wallet}"
           f"&startblock={start_block}&endblock=99999999&apikey={st.secrets['basescan_api_key']}")

    response = requests.get(url)
    response.raise_for_status()  # Raises a HTTPError if the response status is 4XX or 5XX
    try:
        data = json.loads(response.text)
    except requests.exceptions.JSONDecodeError:
        return None, None, None, None, None

    if data['status'] != '1':
        return None, None, None, None, None

    txs = data['result']

    tx_url = (f"https://api.basescan.org/api?module=account&action=txlistinternal&address={wallet}"
              f"&startblock={start_block}&endblock=99999999&apikey={st.secrets['basescan_api_key']}")

    response = requests.get(tx_url)
    response.raise_for_status()
    data_int = response.json()
    txs_int = data_int['result']

    # Create set of hashes to reduce the data
    tx_hashes = set(item['hash'] for item in txs)
    # Checking for txs, where the receiver isn't friend.tech
    conf_int_txs = [item for item in txs_int if item['hash'] in tx_hashes
                    and item['to'] != st.secrets['friendtech_wallet'].lower()]
    results = []
    for tx in txs:
        # If the transaction is a buyShares transaction, subtract the value from profit
        if (tx['functionName'].startswith('buyShares') or tx['functionName'].startswith('sellShares')
                and tx['isError'] != "1"):
            # Here, you search for the corresponding transaction in conf_int_txs
            matching_tx = next((item for item in conf_int_txs if item['hash'] == tx['hash']
                                and tx['from'] != item['to']), None)

            if matching_tx:
                # Convert the value to integer
                value = int(matching_tx['value']) * 20 * 10 ** -18

                # Search for existing dictionary with the 'to' address in results list
                found = False
                for result in results:
                    if result['Subject'] == matching_tx['to']:
                        if tx['functionName'].startswith('buyShares'):
                            result['Value'] += value
                        elif tx['functionName'].startswith('sellShares'):
                            result['Value'] -= value
                        found = True
                        break

                    # If not found, append a new dictionary to results
                if not found:
                    new_dict = {
                        'Subject': matching_tx['to'],
                        'Value': (value if tx['functionName'].startswith('buyShares') else -value)
                    }
                    results.append(new_dict)

    winners = [res for res in results if res['Value'] > 0.01 and 'e' not in str(res['Value'])]  # Filter for Winning
    losers = [res for res in results if res['Value'] < -0.01 and 'e' not in str(res['Value'])]  # Filter for Losing
    winners.sort(key=lambda x: x['Value'], reverse=True)  # Sorting
    losers.sort(key=lambda x: x['Value'])

    return winners, losers


def get_block_by_timestamp(timestamp):
    url = (f"https://api.basescan.org/api?module=block&action=getblocknobytime&timestamp={str(int(timestamp))}"
           f"&closest=before&apikey={st.secrets['basescan_api_key']}")
    response = requests.get(url)
    response.raise_for_status()  # Raises a HTTPError if the response status is 4XX or 5XX
    try:
        data = json.loads(response.text)
    except requests.exceptions.JSONDecodeError:
        return "0"

    if data['status'] != '1':
        return "0"  # To avoid crash at failed request
    return data['result']


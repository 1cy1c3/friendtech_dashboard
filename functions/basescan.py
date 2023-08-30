import requests
import streamlit as st
import functions.friendtech as ft
import json
import time


# @st.cache_data(show_spinner=False)
def account_stats(wallet: str):
    input_time = int(time.time()) - (15 * 60)
    trending = False

    if wallet == st.secrets['friendtech_contract']:
        trending = True

    start_block = get_block_by_timestamp(input_time)

    if trending:
        url = (f"https://api.basescan.org/api?module=account&action=txlist&address={wallet}"
               f"&startblock={start_block}&endblock=99999999&apikey={st.secrets['basescan_api_key']}")
    else:
        url = (f"https://api.basescan.org/api?module=account&action=txlist&address={wallet}"
               f"&startblock=0&endblock=99999999&apikey={st.secrets['basescan_api_key']}")

    response = requests.get(url)
    response.raise_for_status()  # Raises a HTTPError if the response status is 4XX or 5XX
    data = json.loads(response.text)

    if data['status'] != '1':
        print('Anfrage 1 fehlgeschlagen')
        return None, None, None, None, None

    txs = data['result']

    # Initial profit/loss value
    profit = 0
    volume = 0
    total_gas_fees = 0
    buys = 0
    sells = 0
    date = None

    if trending:
        tx_url = (f"https://api.basescan.org/api?module=account&action=txlistinternal&address={wallet}"
                  f"&startblock={start_block}&endblock=99999999&apikey={st.secrets['basescan_api_key']}")
    else:
        tx_url = (f"https://api.basescan.org/api?module=account&action=txlistinternal&address={wallet}"
                  f"&startblock=0&endblock=99999999&apikey={st.secrets['basescan_api_key']}")

    response = requests.get(tx_url)
    response.raise_for_status()
    data_int = response.json()
    txs_int = data_int['result']

    if not trending:
        # Iterate over each transaction in the data
        for tx in txs:
            # If the transaction is a buyShares transaction, subtract the value from profit
            if tx['functionName'].startswith('buyShares') and tx['isError'] != "1":
                profit -= int(tx['value']) / (10 ** 18)
                volume += int(tx['value']) / (10 ** 18)
                buys += 1

                if tx['value'] == "0":
                    creation_block = str(tx["blockNumber"])
                    block_url = (f"https://api.basescan.org/api?module=block&action=getblockreward&blockno="
                                 f"{creation_block}&apikey={st.secrets['basescan_api_key']}")

                    response = requests.get(block_url)
                    response.raise_for_status()  # Raises a HTTPError if the response status is 4XX or 5XX
                    data_block = json.loads(response.text)

                    if data_block['status'] != '1':
                        print('Anfrage 2 fehlgeschlagen')
                    else:
                        timestamp = ft._timestamp_to_string(int(data_block["result"]["timeStamp"]))
                        date = str(timestamp + " (UTC)")

            elif (tx['functionName'].startswith('sellShares') and tx['hash'] in
                  [item["hash"] for item in data_int["result"]] and tx['isError'] != "1"):

                matched_values = [item["value"] for item in data_int["result"] if item["hash"] == tx["hash"]]
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
    else:
        tx_hashes = set(item['hash'] for item in txs)
        conf_int_txs = [item for item in txs_int if item['hash'] in tx_hashes
                        and item['to'] != st.secrets['friendtech_wallet'].lower()]
        results = []
        for tx in txs:
            # If the transaction is a buyShares transaction, subtract the value from profit
            if (tx['functionName'].startswith('buyShares') or tx['functionName'].startswith('sellShares')
                    and tx['isError'] != "1"):
                # Here, you search for the corresponding transaction in conf_int_txs
                matching_tx = next((item for item in conf_int_txs if item['hash'] == tx['hash']), None)

                if matching_tx:
                    # Convert the value to integer
                    value = int(matching_tx['value']) * 10 ** -18

                    # Search for existing dictionary with the 'to' address in results list
                    found = False
                    for result in results:
                        if result['to'] == matching_tx['to']:
                            if tx['functionName'].startswith('buyShares'):
                                result['value'] += value
                            elif tx['functionName'].startswith('sellShares'):
                                result['value'] -= value
                            found = True
                            break

                        # If not found, append a new dictionary to results
                    if not found:
                        new_dict = {
                            'to': matching_tx['to'],
                            'value': (value if tx['functionName'].startswith('buyShares') else -value)
                        }
                        results.append(new_dict)

        winners = [res for res in results if res['value'] > 0.01 and 'e' not in str(res['value'])]
        losers = [res for res in results if res['value'] < -0.01 and 'e' not in str(res['value'])]
        winners.sort(key=lambda x: x['value'], reverse=True)
        losers.sort(key=lambda x: x['value'])

        return winners, losers


def get_block_by_timestamp(timestamp):
    url = (f"https://api.basescan.org/api?module=block&action=getblocknobytime&timestamp={str(int(timestamp))}"
           f"&closest=before&apikey={st.secrets['basescan_api_key']}")
    response = requests.get(url)
    response.raise_for_status()  # Raises a HTTPError if the response status is 4XX or 5XX
    data = json.loads(response.text)

    if data['status'] != '1':
        print('Anfrage 3 fehlgeschlagen')
        return "0"
    return data['result']


def extract_value(hex_string):
    # Remove the '0x' prefix if it exists
    hex_string = hex_string[2:] if hex_string.startswith('0x') else hex_string

    # Find the position of the last zero
    last_zero_position = max(loc for loc, val in enumerate(hex_string) if val == '0')

    # Slice the string from the last zero's position to the end
    result = hex_string[last_zero_position + 1:]

    return result

import mysql.connector
import streamlit as st
import pandas as pd

ss = st.session_state
sc = st.secrets


@st.cache_data(show_spinner=False, ttl="15m")
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
    get_watchlist.cache_data.clear()


def get_data(wallet, database):
    try:
        conn = mysql.connector.connect(
            host=sc["db_host"],
            user=sc["db_user"],
            password=sc["db_pw"],
            database=sc["db_name"],
            autocommit=True
        )
        cursor = conn.cursor()

        create_table_query = f"""
            SELECT * FROM {database} WHERE wallet = %s
            ORDER BY timestamp DESC
            """

        cursor.execute(create_table_query, (wallet,))
        # Fetch all the rows from the cursor
        rows = cursor.fetchall()

        # Get the column names from the cursor description
        column_names = [desc[0] for desc in cursor.description]
        # Create a pandas DataFrame from the fetched rows and column names
        df = pd.DataFrame(rows, columns=column_names)
        df = df.drop(columns=['id'])

        # Convert the filtered DataFrame to a JSON string
        json_data = df.to_dict(orient='records')
        return json_data
    except:
        return None


def post_data_user_activity(data, wallet):
    conn = mysql.connector.connect(
        host=sc["db_host"],
        user=sc["db_user"],
        password=sc["db_pw"],
        database=sc["db_name"],
        autocommit=True
    )
    cursor = conn.cursor()
    for item in data:
        if 'PFP' in item:
            create_table_query = f"""
                INSERT INTO user_activity (Timestamp, Wallet, PFP, Subject, Activity, Keys, Eth, Timedelta) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
            cursor.execute(
                create_table_query,
                (item['Timestamp'], wallet, item['PFP'], item['Subject'], item['Activity'], item['Keys'], item['Eth'], item['Timedelta']))
    conn.commit()
    conn.close()


def post_data_key_activity(data, wallet):
    conn = mysql.connector.connect(
        host=sc["db_host"],
        user=sc["db_user"],
        password=sc["db_pw"],
        database=sc["db_name"],
        autocommit=True
    )
    cursor = conn.cursor()
    for item in data:
        create_table_query = f"""
            INSERT INTO key_activity (Timestamp, Wallet, PFP, Trader, Activity, Keys, Eth, Timedelta) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
        cursor.execute(
            create_table_query,
            (item['Timestamp'], wallet, item['PFP'], item['Trader'], item['Activity'], item['Keys'], item['Eth'], item['Timedelta']))
    conn.commit()
    conn.close()

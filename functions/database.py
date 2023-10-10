import mysql.connector
import streamlit as st
import datetime

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
        """

    cursor.execute(create_table_query, (wallet,))
    results = cursor.fetchall()
    return results


def post_data_holders(data, wallet):
    current_date = datetime.datetime.now().date()
    timestamp = int(
        (datetime.datetime.timestamp(datetime.datetime.combine(current_date, datetime.datetime.min.time()))))
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
            INSERT INTO holders (timestamp, wallet, pfp, name, amount) VALUES (%s, %s, %s, %s, %s)
            """
        cursor.execute(create_table_query, (timestamp, wallet, item['PFP'], item['Holder'], item['Balance']))
    conn.commit()
    conn.close()


def post_data_holdings(data, wallet):
    current_date = datetime.datetime.now().date()
    timestamp = int(
        (datetime.datetime.timestamp(datetime.datetime.combine(current_date, datetime.datetime.min.time()))))
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
            INSERT INTO holdings (timestamp, wallet, pfp, name, amount) VALUES (%s, %s, %s, %s, %s)
            """
        cursor.execute(create_table_query, (timestamp, wallet, item['PFP'], item['Holder'], item['Balance']))
    conn.commit()
    conn.close()
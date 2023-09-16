import mysql.connector
import streamlit as st


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
    st.cache_data.clear()

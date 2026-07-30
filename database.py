import mysql.connector
from mysql.connector import Error
from config import (
    DB_HOST,
    DB_PORT,
    DB_USER,
    DB_PASSWORD,
    DB_NAME
)

def get_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            ssl_disabled=False
        )

        if connection.is_connected():
            print("Database Connected Successfully")

        return connection

    except Error as e:
        print(f"Database Connection Error: {e}")
        return None

import mysql.connector
from mysql.connector import Error
from config import *

def get_connection():
    try:
        connection = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)

        if connection.is_connected():
            print("✅ Database Connected Successfully")

        return connection

    except Error as e:
        print(f"❌ Database Connection Error: {e}")
        return None
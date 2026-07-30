import mysql.connector
from mysql.connector import Error

from config import (
    DB_HOST,
    DB_USER,
    DB_PASSWORD,
    DB_NAME,
    DB_PORT
)


def get_connection():

    try:

        connection = mysql.connector.connect(

            host=DB_HOST,

            port=DB_PORT,

            user=DB_USER,

            password=DB_PASSWORD,

            database=DB_NAME,

            connection_timeout=10

        )

        if connection.is_connected():

            print(
                "Database Connected Successfully"
            )

        return connection

    except Error as error:

        print(
            "Database Connection Error:",
            error
        )

        return None

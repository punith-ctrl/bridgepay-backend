from flask import Blueprint, jsonify
from database import get_connection

import requests
import socket


# =====================================
# BLUEPRINT
# =====================================

sync_bp = Blueprint(
    "sync",
    __name__
)


# =====================================
# ESP32 ADDRESS
# =====================================

ESP32_IP = "192.168.4.1"

ESP32_URL = (
    f"http://{ESP32_IP}"
)


# =====================================
# CHECK INTERNET
# =====================================

def internet_available():

    try:

        connection = socket.create_connection(

            (
                "8.8.8.8",
                53
            ),

            timeout=3

        )

        connection.close()

        return True

    except OSError:

        return False


# =====================================
# CHECK ESP32
# =====================================

def esp32_available():

    try:

        response = requests.get(

            ESP32_URL +
            "/status",

            timeout=3

        )

        if (
            response.status_code
            == 200
        ):

            return True

        return False

    except Exception as error:

        print(

            "ESP32 check:",

            error

        )

        return False


# =====================================
# ESP32 STATUS API
# =====================================

@sync_bp.route(

    "/esp32/status",

    methods=["GET"]

)
def esp32_status():

    connected = (
        esp32_available()
    )


    return jsonify({

        "connected":
        connected

    })


# =====================================
# SYNCHRONIZE PAYMENTS
# =====================================

@sync_bp.route(

    "/sync",

    methods=["POST"]

)
def synchronize_payments():

    # =================================
    # STEP 1:
    # CHECK REAL INTERNET
    # =================================

    internet = (
        internet_available()
    )


    # ---------------------------------
    # INTERNET NOT AVAILABLE
    # ---------------------------------

    if not internet:

        return jsonify({

            "status":
            "waiting",

            "internet":
            False,

            "esp32":
            esp32_available(),

            "synced":
            0,

            "message":
            "Waiting for internet"

        })


    # =================================
    # STEP 2:
    # INTERNET IS AVAILABLE
    # =================================

    connection = get_connection()


    if connection is None:

        return jsonify({

            "status":
            "failed",

            "message":
            "Database connection failed"

        }), 500


    cursor = connection.cursor()


    try:

        # =================================
        # FIND PENDING PAYMENTS
        # =================================

        cursor.execute(

            """
            SELECT
                transaction_id

            FROM transactions

            WHERE

                status = 'PENDING'

                OR

                sync_status = 'PENDING'
            """

        )


        pending_rows = (
            cursor.fetchall()
        )


        pending_count = (
            len(
                pending_rows
            )
        )


        # =================================
        # NO PENDING PAYMENT
        # =================================

        if pending_count == 0:

            return jsonify({

                "status":
                "success",

                "internet":
                True,

                "esp32":
                esp32_available(),

                "synced":
                0,

                "message":
                "All payments credited"

            })


        # =================================
        # STEP 3:
        # TRY TO NOTIFY ESP32
        # =================================

        esp32_connected = (
            esp32_available()
        )


        esp32_notified = False


        if esp32_connected:

            try:

                response = requests.get(

                    ESP32_URL +
                    "/sync",

                    timeout=5

                )


                if (
                    response.status_code
                    == 200
                ):

                    esp32_notified = True


                    print(

                        "ESP32 sync signal sent"

                    )


            except Exception as error:

                print(

                    "ESP32 notification failed:",

                    error

                )


        # =================================
        # STEP 4:
        # CREDIT PAYMENT
        #
        # INTERNET IS ENOUGH HERE.
        # ESP32 MAY BE DISCONNECTED.
        # =================================

        cursor.execute(

            """
            UPDATE transactions

            SET

                status = 'COMPLETED',

                sync_status = 'SYNCED'

            WHERE

                status = 'PENDING'

                OR

                sync_status = 'PENDING'
            """

        )


        connection.commit()


        print(

            pending_count,

            "payment(s) credited"

        )


        # =================================
        # SUCCESS RESPONSE
        # =================================

        return jsonify({

            "status":
            "success",

            "internet":
            True,

            "esp32":
            esp32_connected,

            "esp32_notified":
            esp32_notified,

            "synced":
            pending_count,

            "message":
            "Payments credited successfully"

        })


    except Exception as error:

        connection.rollback()


        print(

            "SYNC ERROR:",

            error

        )


        return jsonify({

            "status":
            "failed",

            "message":
            str(
                error
            )

        }), 500


    finally:

        cursor.close()

        connection.close()
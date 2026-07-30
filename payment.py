from flask import Blueprint, request, jsonify
from database import get_connection
import requests

# =====================================
# BLUEPRINT
# =====================================

payment_bp = Blueprint(
    "payment",
    __name__
)

# =====================================
# ESP32 ADDRESS
# =====================================

ESP32_URL = "http://192.168.4.1"


# =====================================
# SEND PAYMENT
# =====================================

@payment_bp.route(
    "/payment/send",
    methods=["POST"]
)
def send_payment():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({

            "status": "failed",

            "message":
            "Invalid payment data"

        }), 400


    # ---------------------------------
    # GET PAYMENT DATA
    # ---------------------------------

    try:

        sender_id = int(
            data.get(
                "sender_id"
            )
        )

        receiver_phone = str(
            data.get(
                "receiver_phone",
                ""
            )
        ).strip()

        amount = float(
            data.get(
                "amount"
            )
        )

    except Exception:

        return jsonify({

            "status": "failed",

            "message":
            "Invalid sender, receiver, or amount"

        }), 400


    # ---------------------------------
    # VALIDATE
    # ---------------------------------

    if not receiver_phone:

        return jsonify({

            "status": "failed",

            "message":
            "Enter receiver phone number"

        }), 400


    if amount <= 0:

        return jsonify({

            "status": "failed",

            "message":
            "Enter a valid amount"

        }), 400


    # ---------------------------------
    # DATABASE
    # ---------------------------------

    connection = get_connection()

    if connection is None:

        return jsonify({

            "status": "failed",

            "message":
            "Database connection failed"

        }), 500


    cursor = connection.cursor(
        dictionary=True
    )


    try:

        # ---------------------------------
        # FIND RECEIVER
        # ---------------------------------

        cursor.execute(

            """
            SELECT
                customer_id,
                name

            FROM customers

            WHERE phone = %s
            """,

            (
                receiver_phone,
            )

        )


        receiver = cursor.fetchone()


        if receiver is None:

            return jsonify({

                "status": "failed",

                "message":
                "Receiver not found"

            }), 404


        receiver_id = (
            receiver[
                "customer_id"
            ]
        )


        # ---------------------------------
        # PREVENT SELF PAYMENT
        # ---------------------------------

        if sender_id == receiver_id:

            return jsonify({

                "status": "failed",

                "message":
                "You cannot send money to yourself"

            }), 400


        # ---------------------------------
        # CHECK BALANCE
        # ---------------------------------

        cursor.execute(

            """
            SELECT balance

            FROM wallets

            WHERE customer_id = %s
            """,

            (
                sender_id,
            )

        )


        sender_wallet = (
            cursor.fetchone()
        )


        if sender_wallet is None:

            return jsonify({

                "status": "failed",

                "message":
                "Sender wallet not found"

            }), 404


        if float(
            sender_wallet[
                "balance"
            ]
        ) < amount:

            return jsonify({

                "status": "failed",

                "message":
                "Insufficient balance"

            }), 400


        # =================================
        # SEND TO ESP32
        # =================================

        try:

            print(
                "Sending payment to ESP32..."
            )


            esp32_response = requests.post(

                ESP32_URL +
                "/payment",

                json={

                    "sender":
                    str(
                        sender_id
                    ),

                    "receiver":
                    receiver_phone,

                    "amount":
                    amount

                },

                timeout=8

            )


            print(

                "ESP32 response:",

                esp32_response.status_code,

                esp32_response.text

            )


            if (
                esp32_response.status_code
                != 200
            ):

                return jsonify({

                    "status":
                    "failed",

                    "message":
                    "ESP32 rejected payment"

                }), 503


            esp32_data = (
                esp32_response.json()
            )


            if (
                esp32_data.get(
                    "status"
                )
                !=
                "success"
            ):

                return jsonify({

                    "status":
                    "failed",

                    "message":

                    esp32_data.get(

                        "message",

                        "ESP32 payment failed"

                    )

                }), 503


        except requests.exceptions.RequestException:

            return jsonify({

                "status":
                "failed",

                "message":

                "ESP32 not connected. "
                "Connect the laptop to "
                "VillagePay Wi-Fi."

            }), 503


        # =================================
        # ESP32 ACCEPTED
        # DEDUCT SENDER BALANCE
        # =================================

        cursor.execute(

            """
            UPDATE wallets

            SET balance =
                balance - %s

            WHERE customer_id = %s
            """,

            (

                amount,

                sender_id

            )

        )


        # =================================
        # CREATE PENDING TRANSACTION
        # =================================

        cursor.execute(

            """
            INSERT INTO transactions
            (

                sender_id,

                receiver_id,

                amount,

                mode,

                status,

                sync_status

            )

            VALUES
            (

                %s,

                %s,

                %s,

                %s,

                %s,

                %s

            )
            """,

            (

                sender_id,

                receiver_id,

                amount,

                "OFFLINE",

                "PENDING",

                "PENDING"

            )

        )


        connection.commit()


        return jsonify({

            "status":
            "success",

            "message":

            "Payment stored in ESP32. "
            "Waiting for internet.",

            "receiver":

            receiver[
                "name"
            ],

            "amount":

            amount,

            "payment_status":

            "PENDING"

        })


    except Exception as error:

        connection.rollback()

        print(

            "PAYMENT ERROR:",

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


# =====================================
# TRANSACTION HISTORY
# =====================================

@payment_bp.route(
    "/transactions/<int:customer_id>",
    methods=["GET"]
)
def get_transactions(
    customer_id
):

    connection = get_connection()


    if connection is None:

        return jsonify(
            []
        )


    cursor = connection.cursor(
        dictionary=True
    )


    try:

        cursor.execute(

            """
            SELECT

                t.transaction_id,

                CASE

                    WHEN
                    t.sender_id = %s

                    THEN
                    receiver.phone

                    ELSE
                    sender.phone

                END
                AS other_phone,


                CASE

                    WHEN
                    t.sender_id = %s

                    THEN
                    'Sent'

                    ELSE
                    'Received'

                END
                AS transaction_type,


                t.amount,

                t.status,

                t.sync_status,

                t.created_at


            FROM transactions t


            LEFT JOIN customers sender

            ON
            t.sender_id =
            sender.customer_id


            LEFT JOIN customers receiver

            ON
            t.receiver_id =
            receiver.customer_id


            WHERE

            t.sender_id = %s

            OR

            t.receiver_id = %s


            ORDER BY

            t.transaction_id DESC

            """,

            (

                customer_id,

                customer_id,

                customer_id,

                customer_id

            )

        )


        rows = cursor.fetchall()


        transactions = []


        for tx in rows:

            transactions.append({

                "transaction_id":

                tx[
                    "transaction_id"
                ],


                "other_phone":

                tx[
                    "other_phone"
                ]

                or

                "Unknown",


                "transaction_type":

                tx[
                    "transaction_type"
                ],


                "amount":

                float(

                    tx[
                        "amount"
                    ]

                ),


                "status":

                tx[
                    "status"
                ]

                or

                "",


                "sync_status":

                tx[
                    "sync_status"
                ]

                or

                "",


                "created_at":

                str(

                    tx[
                        "created_at"
                    ]

                )

            })


        return jsonify(
            transactions
        )


    except Exception as error:

        print(

            "TRANSACTION ERROR:",

            error

        )


        return jsonify(
            []
        )


    finally:

        cursor.close()

        connection.close()
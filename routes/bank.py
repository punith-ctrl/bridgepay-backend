from flask import Blueprint, jsonify
from database import get_connection

bank_bp = Blueprint("bank", __name__)

@bank_bp.route("/banksync", methods=["GET"])
def bank_sync():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            c.customer_id,
            c.name,
            c.bank_name,
            w.balance
        FROM customers c
        JOIN wallets w
        ON c.customer_id = w.customer_id
    """)

    customers = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({
        "status": "success",
        "bank_server": "BridgePay Bank Simulator",
        "customers": customers
    })

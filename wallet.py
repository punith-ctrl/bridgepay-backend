from flask import Blueprint, request, jsonify
from database import get_connection

wallet_bp = Blueprint("wallet", __name__)


@wallet_bp.route("/wallet/<int:customer_id>", methods=["GET"])
def get_wallet(customer_id):

    connection = get_connection()

    # Fixed: was missing null-check — crashed with AttributeError when DB
    # connection failed, causing a silent 500 and balance stuck at ₹0
    if connection is None:
        return jsonify({
            "status": "failed",
            "message": "Database connection failed"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            "SELECT balance FROM wallets WHERE customer_id = %s",
            (customer_id,)
        )
        wallet = cursor.fetchone()

        if wallet:
            return jsonify({
                "status":  "success",
                "balance": float(wallet["balance"])   # explicit float, never Decimal
            })

        return jsonify({
            "status":  "failed",
            "message": "Wallet not found"
        }), 404

    except Exception as e:

        return jsonify({
            "status":  "failed",
            "message": str(e)
        }), 500

    finally:

        cursor.close()
        connection.close()


@wallet_bp.route("/deposit", methods=["POST"])
def deposit():

    data = request.get_json()

    customer_id = data["customer_id"]
    amount      = float(data["amount"])

    connection = get_connection()

    if connection is None:
        return jsonify({"status": "failed", "message": "Database connection failed"}), 500

    cursor = connection.cursor()

    try:

        cursor.execute(
            "UPDATE wallets SET balance = balance + %s WHERE customer_id = %s",
            (amount, customer_id)
        )
        connection.commit()

        return jsonify({
            "status":  "success",
            "message": "Money Deposited Successfully"
        })

    except Exception as e:

        connection.rollback()
        return jsonify({"status": "failed", "message": str(e)}), 500

    finally:

        cursor.close()
        connection.close()


@wallet_bp.route("/withdraw", methods=["POST"])
def withdraw():

    data = request.get_json()

    customer_id = data["customer_id"]
    amount      = float(data["amount"])

    connection = get_connection()

    if connection is None:
        return jsonify({"status": "failed", "message": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            "SELECT balance FROM wallets WHERE customer_id = %s",
            (customer_id,)
        )
        wallet = cursor.fetchone()

        if not wallet:
            return jsonify({"status": "failed", "message": "Wallet not found"}), 404

        if float(wallet["balance"]) < amount:
            return jsonify({"status": "failed", "message": "Insufficient Balance"})

        cursor.execute(
            "UPDATE wallets SET balance = balance - %s WHERE customer_id = %s",
            (amount, customer_id)
        )
        connection.commit()

        return jsonify({
            "status":  "success",
            "message": "Money Withdrawn Successfully"
        })

    except Exception as e:

        connection.rollback()
        return jsonify({"status": "failed", "message": str(e)}), 500

    finally:

        cursor.close()
        connection.close()

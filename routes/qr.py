from flask import Blueprint, request, jsonify
from database import get_connection
import qrcode
import os

qr_bp = Blueprint("qr", __name__)

@qr_bp.route("/generate_qr/<int:customer_id>", methods=["GET"])
def generate_qr(customer_id):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT customer_id, name, phone, villagepay_id
        FROM customers
        WHERE customer_id=%s
    """, (customer_id,))

    customer = cursor.fetchone()

    cursor.close()
    connection.close()

    if customer is None:
        return jsonify({
            "status": "failed",
            "message": "Customer not found"
        })

    qr_data = f"""VILLAGEPAY
ID:{customer['villagepay_id']}
NAME:{customer['name']}
PHONE:{customer['phone']}"""

    qr_dir = os.path.join(os.path.dirname(__file__), '..', 'qrcodes')
    if not os.path.exists(qr_dir):
        os.makedirs(qr_dir)

    filename = f"qrcodes/customer_{customer_id}.png"
    full_path = os.path.join(os.path.dirname(__file__), '..', filename)

    img = qrcode.make(qr_data)
    img.save(full_path)

    return jsonify({
        "status": "success",
        "customer": customer,
        "qr_image": filename
    })


@qr_bp.route("/qrpayment", methods=["POST"])
def qr_payment():

    data = request.get_json()

    sender_id = data["sender_id"]
    receiver_id = data["receiver_id"]
    amount = float(data["amount"])

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # Check sender balance
        cursor.execute(
            "SELECT balance FROM wallets WHERE customer_id=%s",
            (sender_id,)
        )
        sender = cursor.fetchone()

        if sender is None:
            return jsonify({
                "status": "failed",
                "message": "Sender wallet not found"
            })

        if sender["balance"] < amount:
            return jsonify({
                "status": "failed",
                "message": "Insufficient Balance"
            })

        # Check receiver wallet exists before touching sender
        cursor.execute(
            "SELECT balance FROM wallets WHERE customer_id=%s",
            (receiver_id,)
        )
        receiver = cursor.fetchone()

        if receiver is None:
            return jsonify({
                "status": "failed",
                "message": "Receiver wallet not found"
            })

        # Debit sender
        cursor.execute(
            "UPDATE wallets SET balance = balance - %s WHERE customer_id=%s",
            (amount, sender_id)
        )

        # Credit receiver once — Fixed: was credited twice (duplicate UPDATE)
        cursor.execute(
            "UPDATE wallets SET balance = balance + %s WHERE customer_id=%s",
            (amount, receiver_id)
        )

        cursor.execute("""
            INSERT INTO transactions
            (sender_id, receiver_id, amount, mode, status, sync_status)
            VALUES (%s, %s, %s, 'OFFLINE', 'COMPLETED', 'SYNCED')
        """, (sender_id, receiver_id, amount))

        connection.commit()

        return jsonify({
            "status": "success",
            "message": "QR Payment Successful"
        })

    except Exception as e:

        connection.rollback()

        return jsonify({
            "status": "failed",
            "message": str(e)
        }), 500

    finally:

        cursor.close()
        connection.close()

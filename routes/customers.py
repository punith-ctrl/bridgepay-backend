from flask import Blueprint, request, jsonify
from database import get_connection

customer_bp = Blueprint("customers", __name__)


# ----------------------------
# CUSTOMER REGISTRATION
# ----------------------------
@customer_bp.route("/register", methods=["POST"])
def register_customers():

    data = request.get_json()

    name     = data.get("name", "").strip()
    phone    = data.get("phone", "").strip()
    password = data.get("password", "").strip()
    bank     = data.get("bank", "").strip()

    if not name or not phone or not password:
        return jsonify({
            "status": "failed",
            "message": "Name, phone and password are required."
        }), 400

    # Generate VillagePay ID from last 6 digits of phone
    villagepay_id = "VP" + phone[-6:]

    connection = get_connection()

    if connection is None:
        return jsonify({
            "status": "failed",
            "message": "Database connection failed."
        }), 500

    cursor = connection.cursor()

    try:

        # Create customer record
        cursor.execute(
            """
            INSERT INTO customers
                (name, phone, password, bank_name, villagepay_id)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (name, phone, password, bank, villagepay_id)
        )

        customer_id = cursor.lastrowid

        # Create wallet with starter balance automatically
        cursor.execute(
            """
            INSERT INTO wallets (customer_id, balance)
            VALUES (%s, %s)
            """,
            (customer_id, 1000.00)
        )

        connection.commit()

        return jsonify({
            "status":  "success",
            "message": "Registration Successful"
        })

    except Exception as e:

        connection.rollback()

        # Friendly message for duplicate phone
        if "Duplicate entry" in str(e):
            return jsonify({
                "status":  "failed",
                "message": "This phone number is already registered."
            }), 409

        return jsonify({
            "status":  "failed",
            "message": str(e)
        }), 500

    finally:

        cursor.close()
        connection.close()

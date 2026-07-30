from flask import Blueprint, request, jsonify
from database import get_connection

login_bp = Blueprint("login", __name__)


@login_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    phone = data.get("phone")
    password = data.get("password")

    connection = get_connection()

    if connection is None:

        return jsonify({
            "status": "failed",
            "message": "Database connection failed"
        }), 500

    cursor = connection.cursor(
        dictionary=True
    )

    try:

        sql = """
SELECT
    customer_id,
    name,
    phone,
    bank_name,
    villagepay_id
FROM customers
WHERE phone=%s AND password=%s
"""

        cursor.execute(
            sql,
            (phone, password)
        )

        customers = cursor.fetchone()

        if customers:

            return jsonify({
    "status": "success",
    "customers": customers
})

        return jsonify({

            "status": "failed",

            "message":
            "Invalid Phone or Password"

        })

    except Exception as e:

        return jsonify({

            "status": "failed",

            "message": str(e)

        }), 500

    finally:

        cursor.close()

        connection.close()
from flask import Blueprint, jsonify
from database import get_connection

admin_bp = Blueprint("admin", __name__)

# Dashboard Summary
@admin_bp.route("/admin/dashboard", methods=["GET"])
def dashboard():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Fixed: alias was "total_customerss" (double-s) — caused KeyError
    cursor.execute("SELECT COUNT(*) AS total_customers FROM customers")
    customers = cursor.fetchone()["total_customers"]

    cursor.execute("SELECT COUNT(*) AS total_transactions FROM transactions")
    transactions = cursor.fetchone()["total_transactions"]

    cursor.execute("SELECT SUM(amount) AS total_amount FROM transactions")
    total = cursor.fetchone()["total_amount"]

    cursor.close()
    connection.close()

    return jsonify({
        "customers": customers,
        "transactions": transactions,
        "total_amount": float(total or 0)
    })


# Customers List
# Fixed: route was "/admin/customerss" (double-s) — admin.js called /admin/customers and got 404
@admin_bp.route("/admin/customers", methods=["GET"])
def customers_list():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT customer_id, name, phone FROM customers")

    data = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify(data)


# Transaction List
@admin_bp.route("/admin/transactions", methods=["GET"])
def transaction_list():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            t.transaction_id,
            s.name AS sender_name,
            r.name AS receiver_name,
            t.amount,
            t.status,
            t.sync_status,
            t.created_at
        FROM transactions t
        JOIN customers s ON t.sender_id = s.customer_id
        JOIN customers r ON t.receiver_id = r.customer_id
        ORDER BY t.transaction_id DESC
    """)

    data = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify(data)

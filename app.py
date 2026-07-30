from routes.esp32 import esp32_bp
from flask import Flask, jsonify
from flask import Flask
from flask_cors import CORS
from routes.customers import customer_bp
from routes.login import login_bp
from routes.wallet import wallet_bp
from routes.payment import payment_bp
from routes.qr import qr_bp
from routes.sync import sync_bp
from routes.admin import admin_bp
from routes.bank import bank_bp

# Serve the frontend folder as static files so relative API URLs work
app = Flask(__name__, static_folder='../frontend', static_url_path='')

CORS(app)

# Register Blueprints
app.register_blueprint(customer_bp)
app.register_blueprint(login_bp)
app.register_blueprint(wallet_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(qr_bp)
app.register_blueprint(sync_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(bank_bp)
app.register_blueprint(esp32_bp)
@app.route("/")
def home():
    from flask import redirect
    return redirect("/login/login.html")
import requests

ESP32_IP = "192.168.1.100"   # Change this to your ESP32 IP


@app.route("/esp32/status", methods=["GET"])
def esp32_status():

    try:

        response = requests.get(
            f"http://{ESP32_IP}/status",
            timeout=2
        )

        if response.status_code == 200:

            return jsonify({
                "status": "connected"
            })

    except:

        pass

    return jsonify({
        "status": "disconnected"
    })
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
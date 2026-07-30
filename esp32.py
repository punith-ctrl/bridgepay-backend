from flask import Blueprint, jsonify
import requests

esp32_bp = Blueprint(
    "esp32",
    __name__
)

ESP32_URL = "http://192.168.4.1"


@esp32_bp.route(
    "/esp32/status",
    methods=["GET"]
)
def esp32_status():

    try:

        response = requests.get(
            ESP32_URL + "/status",
            timeout=2
        )

        data = response.json()

        if (
            response.status_code == 200
            and
            data.get("connected") is True
        ):

            return jsonify({

                "connected": True,

                "pending":
                data.get(
                    "pending",
                    0
                )

            })

        return jsonify({

            "connected": False,

            "pending": 0

        })

    except Exception as error:

        print(
            "ESP32 error:",
            error
        )

        return jsonify({

            "connected": False,

            "pending": 0

        })
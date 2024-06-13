import os
from dotenv import load_dotenv

from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
import atexit

from flask import Flask, render_template, request, jsonify

from satellite_functions import satellite_cnn_predict
from camera_functions import camera_cnn_predict
from meteorological_functions import weather_data_predict

import sqlite3

# Load environment variables from .env file
load_dotenv()
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")

# Create a database and alerts table if not exists


def init_db():
    conn = sqlite3.connect("alerts.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


# Function that runs email_alert.py script
def run_alert_script():
    script_path = os.path.join(os.path.dirname(__file__), "email_alert.py")
    try:
        subprocess.run(["python", script_path], check=True)
        print("Processing script executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running processing script: {e}")


# Initialize the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=run_alert_script, trigger="interval", hours=1)
scheduler.start()

# Ensure the scheduler is shut down properly on exit
atexit.register(lambda: scheduler.shutdown())


app = Flask(__name__)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/detect/camera")
def detect_camera():
    return render_template("detect_camera.html")


@app.route("/detect/satellite")
def detect_satellite():
    return render_template("detect_satellite.html", MAPBOX_TOKEN=MAPBOX_TOKEN)


@app.route("/alert", methods=["GET", "POST"])
def alert():
    if request.method == "GET":
        return render_template("alert.html", MAPBOX_TOKEN=MAPBOX_TOKEN)

    if request.method == "POST":
        data = request.json
        email = data.get("email")
        latitude = data.get("latitude")
        longitude = data.get("longitude")

        # Check for missing or invalid coordinates or email
        if not email or latitude == 0 or longitude == 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Invalid coordinates or missing information.",
                    }
                ),
                400,
            )

        try:
            conn = sqlite3.connect("alerts.db")
            cursor = conn.cursor()

            # Check if the email is already in the database
            cursor.execute("SELECT * FROM alerts WHERE email=?", (email,))
            existing_alert = cursor.fetchone()
            if existing_alert:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "This email is already subscribed to alerts.",
                        }
                    ),
                    400,
                )

            # Insert the new email
            cursor.execute(
                "INSERT INTO alerts (email, latitude, longitude) VALUES (?, ?, ?)",
                (email, latitude, longitude),
            )
            conn.commit()
            conn.close()
            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Alert subscription successful! You will now receive wildfire alerts.",
                    }
                ),
                200,
            )
        except sqlite3.IntegrityError:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "An error occurred while processing your request. Please try again later.",
                    }
                ),
                500,
            )
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500


# The route for predicting wildfire using satellite data
@app.route("/satellite_predict", methods=["POST"])
def satellite_predict():
    data = request.json
    latitude = data["location"][1]
    longitude = data["location"][0]
    zoom = data["zoom"]

    output_size = (350, 350)
    crop_amount = 35
    save_path = "satellite_image.png"

    prediction_sattelite = satellite_cnn_predict(
        latitude,
        longitude,
        output_size=output_size,
        zoom_level=zoom,
        crop_amount=crop_amount,
        save_path=save_path,
    )

    satellite_confidence = round(
        (
            prediction_sattelite
            if prediction_sattelite > 0.5
            else 1 - prediction_sattelite
        )
        * 100
    )  # float to percentage

    satellite_status = 1 if prediction_sattelite > 0.5 else 0

    prediction_weather = weather_data_predict(latitude, longitude)

    weather_confidence = round(
        (prediction_weather if prediction_weather > 0.5 else 1 - prediction_weather)
        * 100
    )  # float to percentage

    weather_status = 1 if prediction_weather > 0.5 else 0

    # Calculate average probability and its corresponding binary status
    prediction_average = (prediction_sattelite + prediction_weather) / 2

    average_confidence = round(
        (prediction_average if prediction_average > 0.5 else 1 - prediction_average)
        * 100
    )  # float to percentage

    average_status = 1 if prediction_average > 0.5 else 0

    response = {
        "satellite_probability": satellite_confidence,
        "satellite_status": satellite_status,
        "weather_probability": weather_confidence,
        "weather_status": weather_status,
        "average_probability": average_confidence,
        "average_status": average_status,
    }

    return jsonify(response), 200


# The route for predicting wildfire using camera images
@app.route("/camera_predict", methods=["POST"])
def camera_predict():
    image_file = request.files["image"]
    prediction = camera_cnn_predict(image_file)

    confidence = round(
        (prediction if prediction > 0.5 else 1 - prediction) * 100)

    # Alphabetically *fire* (0) comes before *no fire* (1)
    wildfire_prediction = 1 if prediction < 0.5 else 0

    response_data = {
        "wildfire_prediction": wildfire_prediction,
        "confidence": confidence,
    }

    return jsonify(response_data), 200


if __name__ == "__main__":
    init_db()
    app.run(debug=True)

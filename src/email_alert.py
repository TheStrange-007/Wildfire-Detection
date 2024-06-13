import sqlite3
from mailersend import emails
import os

from satellite_functions import satellite_cnn_predict
from meteorological_functions import weather_data_predict

from jinja2 import Template


# Connect to the alerts database
def fetch_alerts():
    conn = sqlite3.connect("alerts.db")
    cursor = conn.cursor()
    cursor.execute("SELECT email, latitude, longitude FROM alerts")
    records = cursor.fetchall()
    conn.close()
    return records


# Perform predictions and generate a report
def generate_report(email, latitude, longitude):
    output_size = (350, 350)
    crop_amount = 35
    save_path = "satellite_image.png"

    satellite_prediction = satellite_cnn_predict(
        latitude,
        longitude,
        output_size=output_size,
        zoom_level=15,
        crop_amount=crop_amount,
        save_path=save_path,
    )

    weather_prediction = weather_data_predict(latitude, longitude)

    report = {
        "email": email,
        "latitude": latitude,
        "longitude": longitude,
        "satellite_probability": round(satellite_prediction * 100),
        "weather_probability": round(weather_prediction * 100),
        "average_probability": round(
            ((satellite_prediction + weather_prediction) / 2) * 100
        ),
    }

    return report


# Prepare the HTML email content using a template
def prepare_email_content(report):
    template = Template(
        """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Wildfire Risk Report</title>
        <style>
            @import url('https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css');
        </style>
    </head>
    <body class="bg-gray-100 text-gray-800">
        <div class="max-w-2xl mx-auto p-6 bg-white shadow-md rounded">
            <h1 class="text-2xl font-bold mb-4">Wildfire Risk Report</h1>
            <p>Hello,</p>
            <p>Based on our analysis, here is the wildfire risk report for your location:</p>
            <ul class="list-disc ml-5">
                <li><strong>Email:</strong> {{ report.email }}</li>
                <li><strong>Latitude:</strong> {{ report.latitude }}</li>
                <li><strong>Longitude:</strong> {{ report.longitude }}</li>
                <li><strong>Satellite Probability:</strong> {{ report.satellite_probability }}%</li>
                <li><strong>Weather Probability:</strong> {{ report.weather_probability }}%</li>
                <li><strong>Average Probability:</strong> {{ report.average_probability }}%</li>
            </ul>
            <p>Stay safe!</p>
        </div>
    </body>
    </html>
    """
    )
    return template.render(report=report)


# Send the email using MailerSend
def send_email(report, email_content):
    mailer = emails.NewEmail(
        os.getenv("MAILERSEND_KEY")
    )

    mail_from = {
        "name": "Wildfire Alerts",
        "email": "alerts@trial-k68zxl21dwm4j905.mlsender.net",
    }

    recipients = [{"email": report["email"]}]

    mail_body = {}
    mailer.set_mail_from(mail_from, mail_body)
    mailer.set_mail_to(recipients, mail_body)
    mailer.set_subject("Wildfire Risk Report for Your Area", mail_body)
    mailer.set_html_content(email_content, mail_body)

    response = mailer.send(mail_body)
    print(f"Email sent to {report['email']} with response: {response}")


# Main function to process all alerts
def process_alerts():
    alerts = fetch_alerts()
    for alert in alerts:
        email, latitude, longitude = alert
        report = generate_report(email, latitude, longitude)
        email_content = prepare_email_content(report)
        send_email(report, email_content)


if __name__ == "__main__":
    process_alerts()

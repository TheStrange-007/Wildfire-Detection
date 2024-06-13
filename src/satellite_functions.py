import os
from dotenv import load_dotenv

import requests
from PIL import Image
from io import BytesIO
import numpy as np
from tensorflow.keras.models import load_model

# Load environment variables from .env file
load_dotenv()
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")

model = load_model("analysis/wildfire_satellite_detection_model.keras")


# Function to preprocess the satellite image
def preprocess_image(img_path):
    img = Image.open(img_path)
    img_resized = img.resize((224, 224))
    img_array = np.array(img_resized)
    img_array = img_array / 255.0

    return np.expand_dims(img_array, axis=0)


# Function to predict wildfire probability using satellite imagery
def satellite_cnn_predict(
    latitude, longitude, output_size, zoom_level, crop_amount, save_path
):
    # Increase the height of the image by crop_amount pixels
    output_size_modified = (output_size[0], output_size[1] + crop_amount)

    url = f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/{longitude},{latitude},{zoom_level}/{output_size_modified[0]}x{output_size_modified[1]}?access_token={MAPBOX_TOKEN}"
    response = requests.get(url)

    if response.status_code == 200:
        img = Image.open(BytesIO(response.content))

        # Calculate the amount of pixels to remove from top and bottom
        remove_pixels = crop_amount
        remove_pixels_half = remove_pixels // 2

        img_cropped = img.crop(
            (0, remove_pixels_half, img.width, img.height - remove_pixels_half)
        )
        img_resized = img_cropped.resize((224, 224))
        img_resized.save(save_path)
        print(f"Image saved as '{save_path}'")

        processed_image = preprocess_image(save_path)
        prediction = model.predict(processed_image)

        return prediction[0][0]

    else:
        print("Failed to retrieve the image.")

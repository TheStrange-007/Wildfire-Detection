import numpy as np
from PIL import Image
from io import BytesIO
from tensorflow.keras.models import load_model

# Load the model
model_path = "analysis/wildfire_camera_detection_model.keras"
model = load_model(model_path)


# Function to preprocess the image before prediction
def preprocess_image(img):
    img_resized = img.resize((224, 224))
    img_array = np.array(img_resized)
    img_array = img_array / 255.0

    return np.expand_dims(img_array, axis=0)


# Function to predict wildfire probability using camera image
def camera_cnn_predict(image_file):
    image = Image.open(BytesIO(image_file.read())).convert("RGB")
    preprocessed_image = preprocess_image(image)
    prediction = model.predict(preprocessed_image)[0][0]

    return prediction

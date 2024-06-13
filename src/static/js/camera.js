document.addEventListener("DOMContentLoaded", () => {
    const imageInput = document.getElementById('imageInput');
    const imageContainer = document.getElementById('imageContainer');
    const uploadedImage = document.getElementById('uploadedImage');
    const predictBtn = document.getElementById('predictBtn');
    const predictionResult = document.getElementById('predictionResult');
    const confidenceBar = document.getElementById('confidenceBar');
    const confidenceText = document.getElementById('confidenceText');

    imageInput.addEventListener('change', () => {
        const file = imageInput.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                uploadedImage.src = e.target.result;
                uploadedImage.style.display = 'block';
            };
            reader.readAsDataURL(file);
        } else {
            uploadedImage.style.display = 'none';
        }
    });

    predictBtn.addEventListener('click', async () => {
        if (!imageInput.files.length) {
            alert('Please upload an image first.');
            return;
        }

        const formData = new FormData();
        formData.append('image', imageInput.files[0]);

        const response = await fetch('/camera_predict', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        const wildfirePrediction = data.wildfire_prediction;
        const confidence = data.confidence;
        const predictionPercentage = data.prediction_percentage;

        predictionResult.textContent = wildfirePrediction ? 'THERE IS A WILDFIRE' : 'THERE IS NO WILDFIRE';
        confidenceBar.style.width = `${confidence}%`;
        confidenceText.textContent = `Confidence: ${confidence}%`;
    });
});

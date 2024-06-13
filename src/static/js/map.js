document.addEventListener("DOMContentLoaded", () => {
    const map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/streets-v11',
        center: [0, 0],
        zoom: 2
    });

    const searchInput = document.getElementById('search');
    const searchBtn = document.getElementById('searchBtn');
    const predictBtn = document.getElementById('predictBtn');
    const suggestionsContainer = document.getElementById('suggestions');

    let marker = new mapboxgl.Marker({
        draggable: true
    }).setLngLat([0, 0]).addTo(map);

    marker.on('dragend', onDragEnd);

    function onDragEnd() {
        const lngLat = marker.getLngLat();
        setMapLocation([lngLat.lng, lngLat.lat]);
    }

    async function fetchSuggestions(query) {
        const response = await fetch(`https://api.mapbox.com/geocoding/v5/mapbox.places/${query}.json?access_token=${mapboxgl.accessToken}`);
        const data = await response.json();
        return data.features.map(feature => ({
            label: feature.place_name,
            value: feature.center
        }));
    }

    function showSuggestions(suggestions) {
        suggestionsContainer.innerHTML = '';
        suggestions.forEach(suggestion => {
            const suggestionItem = document.createElement('div');
            suggestionItem.className = 'suggestion-item';
            suggestionItem.textContent = suggestion.label;
            suggestionItem.addEventListener('click', () => {
                searchInput.value = suggestion.label;
                setMapLocation(suggestion.value);
                suggestionsContainer.innerHTML = '';
            });
            suggestionsContainer.appendChild(suggestionItem);
        });
    }

    searchInput.addEventListener('input', async () => {
        const query = searchInput.value;
        if (query.length > 2) {
            const suggestions = await fetchSuggestions(query);
            showSuggestions(suggestions);
        } else {
            suggestionsContainer.innerHTML = '';
        }
    });

    searchBtn.addEventListener('click', () => {
        const query = searchInput.value;
        fetchSuggestions(query).then(suggestions => {
            if (suggestions.length > 0) {
                setMapLocation(suggestions[0].value);
            }
        });
    });

    searchInput.addEventListener('keypress', event => {
        if (event.key === 'Enter') {
            const query = searchInput.value;
            fetchSuggestions(query).then(suggestions => {
                if (suggestions.length > 0) {
                    setMapLocation(suggestions[0].value);
                }
            });
        }
    });

    function setMapLocation(coords) {
        const [lng, lat] = coords;
        map.setCenter([lng, lat]);
        map.setZoom(15);

        marker.setLngLat([lng, lat]);

        console.log({
            location: coords,
            zoom: map.getZoom()
        });
    }

    predictBtn.addEventListener('click', async () => {
        const center = map.getCenter();
        const zoom = 15;
        map.setZoom(zoom);
        marker.setLngLat([center.lng, center.lat]);

        console.log({
            location: [center.lng, center.lat],
            zoom: zoom
        });

        const response = await fetch('/satellite_predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                location: [center.lng, center.lat],
                zoom: zoom
            })
        });

        const data = await response.json();

        // Satellite Prediction
        const satelliteProbability = data.satellite_probability;
        const satelliteStatus = data.satellite_status;

        const satellitePredictionResult = document.getElementById('satellitePredictionResult');
        const satelliteConfidenceBar = document.getElementById('satelliteConfidenceBar');
        const satelliteConfidenceText = document.getElementById('satelliteConfidenceText');

        satellitePredictionResult.textContent = satelliteStatus ? 'THERE IS A WILDFIRE (SATELLITE)' : 'THERE IS NO WILDFIRE (SATELLITE)';
        satelliteConfidenceBar.style.width = `${satelliteProbability}%`;
        satelliteConfidenceBar.classList
            .remove('bg-red-500', 'bg-green-500');
        satelliteConfidenceBar.classList.add(satelliteStatus ? 'bg-red-500' : 'bg-green-500');
        satelliteConfidenceText.textContent = `Confidence: ${satelliteProbability}%`;

        // Weather Prediction
        const weatherProbability = data.weather_probability;
        const weatherStatus = data.weather_status;

        const weatherPredictionResult = document.getElementById('weatherPredictionResult');
        const weatherConfidenceBar = document.getElementById('weatherConfidenceBar');
        const weatherConfidenceText = document.getElementById('weatherConfidenceText');

        weatherPredictionResult.textContent = weatherStatus ? 'THERE IS A WILDFIRE (WEATHER)' : 'THERE IS NO WILDFIRE (WEATHER)';
        weatherConfidenceBar.style.width = `${weatherProbability}%`;
        weatherConfidenceBar.classList.remove('bg-red-500', 'bg-green-500');
        weatherConfidenceBar.classList.add(weatherStatus ? 'bg-red-500' : 'bg-green-500');
        weatherConfidenceText.textContent = `Confidence: ${weatherProbability}%`;

        // Combined Prediction
        const averageProbability = data.average_probability;
        const averageStatus = data.average_status;

        const combinedPredictionResult = document.getElementById('combinedPredictionResult');
        const combinedConfidenceBar = document.getElementById('combinedConfidenceBar');
        const combinedConfidenceText = document.getElementById('combinedConfidenceText');

        combinedPredictionResult.textContent = averageStatus ? 'THERE IS A WILDFIRE (COMBINED)' : 'THERE IS NO WILDFIRE (COMBINED)';
        combinedConfidenceBar.style.width = `${averageProbability}%`;
        combinedConfidenceBar.classList.remove('bg-red-500', 'bg-green-500');
        combinedConfidenceBar.classList.add(averageStatus ? 'bg-red-500' : 'bg-green-500');
        combinedConfidenceText.textContent = `Confidence: ${averageProbability}%`;
    });
});
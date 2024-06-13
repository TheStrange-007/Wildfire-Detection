document.addEventListener("DOMContentLoaded", () => {
    const map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/streets-v11',
        center: [0, 0],
        zoom: 2
    });

    const searchInput = document.getElementById('search');
    const searchBtn = document.getElementById('searchBtn');
    const suggestionsContainer = document.getElementById('suggestions');
    const alertForm = document.getElementById('alertForm');
    const messageDiv = document.getElementById('message');

    let marker = new mapboxgl.Marker({ draggable: true })
        .setLngLat([0, 0])
        .addTo(map);

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
            event.preventDefault();
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
    }

    alertForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const email = document.getElementById('email').value;
        const center = map.getCenter();

        if (!email || !center) {
            messageDiv.innerText = "Please provide your email and select a location.";
            return;
        }

        fetch('/alert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                latitude: center.lat,
                longitude: center.lng
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                messageDiv.innerText = "Alert subscription successful! You will now receive wildfire alerts.";
                messageDiv.classList.remove('text-red-500');
                messageDiv.classList.add('text-green-500');
            } else {
                messageDiv.innerText = data.message || "An unexpected error occurred. Please try again later.";
                messageDiv.classList.remove('text-green-500');
                messageDiv.classList.add('text-red-500');
            }
        })
        .catch((error) => {
            messageDiv.innerText = "An unexpected error occurred. Please try again later.";
            messageDiv.classList.remove('text-green-500');
            messageDiv.classList.add('text-red-500');
            console.error('Error:', error);
        });        
    });
});

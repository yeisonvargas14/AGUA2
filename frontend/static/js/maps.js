/**
 * AquaFlow — Google Maps + Geolocation for Checkout
 * Validates the user is within the Comarapa municipality delivery zone.
 */

let map;
let marker;
let selectedLat = null;
let selectedLng = null;

// Called by Google Maps API after loading
function initMap() {
    const comarapaCenter = { lat: DEFAULT_LAT, lng: DEFAULT_LNG };

    map = new google.maps.Map(document.getElementById('map'), {
        center: comarapaCenter,
        zoom: 13,
        mapTypeId: 'roadmap',
        styles: [
            { featureType: 'poi', elementType: 'labels', stylers: [{ visibility: 'off' }] },
            { featureType: 'transit', elementType: 'labels', stylers: [{ visibility: 'off' }] }
        ]
    });

    // Draw the delivery zone polygon on the map
    const comarapaZone = new google.maps.Polygon({
        paths: [
            { lat: -17.915000, lng: -64.515000 },
            { lat: -17.895000, lng: -64.510000 },
            { lat: -17.880000, lng: -64.495000 },
            { lat: -17.882000, lng: -64.475000 },
            { lat: -17.900000, lng: -64.460000 },
            { lat: -17.920000, lng: -64.465000 },
            { lat: -17.935000, lng: -64.485000 },
            { lat: -17.930000, lng: -64.505000 },
        ],
        strokeColor: '#6366f1',
        strokeOpacity: 0.8,
        strokeWeight: 2,
        fillColor: '#6366f1',
        fillOpacity: 0.1
    });
    comarapaZone.setMap(map);

    // Allow clicking on the map to set delivery location
    map.addListener('click', function(event) {
        const lat = event.latLng.lat();
        const lng = event.latLng.lng();
        placeMarker(lat, lng);
        validateLocation(lat, lng);
    });

    // Try auto-detect via GPS
    if (navigator.geolocation) {
        showGeoFeedback('Detectando tu ubicación...', 'info');
        navigator.geolocation.getCurrentPosition(
            function(pos) {
                const lat = pos.coords.latitude;
                const lng = pos.coords.longitude;
                placeMarker(lat, lng);
                map.setCenter({ lat, lng });
                validateLocation(lat, lng);
            },
            function(err) {
                showGeoFeedback('No se pudo obtener tu ubicación automáticamente. Por favor haz clic en el mapa para marcar tu dirección.', 'warning');
                console.warn('Geolocation error:', err.message);
            },
            { timeout: 10000, maximumAge: 0 }
        );
    } else {
        showGeoFeedback('Tu navegador no soporta geolocalización. Haz clic en el mapa para marcar tu ubicación.', 'warning');
    }
}

function placeMarker(lat, lng) {
    selectedLat = lat;
    selectedLng = lng;

    if (marker) {
        marker.setPosition({ lat, lng });
    } else {
        marker = new google.maps.Marker({
            position: { lat, lng },
            map: map,
            title: 'Tu dirección de entrega',
            animation: google.maps.Animation.DROP,
            icon: {
                url: 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png'
            }
        });
    }

    // Fill hidden fields
    const latInput = document.getElementById('id_lat');
    const lngInput = document.getElementById('id_lng');
    if (latInput) latInput.value = lat.toFixed(6);
    if (lngInput) lngInput.value = lng.toFixed(6);
}

function validateLocation(lat, lng) {
    showGeoFeedback('Validando si tu ubicación está dentro de Comarapa...', 'info');

    fetch(VALIDATE_LOC_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN
        },
        body: JSON.stringify({ lat: lat, lng: lng })
    })
    .then(response => response.json())
    .then(data => {
        const submitBtn = document.getElementById('btn-submit');

        if (data.valid) {
            showGeoFeedback(
                '<i class="fa-solid fa-circle-check"></i> ¡Ubicación válida! Estás dentro del municipio de Comarapa. Puedes continuar con tu pedido.',
                'success'
            );
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fa-solid fa-circle-check"></i> Confirmar Ubicación y Realizar Pedido';
            }
        } else {
            showGeoFeedback(
                '<i class="fa-solid fa-circle-exclamation"></i> <strong>Fuera del área de cobertura:</strong> Tu ubicación no está dentro del municipio de Comarapa. El servicio de entrega a domicilio solo está disponible en este municipio. Por favor, contacta a una agencia cercana.',
                'danger'
            );
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-ban"></i> Fuera del área de entrega';
            }
        }
    })
    .catch(err => {
        showGeoFeedback('Error al validar la ubicación. Por favor intenta de nuevo.', 'warning');
        console.error('Validation error:', err);
    });
}

function showGeoFeedback(message, type) {
    const el = document.getElementById('geo-status');
    if (!el) return;

    const colorMap = {
        'success': '#d1fae5',
        'danger': '#fee2e2',
        'warning': '#fef3c7',
        'info': '#dbeafe'
    };
    const textMap = {
        'success': '#065f46',
        'danger': '#991b1b',
        'warning': '#92400e',
        'info': '#1e3a5f'
    };

    el.style.display = 'block';
    el.style.backgroundColor = colorMap[type] || '#f0f4ff';
    el.style.color = textMap[type] || '#333';
    el.style.border = `1px solid ${type === 'danger' ? '#fca5a5' : type === 'success' ? '#6ee7b7' : '#bfdbfe'}`;
    el.innerHTML = message;
}

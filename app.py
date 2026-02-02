from fasthtml.common import *
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

app, rt = fast_app(
    pico=False,
    hdrs=[
        Script(src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"),
        Link(rel="stylesheet", href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css"),
        Script(src=f"https://maps.googleapis.com/maps/api/js?key={GOOGLE_PLACES_API_KEY}&libraries=places"),
        Style("""
            html, body { margin: 0; padding: 0; width: 100%; height: 100%; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
            #map { width: 100%; height: 100vh; }
            #panel {
                position: absolute; top: 10px; left: 10px; z-index: 1000;
                background: white; border-radius: 8px; padding: 16px;
                width: 300px; box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            }
            #panel h3 { margin-bottom: 12px; font-size: 16px; }
            #panel label { font-size: 13px; color: #555; display: block; margin-bottom: 2px; }
            #panel input[type=text] {
                width: 100%; padding: 8px 10px; border: 1px solid #ddd;
                border-radius: 4px; font-size: 14px; margin-bottom: 4px;
                box-sizing: border-box;
            }
            #panel input[type=text]:focus { outline: none; border-color: #4285f4; }
            .loc-btn {
                background: none; border: none; color: #4285f4; font-size: 12px;
                cursor: pointer; padding: 0; margin-bottom: 10px; display: inline-block;
            }
            .loc-btn:hover { text-decoration: underline; }
            #get-dir {
                width: 100%; padding: 10px; background: #4285f4; color: white;
                border: none; border-radius: 4px; font-size: 14px; cursor: pointer;
                margin-top: 4px;
            }
            #get-dir:hover { background: #3367d6; }
            #route-info {
                margin-top: 12px; padding-top: 12px; border-top: 1px solid #eee;
                font-size: 14px; color: #333; display: none;
            }
            .pac-container { z-index: 1002 !important; }
            .pac-container::after { display: none !important; }
        """),
    ],
)

http_client = httpx.AsyncClient(timeout=10.0)


@rt("/")
def get():
    return Title("Pittsburgh Walking Directions"), Div(
        Div(
            H3("Walking Directions"),
            Label("From", _for="from-input"),
            Input(type="text", id="from-input", placeholder="Starting point"),
            Button("Use my location", cls="loc-btn", id="use-loc"),
            Label("To", _for="to-input"),
            Input(type="text", id="to-input", placeholder="Destination"),
            Button("Get Directions", id="get-dir"),
            Div(id="route-info"),
            id="panel",
        ),
        Div(id="map"),
    ), Script(_map_script())


@rt("/route")
async def get(start_lat: float, start_lng: float, end_lat: float, end_lng: float):
    coords = f"{start_lng},{start_lat};{end_lng},{end_lat}"
    resp = await http_client.get(
        f"https://router.project-osrm.org/route/v1/foot/{coords}",
        params={
            "overview": "full",
            "geometries": "geojson",
            "steps": "true",
        },
    )
    return Response(resp.text, media_type="application/json")


def _map_script():
    return """
document.addEventListener('DOMContentLoaded', function() {
    const map = new maplibregl.Map({
        container: 'map',
        style: {
            version: 8,
            sources: {
                osm: {
                    type: 'raster',
                    tiles: [
                        'https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png',
                        'https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png',
                        'https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png'
                    ],
                    tileSize: 256,
                    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
                }
            },
            layers: [{
                id: 'osm',
                type: 'raster',
                source: 'osm',
            }]
        },
        center: [-79.9959, 40.4406],
        zoom: 12,
    });

    map.addControl(new maplibregl.NavigationControl());

    let routeSourceAdded = false;
    let startMarker = null;
    let endMarker = null;
    let startCoords = null;
    let endCoords = null;

    const fromInput = document.getElementById('from-input');
    const toInput = document.getElementById('to-input');
    const getDirBtn = document.getElementById('get-dir');
    const useLocBtn = document.getElementById('use-loc');
    const routeInfo = document.getElementById('route-info');

    // Pittsburgh bounds for biasing
    const pittsBounds = new google.maps.LatLngBounds(
        new google.maps.LatLng(40.2, -80.2),
        new google.maps.LatLng(40.6, -79.8)
    );

    // Google Places Autocomplete on From input
    const fromAC = new google.maps.places.Autocomplete(fromInput, {
        bounds: pittsBounds,
        fields: ['geometry', 'name'],
    });
    fromAC.addListener('place_changed', () => {
        const place = fromAC.getPlace();
        if (place.geometry) {
            startCoords = { lat: place.geometry.location.lat(), lng: place.geometry.location.lng() };
        }
    });

    // Google Places Autocomplete on To input
    const toAC = new google.maps.places.Autocomplete(toInput, {
        bounds: pittsBounds,
        fields: ['geometry', 'name'],
    });
    toAC.addListener('place_changed', () => {
        const place = toAC.getPlace();
        if (place.geometry) {
            endCoords = { lat: place.geometry.location.lat(), lng: place.geometry.location.lng() };
        }
    });

    // --- Use my location ---
    useLocBtn.addEventListener('click', () => {
        if (!navigator.geolocation) {
            alert('Geolocation not supported by your browser');
            return;
        }
        useLocBtn.textContent = 'Locating...';
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                startCoords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
                fromInput.value = startCoords.lat.toFixed(5) + ', ' + startCoords.lng.toFixed(5);
                useLocBtn.textContent = 'Use my location';
            },
            (err) => {
                alert('Could not get location: ' + err.message);
                useLocBtn.textContent = 'Use my location';
            },
            { enableHighAccuracy: true }
        );
    });

    // --- Get Directions ---
    getDirBtn.addEventListener('click', async () => {
        if (!startCoords || !endCoords) {
            alert('Please select both a starting point and destination from the suggestions.');
            return;
        }

        getDirBtn.textContent = 'Loading...';
        getDirBtn.disabled = true;

        try {
            const url = '/route?start_lat=' + startCoords.lat + '&start_lng=' + startCoords.lng
                      + '&end_lat=' + endCoords.lat + '&end_lng=' + endCoords.lng;
            const resp = await fetch(url);
            const data = await resp.json();

            if (!data.routes || !data.routes.length) {
                alert('No route found.');
                return;
            }

            const route = data.routes[0];
            const geojson = route.geometry;

            // Remove old markers
            if (startMarker) startMarker.remove();
            if (endMarker) endMarker.remove();

            // Add/update route source and layer
            if (routeSourceAdded) {
                map.getSource('route').setData(geojson);
            } else {
                map.addSource('route', { type: 'geojson', data: geojson });
                map.addLayer({
                    id: 'route',
                    type: 'line',
                    source: 'route',
                    layout: { 'line-join': 'round', 'line-cap': 'round' },
                    paint: { 'line-color': '#4285f4', 'line-width': 5, 'line-opacity': 0.8 },
                });
                routeSourceAdded = true;
            }

            // Markers
            startMarker = new maplibregl.Marker({ color: '#34a853' })
                .setLngLat([startCoords.lng, startCoords.lat])
                .setPopup(new maplibregl.Popup().setText('Start'))
                .addTo(map);
            endMarker = new maplibregl.Marker({ color: '#ea4335' })
                .setLngLat([endCoords.lng, endCoords.lat])
                .setPopup(new maplibregl.Popup().setText('Destination'))
                .addTo(map);

            // Fit bounds to route
            const coords = geojson.coordinates;
            const bounds = coords.reduce((b, c) => b.extend(c), new maplibregl.LngLatBounds(coords[0], coords[0]));
            map.fitBounds(bounds, { padding: 60 });

            // Show distance and time
            const distMiles = (route.distance / 1609.34).toFixed(1);
            const mins = Math.round(route.duration / 60);
            routeInfo.style.display = 'block';
            routeInfo.innerHTML = '<strong>' + distMiles + ' mi</strong> &middot; <strong>' + mins + ' min</strong> walking';

        } catch (err) {
            alert('Error getting route: ' + err.message);
        } finally {
            getDirBtn.textContent = 'Get Directions';
            getDirBtn.disabled = false;
        }
    });
});
"""


serve(port=5002)

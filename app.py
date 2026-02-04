from fasthtml.common import *
import httpx
import json
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
            #mode-selector {
                display: flex; justify-content: center; gap: 8px;
                margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #eee;
            }
            .mode-btn {
                background: none; border: 2px solid transparent; border-radius: 8px;
                padding: 8px 16px; cursor: pointer; display: flex; align-items: center;
                gap: 4px; font-size: 12px; color: #666; transition: all 0.2s;
            }
            .mode-btn:hover { background: #f0f0f0; }
            .mode-btn.active { border-color: #4285f4; color: #4285f4; background: #e8f0fe; }
            .mode-btn svg { width: 20px; height: 20px; }
            #panel label { font-size: 13px; color: #555; display: block; margin-bottom: 2px; }
            #panel input[type=text] {
                width: 100%; padding: 8px 10px; border: 1px solid #ddd;
                border-radius: 4px; font-size: 14px; margin-bottom: 4px;
                box-sizing: border-box;
            }
            #panel input[type=text]:focus { outline: none; border-color: #4285f4; }
            .input-wrap {
                position: relative; margin-bottom: 4px;
            }
            .input-wrap input[type=text] { padding-right: 32px; margin-bottom: 0; }
            .loc-btn {
                position: absolute; right: 4px; top: 50%; transform: translateY(-50%);
                background: none; border: none; cursor: pointer; padding: 4px;
                color: #666; display: flex; align-items: center; justify-content: center;
            }
            .loc-btn:hover { color: #4285f4; }
            .loc-btn svg { width: 18px; height: 18px; }
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
            #steps-list {
                margin-top: 10px; padding: 0; list-style: none; font-size: 13px;
                max-height: 300px; overflow-y: auto;
            }
            #steps-list li {
                padding: 8px 0; border-bottom: 1px solid #f0f0f0;
                display: flex; align-items: flex-start; gap: 8px;
            }
            #steps-list li:last-child { border-bottom: none; }
            .step-icon {
                flex-shrink: 0; width: 20px; height: 20px; background: #e8f0fe;
                border-radius: 50%; display: flex; align-items: center; justify-content: center;
                font-size: 10px; color: #4285f4; font-weight: bold; margin-top: 1px;
            }
            .step-text { flex: 1; line-height: 1.4; }
            .step-dist { color: #888; font-size: 12px; }

            /* Transit timeline */
            .timeline { margin-top: 10px; padding: 4px 0 0 0; list-style: none; max-height: 350px; overflow-y: auto; }
            .tl-step { display: flex; gap: 10px; position: relative; padding-bottom: 0; }
            .tl-time {
                flex-shrink: 0; width: 42px; font-size: 11px; color: #888;
                text-align: right; padding-top: 2px; font-weight: 500;
            }
            .tl-track { display: flex; flex-direction: column; align-items: center; flex-shrink: 0; width: 20px; }
            .tl-dot {
                width: 10px; height: 10px; border-radius: 50%; background: #9aa0a6;
                border: 2px solid white; box-shadow: 0 0 0 1px #9aa0a6; flex-shrink: 0; z-index: 1;
            }
            .tl-dot.transit { background: #4285f4; box-shadow: 0 0 0 1px #4285f4; }
            .tl-line { width: 3px; flex: 1; background: #dadce0; min-height: 20px; }
            .tl-line.walk { background: repeating-linear-gradient(to bottom, #9aa0a6 0, #9aa0a6 4px, transparent 4px, transparent 8px); width: 3px; }
            .tl-line.transit-line { background: #4285f4; }
            .tl-content { flex: 1; padding-bottom: 14px; font-size: 13px; line-height: 1.4; }
            .tl-content .tl-label { color: #333; }
            .tl-content .tl-sub { color: #888; font-size: 12px; margin-top: 2px; }
            .transit-badge {
                display: inline-flex; align-items: center; gap: 4px;
                padding: 2px 8px; border-radius: 4px; font-size: 12px;
                font-weight: 700; margin-right: 6px; vertical-align: middle;
            }
            .pac-container { z-index: 1002 !important; }
            .pac-container::after { display: none !important; }
        """),
    ],
)

http_client = httpx.AsyncClient(timeout=10.0)


@rt("/")
def get():
    return Title("Pittsburgh Directions"), Div(
        Div(
            Div(
                Button(
                    NotStr('<svg viewBox="0 0 24 24" fill="currentColor"><path d="M13.5 5.5c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zM9.8 8.9L7 23h2.1l1.8-8 2.1 2v6h2v-7.5l-2.1-2 .6-3C14.8 12 16.8 13 19 13v-2c-1.9 0-3.5-1-4.3-2.4l-1-1.6c-.4-.6-1-1-1.7-1-.3 0-.5.1-.8.1L6 8.3V13h2V9.6l1.8-.7"/></svg>'),
                    "Walk",
                    cls="mode-btn active", id="mode-walk", data_mode="foot",
                ),
                Button(
                    NotStr('<svg viewBox="0 0 24 24" fill="currentColor"><path d="M15.5 5.5c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zM5 12c-2.8 0-5 2.2-5 5s2.2 5 5 5 5-2.2 5-5-2.2-5-5-5zm0 8.5c-1.9 0-3.5-1.6-3.5-3.5s1.6-3.5 3.5-3.5 3.5 1.6 3.5 3.5-1.6 3.5-3.5 3.5zm5.8-10l2.4-2.4.8.8c1.3 1.3 3 2.1 5 2.1V9c-1.5 0-2.7-.6-3.6-1.5l-1.9-1.9c-.5-.4-1-.6-1.6-.6s-1.1.2-1.4.6L7.8 8.4c-.4.4-.6.9-.6 1.4 0 .6.2 1.1.6 1.4L11 14v5h2v-6.2l-2.2-2.3zM19 12c-2.8 0-5 2.2-5 5s2.2 5 5 5 5-2.2 5-5-2.2-5-5-5zm0 8.5c-1.9 0-3.5-1.6-3.5-3.5s1.6-3.5 3.5-3.5 3.5 1.6 3.5 3.5-1.6 3.5-3.5 3.5z"/></svg>'),
                    "Bike",
                    cls="mode-btn", id="mode-bike", data_mode="bike",
                ),
                Button(
                    NotStr('<svg viewBox="0 0 24 24" fill="currentColor"><path d="M4 16c0 .88.39 1.67 1 2.22V20c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h8v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1.78c.61-.55 1-1.34 1-2.22V6c0-3.5-3.58-4-8-4s-8 .5-8 4v10zm3.5 1c-.83 0-1.5-.67-1.5-1.5S6.67 14 7.5 14s1.5.67 1.5 1.5S8.33 17 7.5 17zm9 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm1.5-6H6V6h12v5z"/></svg>'),
                    "Transit",
                    cls="mode-btn", id="mode-transit", data_mode="transit",
                ),
                id="mode-selector",
            ),
            Label("From", _for="from-input"),
            Div(
                Input(type="text", id="from-input", placeholder="Starting point"),
                Button(
                    NotStr('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/></svg>'),
                    cls="loc-btn", id="use-loc", title="Use my location",
                ),
                cls="input-wrap",
            ),
            Label("To", _for="to-input"),
            Input(type="text", id="to-input", placeholder="Destination"),
            Button("Get Directions", id="get-dir"),
            Div(id="route-info"),
            id="panel",
        ),
        Div(id="map"),
    ), Script(_map_script())


OSRM_PROFILES = {"foot": "foot", "bike": "bike"}


def _decode_polyline(encoded):
    """Decode a Google encoded polyline into a list of [lng, lat] coords."""
    points = []
    idx, lat, lng = 0, 0, 0
    while idx < len(encoded):
        for is_lng in (False, True):
            shift, result = 0, 0
            while True:
                b = ord(encoded[idx]) - 63
                idx += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if (result & 1) else (result >> 1)
            if is_lng:
                lng += delta
            else:
                lat += delta
        points.append([lng / 1e5, lat / 1e5])
    return points


@rt("/route")
async def get(start_lat: float, start_lng: float, end_lat: float, end_lng: float, mode: str = "foot"):
    if mode == "transit":
        return await _google_transit_route(start_lat, start_lng, end_lat, end_lng)

    profile = OSRM_PROFILES.get(mode, "foot")
    coords = f"{start_lng},{start_lat};{end_lng},{end_lat}"
    resp = await http_client.get(
        f"https://router.project-osrm.org/route/v1/{profile}/{coords}",
        params={
            "overview": "full",
            "geometries": "geojson",
            "steps": "true",
        },
    )
    return Response(resp.text, media_type="application/json")


async def _google_transit_route(start_lat, start_lng, end_lat, end_lng):
    resp = await http_client.post(
        "https://routes.googleapis.com/directions/v2:computeRoutes",
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
            "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs.steps.navigationInstruction,routes.legs.steps.distanceMeters,routes.legs.steps.staticDuration,routes.legs.steps.transitDetails,routes.legs.steps.travelMode,routes.legs.steps.polyline.encodedPolyline",
        },
        json={
            "origin": {"location": {"latLng": {"latitude": start_lat, "longitude": start_lng}}},
            "destination": {"location": {"latLng": {"latitude": end_lat, "longitude": end_lng}}},
            "travelMode": "TRANSIT",
        },
    )
    data = resp.json()
    if not data.get("routes"):
        return Response(json.dumps({"routes": [], "error": "No transit routes found"}), media_type="application/json")

    groute = data["routes"][0]
    leg = groute["legs"][0]

    # Decode polyline to GeoJSON
    coords = _decode_polyline(groute["polyline"]["encodedPolyline"])
    geometry = {"type": "LineString", "coordinates": coords}

    # Parse duration (e.g. "1033s" -> 1033)
    duration = int(groute["duration"].rstrip("s"))

    # Convert steps — group consecutive WALK steps, keep TRANSIT steps separate
    steps = []
    for step in leg["steps"]:
        instruction = step.get("navigationInstruction", {}).get("instructions", "Continue")
        travel_mode = step.get("travelMode", "WALK")
        step_duration = int(step.get("staticDuration", "0s").rstrip("s"))

        # Per-step polyline
        step_polyline = None
        sp = step.get("polyline", {}).get("encodedPolyline")
        if sp:
            step_polyline = {"type": "LineString", "coordinates": _decode_polyline(sp)}

        td = step.get("transitDetails")
        transit_info = None
        if td:
            line = td.get("transitLine", {})
            stop_details = td.get("stopDetails", {})
            transit_info = {
                "line_short": line.get("nameShort") or line.get("name", ""),
                "line_name": line.get("name", ""),
                "vehicle": line.get("vehicle", {}).get("name", {}).get("text", ""),
                "color": line.get("color", "#4285f4"),
                "text_color": line.get("textColor", "#ffffff"),
                "departure_stop": stop_details.get("departureStop", {}).get("name", ""),
                "arrival_stop": stop_details.get("arrivalStop", {}).get("name", ""),
                "departure_time": stop_details.get("departureTime", ""),
                "arrival_time": stop_details.get("arrivalTime", ""),
                "stop_count": td.get("stopCount", 0),
                "headsign": td.get("headsign", ""),
            }

        steps.append({
            "distance": step.get("distanceMeters", 0),
            "duration": step_duration,
            "travel_mode": travel_mode,
            "maneuver": {"instruction": instruction},
            "polyline": step_polyline,
            "transit": transit_info,
        })

    result = {
        "routes": [{
            "distance": groute["distanceMeters"],
            "duration": duration,
            "geometry": geometry,
            "legs": [{"steps": steps}],
        }],
    }
    return Response(json.dumps(result), media_type="application/json")


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

    let routeLayerIds = [];
    let routeSourceIds = [];
    let startMarker = null;
    let endMarker = null;
    let startCoords = null;
    let endCoords = null;
    let currentMode = 'foot';

    const fromInput = document.getElementById('from-input');
    const toInput = document.getElementById('to-input');
    const getDirBtn = document.getElementById('get-dir');
    const useLocBtn = document.getElementById('use-loc');
    const routeInfo = document.getElementById('route-info');

    // Mode selector
    const modeBtns = document.querySelectorAll('.mode-btn');
    modeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            modeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentMode = btn.dataset.mode;
            // Re-fetch route if we already have coords
            if (startCoords && endCoords) {
                getDirBtn.click();
            }
        });
    });

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
        useLocBtn.style.opacity = '0.4';
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                startCoords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
                fromInput.value = startCoords.lat.toFixed(5) + ', ' + startCoords.lng.toFixed(5);
                useLocBtn.style.opacity = '1';
            },
            (err) => {
                alert('Could not get location: ' + err.message);
                useLocBtn.style.opacity = '1';
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
                      + '&end_lat=' + endCoords.lat + '&end_lng=' + endCoords.lng
                      + '&mode=' + currentMode;
            const resp = await fetch(url);
            const data = await resp.json();

            if (!data.routes || !data.routes.length) {
                alert('No route found.');
                return;
            }

            const route = data.routes[0];
            const geojson = route.geometry;
            const steps = route.legs[0].steps;

            // Remove old markers & layers
            if (startMarker) startMarker.remove();
            if (endMarker) endMarker.remove();
            routeLayerIds.forEach(id => { if (map.getLayer(id)) map.removeLayer(id); });
            routeSourceIds.forEach(id => { if (map.getSource(id)) map.removeSource(id); });
            routeLayerIds = [];
            routeSourceIds = [];

            // --- Draw route segments ---
            if (currentMode === 'transit') {
                // Per-step segments with different styles
                steps.forEach((step, i) => {
                    if (!step.polyline) return;
                    const srcId = 'route-seg-' + i;
                    const layerId = 'route-seg-layer-' + i;
                    map.addSource(srcId, { type: 'geojson', data: step.polyline });
                    const isTransit = step.travel_mode === 'TRANSIT';
                    const color = isTransit ? (step.transit && step.transit.color !== '#ffffff' ? step.transit.color : '#4285f4') : '#9aa0a6';
                    const paint = isTransit
                        ? { 'line-color': color, 'line-width': 5, 'line-opacity': 0.9 }
                        : { 'line-color': '#9aa0a6', 'line-width': 4, 'line-opacity': 0.7, 'line-dasharray': [2, 2] };
                    map.addLayer({
                        id: layerId, type: 'line', source: srcId,
                        layout: { 'line-join': 'round', 'line-cap': 'round' },
                        paint: paint,
                    });
                    routeSourceIds.push(srcId);
                    routeLayerIds.push(layerId);
                });
            } else {
                // Single line for walking/biking
                const srcId = 'route-main';
                const layerId = 'route-main-layer';
                map.addSource(srcId, { type: 'geojson', data: geojson });
                const color = currentMode === 'bike' ? '#0d904f' : '#4285f4';
                map.addLayer({
                    id: layerId, type: 'line', source: srcId,
                    layout: { 'line-join': 'round', 'line-cap': 'round' },
                    paint: { 'line-color': color, 'line-width': 5, 'line-opacity': 0.8 },
                });
                routeSourceIds.push(srcId);
                routeLayerIds.push(layerId);
            }

            // Markers with labels
            const startLabel = fromInput.value || 'Start';
            const endLabel = toInput.value || 'Destination';
            startMarker = new maplibregl.Marker({ color: '#34a853' })
                .setLngLat([startCoords.lng, startCoords.lat])
                .setPopup(new maplibregl.Popup({ offset: 25 }).setText(startLabel))
                .addTo(map);
            startMarker.togglePopup();
            endMarker = new maplibregl.Marker({ color: '#ea4335' })
                .setLngLat([endCoords.lng, endCoords.lat])
                .setPopup(new maplibregl.Popup({ offset: 25 }).setText(endLabel))
                .addTo(map);
            endMarker.togglePopup();

            // Fit bounds to route
            const coords = geojson.coordinates;
            const bounds = coords.reduce((b, c) => b.extend(c), new maplibregl.LngLatBounds(coords[0], coords[0]));
            map.fitBounds(bounds, { padding: 60 });

            // Show distance and time
            const distMiles = (route.distance / 1609.34).toFixed(1);
            const mins = Math.round(route.duration / 60);
            routeInfo.style.display = 'block';
            const modeLabels = { foot: 'walking', bike: 'biking', transit: 'by transit' };
            routeInfo.innerHTML = '<strong>' + distMiles + ' mi</strong> &middot; <strong>' + mins + ' min</strong> ' + (modeLabels[currentMode] || 'walking');

            // --- Render steps ---
            if (currentMode === 'transit') {
                // Timeline view
                let html = '<ul class="timeline">';
                steps.forEach((step, i) => {
                    const isTransit = step.travel_mode === 'TRANSIT';
                    const t = step.transit;

                    // Time label
                    let timeStr = '';
                    if (isTransit && t && t.departure_time) {
                        const d = new Date(t.departure_time);
                        timeStr = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
                    }

                    // Dot & line style
                    const dotCls = isTransit ? 'tl-dot transit' : 'tl-dot';
                    const lineCls = isTransit ? 'tl-line transit-line' : 'tl-line walk';

                    // Content
                    let content = '';
                    if (isTransit && t) {
                        const badgeColor = (t.color && t.color !== '#ffffff') ? t.color : '#4285f4';
                        const textColor = (t.text_color && t.text_color !== '#000000') ? t.text_color : '#fff';
                        content = '<span class="transit-badge" style="background:' + badgeColor + ';color:' + textColor + '">'
                            + t.line_short + '</span>'
                            + '<span class="tl-label">' + t.headsign + '</span>'
                            + '<div class="tl-sub">' + t.departure_stop + ' → ' + t.arrival_stop
                            + ' &middot; ' + t.stop_count + ' stops</div>';
                    } else {
                        const stepDist = step.distance >= 1000
                            ? (step.distance / 1609.34).toFixed(1) + ' mi'
                            : Math.round(step.distance * 3.281) + ' ft';
                        const walkMins = Math.round(step.duration / 60);
                        content = '<span class="tl-label">Walk ' + stepDist + '</span>'
                            + '<div class="tl-sub">' + step.maneuver.instruction + ' &middot; ' + walkMins + ' min</div>';
                    }

                    // Check what comes after this step
                    const next = steps[i + 1];
                    const isLast = !next && !(isTransit && t && t.arrival_time);

                    html += '<div class="tl-step">'
                        + '<div class="tl-time">' + timeStr + '</div>'
                        + '<div class="tl-track"><div class="' + dotCls + '"></div>'
                        + (isLast ? '' : '<div class="' + lineCls + '"></div>')
                        + '</div>'
                        + '<div class="tl-content">' + content + '</div>'
                        + '</div>';

                    // Arrival time for transit step
                    if (isTransit && t && t.arrival_time) {
                        const arrD = new Date(t.arrival_time);
                        const arrStr = arrD.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
                        if (!next || next.travel_mode !== 'TRANSIT') {
                            const hasMore = !!next;
                            html += '<div class="tl-step">'
                                + '<div class="tl-time">' + arrStr + '</div>'
                                + '<div class="tl-track"><div class="tl-dot transit"></div>'
                                + (hasMore ? '<div class="tl-line walk"></div>' : '') + '</div>'
                                + '<div class="tl-content"><span class="tl-label">Arrive ' + t.arrival_stop + '</span></div>'
                                + '</div>';
                        }
                    }
                });
                html += '</ul>';
                routeInfo.innerHTML += html;
            } else {
                // Simple step list for walk/bike
                let stepsHtml = '<ul id="steps-list">';
                steps.forEach((step, i) => {
                    const stepDist = step.distance >= 1000
                        ? (step.distance / 1609.34).toFixed(1) + ' mi'
                        : Math.round(step.distance * 3.281) + ' ft';
                    const instruction = step.maneuver.instruction || step.name || 'Continue';
                    stepsHtml += '<li>'
                        + '<div class="step-icon">' + (i + 1) + '</div>'
                        + '<div class="step-text">' + instruction
                        + ' <span class="step-dist">(' + stepDist + ')</span></div>'
                        + '</li>';
                });
                stepsHtml += '</ul>';
                routeInfo.innerHTML += stepsHtml;
            }

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

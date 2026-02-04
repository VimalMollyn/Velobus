from fasthtml.common import *
import asyncio
import copy
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
                width: 380px; box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            }
            #mode-selector {
                display: flex; justify-content: center; gap: 4px;
                margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #eee;
                flex-wrap: wrap;
            }
            .mode-btn {
                background: none; border: 2px solid transparent; border-radius: 8px;
                padding: 8px 12px; cursor: pointer; display: flex; align-items: center;
                gap: 4px; font-size: 11px; color: #666; transition: all 0.2s;
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
            .tl-dot.bike { background: #0d904f; box-shadow: 0 0 0 1px #0d904f; }
            .tl-line.bike-line { background: #0d904f; }
            .tl-content { flex: 1; padding-bottom: 14px; font-size: 13px; line-height: 1.4; }
            .tl-content .tl-label { color: #333; }
            .tl-content .tl-sub { color: #888; font-size: 12px; margin-top: 2px; }
            .transit-badge {
                display: inline-flex; align-items: center; gap: 4px;
                padding: 2px 8px; border-radius: 4px; font-size: 12px;
                font-weight: 700; margin-right: 6px; vertical-align: middle;
            }
            .inputs-row { display: flex; align-items: center; gap: 4px; }
            .inputs-col { flex: 1; min-width: 0; }
            .swap-btn {
                flex-shrink: 0; background: none; border: 1px solid #ddd; border-radius: 50%;
                width: 32px; height: 32px; cursor: pointer; display: flex; align-items: center;
                justify-content: center; color: #666; padding: 0; margin-top: 10px;
                transition: all 0.2s;
            }
            .swap-btn:hover { background: #f0f0f0; color: #4285f4; border-color: #4285f4; }
            .swap-btn svg { width: 20px; height: 20px; }
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
                Button(
                    NotStr('<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C8.14 2 5 3.57 5 6v10c0 1.1.9 2 2 2h1v1c0 .55.45 1 1 1s1-.45 1-1v-1h4v1c0 .55.45 1 1 1s1-.45 1-1v-1h1c1.1 0 2-.9 2-2V6c0-2.43-3.14-4-7-4zm-3.5 14c-.83 0-1.5-.67-1.5-1.5S7.67 13 8.5 13s1.5.67 1.5 1.5S9.33 16 8.5 16zm7 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm1.5-6H7V6h10v4z"/><circle cx="19.5" cy="3.5" r="3.5" fill="#0d904f"/><path d="M18.5 3.5h2M19.5 2.5v2" stroke="white" stroke-width=".8" fill="none"/></svg>'),
                    NotStr("Bike+Bus"),
                    cls="mode-btn", id="mode-bike-transit", data_mode="bike_transit",
                ),
                id="mode-selector",
            ),
            Div(
                Div(
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
                    cls="inputs-col",
                ),
                Button(
                    NotStr('<svg viewBox="0 0 24 24" fill="currentColor"><path d="M16 17.01V10h-2v7.01h-3L15 21l4-3.99h-3zM9 3L5 6.99h3V14h2V6.99h3L9 3z"/></svg>'),
                    cls="swap-btn", id="swap-btn", title="Swap start and destination",
                ),
                cls="inputs-row",
            ),
            Button("Get Directions", id="get-dir"),
            Div(id="route-info"),
            id="panel",
        ),
        Div(id="map"),
    ), Script(_map_script())


GOOGLE_TRAVEL_MODES = {"foot": "WALK", "bike": "BICYCLE"}


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


async def _get_elevation_score(coords):
    """Sample points along a coordinate list and return net elevation impact in meters.
    Positive = net uphill (penalty), negative = net downhill (advantage).
    coords is a list of [lng, lat] pairs."""
    if len(coords) < 2:
        return 0
    # Sample up to 100 evenly spaced points for accuracy
    max_samples = 100
    if len(coords) <= max_samples:
        sampled = coords
    else:
        step = (len(coords) - 1) / (max_samples - 1)
        sampled = [coords[round(i * step)] for i in range(max_samples)]
    locations = "|".join(f"{lat},{lng}" for lng, lat in sampled)
    try:
        resp = await http_client.get(
            "https://maps.googleapis.com/maps/api/elevation/json",
            params={"locations": locations, "key": GOOGLE_PLACES_API_KEY},
        )
        data = resp.json()
        if data.get("status") != "OK":
            return 0
        elevations = [r["elevation"] for r in data["results"]]
        gain = sum(max(0, elevations[i+1] - elevations[i]) for i in range(len(elevations) - 1))
        loss = sum(max(0, elevations[i] - elevations[i+1]) for i in range(len(elevations) - 1))
        return round(gain - loss)
    except Exception:
        return 0


async def _get_bike_route(s_lat, s_lng, e_lat, e_lng):
    """Fetch a bike route via Google Routes API. Returns (geometry, distance_m, duration_s, elevation_score_m) or None."""
    try:
        resp = await http_client.post(
            "https://routes.googleapis.com/directions/v2:computeRoutes",
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
                "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline",
            },
            json={
                "origin": {"location": {"latLng": {"latitude": s_lat, "longitude": s_lng}}},
                "destination": {"location": {"latLng": {"latitude": e_lat, "longitude": e_lng}}},
                "travelMode": "BICYCLE",
            },
        )
        data = resp.json()
        if data.get("routes"):
            r = data["routes"][0]
            coords = _decode_polyline(r["polyline"]["encodedPolyline"])
            geom = {"type": "LineString", "coordinates": coords}
            dist = r.get("distanceMeters", 0)
            dur = int(r["duration"].rstrip("s"))
            elev_gain = await _get_elevation_score(coords)
            return geom, dist, dur, elev_gain
    except Exception:
        pass
    return None


@rt("/route")
async def get(start_lat: float, start_lng: float, end_lat: float, end_lng: float, mode: str = "foot"):
    try:
        if mode == "transit":
            return await _google_transit_route(start_lat, start_lng, end_lat, end_lng)
        if mode == "bike_transit":
            return await _bike_transit_route(start_lat, start_lng, end_lat, end_lng)

        travel_mode = GOOGLE_TRAVEL_MODES.get(mode, "WALK")
        resp = await http_client.post(
            "https://routes.googleapis.com/directions/v2:computeRoutes",
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
                "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs.steps.navigationInstruction,routes.legs.steps.distanceMeters,routes.legs.steps.staticDuration,routes.legs.steps.polyline.encodedPolyline",
            },
            json={
                "origin": {"location": {"latLng": {"latitude": start_lat, "longitude": start_lng}}},
                "destination": {"location": {"latLng": {"latitude": end_lat, "longitude": end_lng}}},
                "travelMode": travel_mode,
            },
        )
        data = resp.json()
        if not data.get("routes"):
            return Response(json.dumps({"routes": [], "error": "No route found"}), media_type="application/json")
        result = {"routes": [_parse_transit_route(data["routes"][0])]}
        return Response(json.dumps(result), media_type="application/json")
    except Exception as e:
        print(f"Route error: {e}")
        return Response(
            json.dumps({"routes": [], "error": str(e)}),
            media_type="application/json",
        )


def _parse_transit_route(groute):
    """Parse a single Google Routes API route into our internal format."""
    leg = groute["legs"][0]
    coords = _decode_polyline(groute["polyline"]["encodedPolyline"])
    geometry = {"type": "LineString", "coordinates": coords}
    duration = int(groute["duration"].rstrip("s"))

    steps = []
    for step in leg["steps"]:
        instruction = step.get("navigationInstruction", {}).get("instructions", "Continue")
        travel_mode = step.get("travelMode", "WALK")
        step_duration = int(step.get("staticDuration", "0s").rstrip("s"))

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

    return {
        "distance": groute.get("distanceMeters", 0),
        "duration": duration,
        "geometry": geometry,
        "legs": [{"steps": steps}],
    }


async def _google_transit_route(start_lat, start_lng, end_lat, end_lng, compute_alternatives=False):
    body = {
        "origin": {"location": {"latLng": {"latitude": start_lat, "longitude": start_lng}}},
        "destination": {"location": {"latLng": {"latitude": end_lat, "longitude": end_lng}}},
        "travelMode": "TRANSIT",
    }
    if compute_alternatives:
        body["computeAlternativeRoutes"] = True

    resp = await http_client.post(
        "https://routes.googleapis.com/directions/v2:computeRoutes",
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
            "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs.steps.navigationInstruction,routes.legs.steps.distanceMeters,routes.legs.steps.staticDuration,routes.legs.steps.transitDetails,routes.legs.steps.travelMode,routes.legs.steps.polyline.encodedPolyline",
        },
        json=body,
    )
    data = resp.json()

    if compute_alternatives:
        # Return list of parsed routes for internal use
        if not data.get("routes"):
            return []
        return [_parse_transit_route(gr) for gr in data["routes"]]

    # Single route mode — return HTTP response for direct use
    if not data.get("routes"):
        return Response(json.dumps({"routes": [], "error": "No transit routes found"}), media_type="application/json")
    result = {"routes": [_parse_transit_route(data["routes"][0])]}
    return Response(json.dumps(result), media_type="application/json")


def _score_route(route):
    """Score a candidate route. Lower is better.
    Penalizes transfers, long bike distances, and uphill biking.
    """
    steps = route["legs"][0]["steps"]
    total_duration = route["duration"]
    num_transfers = sum(1 for s in steps if s["travel_mode"] == "TRANSIT")
    bike_distance = sum(s["distance"] for s in steps if s["travel_mode"] == "BIKE")
    elev_gain = sum(s.get("elevation_score", 0) for s in steps if s["travel_mode"] == "BIKE")
    return (total_duration
            + (num_transfers * 600)
            + max(0, bike_distance - 3218) * 0.5
            + elev_gain * 5)


def _rebuild_overview(route):
    """Rebuild overview geometry and total duration from steps."""
    all_coords = []
    for step in route["legs"][0]["steps"]:
        if step.get("polyline") and step["polyline"].get("coordinates"):
            all_coords.extend(step["polyline"]["coordinates"])
    if all_coords:
        route["geometry"] = {"type": "LineString", "coordinates": all_coords}
    route["duration"] = sum(s.get("duration", 0) for s in route["legs"][0]["steps"])
    route["distance"] = sum(s.get("distance", 0) for s in route["legs"][0]["steps"])


def _format_pure_bike(geometry, distance, duration, elevation_score=0):
    """Wrap a bike route result into transit-compatible response format."""
    return {
        "distance": distance,
        "duration": duration,
        "geometry": geometry,
        "legs": [{"steps": [{
            "distance": distance,
            "duration": duration,
            "travel_mode": "BIKE",
            "maneuver": {"instruction": "Bike to destination"},
            "polyline": geometry,
            "transit": None,
            "elevation_score": elevation_score,
        }]}],
    }


async def _apply_walk_to_bike(route):
    """Variant A: Replace all WALK steps with OSRM bike routes. Returns a new route dict."""
    route = copy.deepcopy(route)
    steps = route["legs"][0]["steps"]

    tasks = []
    walk_indices = []
    for i, step in enumerate(steps):
        if step["travel_mode"] == "WALK" and step.get("polyline"):
            coords = step["polyline"]["coordinates"]
            if len(coords) >= 2:
                s_lng, s_lat = coords[0]
                e_lng, e_lat = coords[-1]
                tasks.append(_get_bike_route(s_lat, s_lng, e_lat, e_lng))
                walk_indices.append(i)

    if tasks:
        results = await asyncio.gather(*tasks)
        for idx, result in zip(walk_indices, results):
            step = steps[idx]
            if result:
                geom, dist, dur, elev = result
                step["polyline"] = geom
                step["distance"] = dist
                step["duration"] = dur
                step["elevation_score"] = elev
            step["travel_mode"] = "BIKE"

    _rebuild_overview(route)
    return route


async def _try_eliminate_short_hops(route):
    """Variant B: For transit segments < 1.5 miles, check if biking through is faster.
    If transit saves < 3 minutes vs biking, eliminate it. Returns a new route dict."""
    route = copy.deepcopy(route)
    steps = route["legs"][0]["steps"]

    SHORT_HOP_THRESHOLD = 2414  # 1.5 miles in meters
    MIN_TIME_SAVINGS = 180  # 3 minutes

    i = 0
    while i < len(steps):
        step = steps[i]
        if step["travel_mode"] != "TRANSIT" or step["distance"] >= SHORT_HOP_THRESHOLD:
            i += 1
            continue

        # Find the bike/walk segments on either side
        prev_idx = i - 1 if i > 0 and steps[i - 1]["travel_mode"] in ("WALK", "BIKE") else None
        next_idx = i + 1 if i + 1 < len(steps) and steps[i + 1]["travel_mode"] in ("WALK", "BIKE") else None

        # Get start coord from prev segment start (or transit start) and end coord from next segment end (or transit end)
        if prev_idx is not None and steps[prev_idx].get("polyline", {}).get("coordinates"):
            s_lng, s_lat = steps[prev_idx]["polyline"]["coordinates"][0]
        elif step.get("polyline", {}).get("coordinates"):
            s_lng, s_lat = step["polyline"]["coordinates"][0]
        else:
            i += 1
            continue

        if next_idx is not None and steps[next_idx].get("polyline", {}).get("coordinates"):
            e_lng, e_lat = steps[next_idx]["polyline"]["coordinates"][-1]
        elif step.get("polyline", {}).get("coordinates"):
            e_lng, e_lat = step["polyline"]["coordinates"][-1]
        else:
            i += 1
            continue

        # Duration of the segments we'd replace
        transit_duration = step["duration"]
        prev_duration = steps[prev_idx]["duration"] if prev_idx is not None else 0
        next_duration = steps[next_idx]["duration"] if next_idx is not None else 0
        combined_duration = transit_duration + prev_duration + next_duration

        bike_result = await _get_bike_route(s_lat, s_lng, e_lat, e_lng)
        if not bike_result:
            i += 1
            continue

        bike_geom, bike_dist, bike_dur, bike_elev = bike_result

        # Only eliminate if transit doesn't save enough time
        if combined_duration - bike_dur < MIN_TIME_SAVINGS:
            # Replace: remove prev, transit, next and insert single bike segment
            new_step = {
                "distance": bike_dist,
                "duration": bike_dur,
                "travel_mode": "BIKE",
                "maneuver": {"instruction": "Bike (skipping short transit hop)"},
                "polyline": bike_geom,
                "transit": None,
                "elevation_score": bike_elev,
            }
            remove_start = prev_idx if prev_idx is not None else i
            remove_end = (next_idx if next_idx is not None else i) + 1
            steps[remove_start:remove_end] = [new_step]
            # Don't increment i — re-check from same position
        else:
            i += 1
        continue

    _rebuild_overview(route)
    return route


async def _bike_transit_route(start_lat, start_lng, end_lat, end_lng):
    """Smart bike+transit routing with multi-candidate evaluation."""
    # Step 1: Parallel data collection
    pure_bike_task = _get_bike_route(start_lat, start_lng, end_lat, end_lng)
    transit_task = _google_transit_route(start_lat, start_lng, end_lat, end_lng, compute_alternatives=True)

    pure_bike_result, transit_routes = await asyncio.gather(pure_bike_task, transit_task)

    candidates = []

    # Step 2: Generate variants for each transit itinerary
    variant_tasks = []
    for tr in transit_routes:
        variant_tasks.append(_apply_walk_to_bike(tr))       # Variant A
        variant_tasks.append(_try_eliminate_short_hops(tr))  # Variant B (on original with walks)

    if variant_tasks:
        variants = await asyncio.gather(*variant_tasks)
        # Variant A and B come in pairs per transit route
        for i in range(0, len(variants), 2):
            variant_a = variants[i]
            candidates.append(variant_a)
            # Also apply hop elimination on the bike-replaced version
            variant_b_on_a = await _try_eliminate_short_hops(variant_a)
            candidates.append(variant_b_on_a)

    # Variant C: Pure bike if < 6 miles (~9656m)
    if pure_bike_result:
        geom, dist, dur, elev = pure_bike_result
        if dist < 9656:
            candidates.append(_format_pure_bike(geom, dist, dur, elev))

    if not candidates:
        # Fallback: return pure bike if available, or error
        if pure_bike_result:
            geom, dist, dur, elev = pure_bike_result
            result = {"routes": [_format_pure_bike(geom, dist, dur, elev)]}
            return Response(json.dumps(result), media_type="application/json")
        return Response(json.dumps({"routes": [], "error": "No routes found"}), media_type="application/json")

    # Step 3: Score and select best
    for idx, c in enumerate(candidates):
        steps = c["legs"][0]["steps"]
        modes = [s["travel_mode"] for s in steps]
        bike_dist = sum(s["distance"] for s in steps if s["travel_mode"] == "BIKE")
        elev_gain = sum(s.get("elevation_score", 0) for s in steps if s["travel_mode"] == "BIKE")
        transfers = sum(1 for m in modes if m == "TRANSIT")
        print(f"  Candidate {idx}: score={_score_route(c):.0f}  dur={c['duration']}s  "
              f"bike={bike_dist:.0f}m  elev_gain={elev_gain}m  transfers={transfers}  modes={modes}")
    best = min(candidates, key=_score_route)
    print(f"  → Selected candidate with score={_score_route(best):.0f}")
    return Response(json.dumps({"routes": [best]}), media_type="application/json")


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
    const routeCache = {};

    const fromInput = document.getElementById('from-input');
    const toInput = document.getElementById('to-input');
    const getDirBtn = document.getElementById('get-dir');
    const useLocBtn = document.getElementById('use-loc');
    const swapBtn = document.getElementById('swap-btn');
    const routeInfo = document.getElementById('route-info');

    function cacheKey(s, e, mode) {
        return s.lat.toFixed(6) + ',' + s.lng.toFixed(6) + ',' + e.lat.toFixed(6) + ',' + e.lng.toFixed(6) + ',' + mode;
    }

    // Mode selector
    const modeBtns = document.querySelectorAll('.mode-btn');
    modeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            modeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentMode = btn.dataset.mode;
            if (startCoords && endCoords) {
                fetchRoute(false);
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

    // --- Swap from/to ---
    swapBtn.addEventListener('click', () => {
        const tmpVal = fromInput.value;
        fromInput.value = toInput.value;
        toInput.value = tmpVal;
        const tmpCoords = startCoords;
        startCoords = endCoords;
        endCoords = tmpCoords;
        if (startCoords && endCoords) fetchRoute(false);
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

    // --- Fetch & display route ---
    async function fetchRoute(forceRefresh) {
        if (!startCoords || !endCoords) {
            alert('Please select both a starting point and destination from the suggestions.');
            return;
        }

        const key = cacheKey(startCoords, endCoords, currentMode);

        // Use cache if available and not forcing refresh
        if (!forceRefresh && routeCache[key]) {
            displayRoute(routeCache[key]);
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

            routeCache[key] = data;
            displayRoute(data);

        } catch (err) {
            alert('Error getting route: ' + err.message);
        } finally {
            getDirBtn.textContent = 'Get Directions';
            getDirBtn.disabled = false;
        }
    }

    function displayRoute(data) {
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
            const isTransitMode = currentMode === 'transit' || currentMode === 'bike_transit';
            if (isTransitMode) {
                // Per-step segments with different styles
                steps.forEach((step, i) => {
                    if (!step.polyline) return;
                    const srcId = 'route-seg-' + i;
                    const layerId = 'route-seg-layer-' + i;
                    map.addSource(srcId, { type: 'geojson', data: step.polyline });
                    const isTransit = step.travel_mode === 'TRANSIT';
                    const isBike = step.travel_mode === 'BIKE';
                    let paint;
                    if (isTransit) {
                        const color = (step.transit && step.transit.color !== '#ffffff') ? step.transit.color : '#4285f4';
                        paint = { 'line-color': color, 'line-width': 5, 'line-opacity': 0.9 };
                    } else if (isBike) {
                        paint = { 'line-color': '#0d904f', 'line-width': 4, 'line-opacity': 0.8 };
                    } else {
                        paint = { 'line-color': '#9aa0a6', 'line-width': 4, 'line-opacity': 0.7, 'line-dasharray': [2, 2] };
                    }
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
            endMarker = new maplibregl.Marker({ color: '#ea4335' })
                .setLngLat([endCoords.lng, endCoords.lat])
                .setPopup(new maplibregl.Popup({ offset: 25 }).setText(endLabel))
                .addTo(map);

            // Fit bounds to route
            const coords = geojson.coordinates;
            const bounds = coords.reduce((b, c) => b.extend(c), new maplibregl.LngLatBounds(coords[0], coords[0]));
            map.fitBounds(bounds, { padding: 60 });

            // Show distance and time
            const distMiles = (route.distance / 1609.34).toFixed(1);
            const mins = Math.round(route.duration / 60);
            routeInfo.style.display = 'block';
            const modeLabels = { foot: 'walking', bike: 'biking', transit: 'by transit', bike_transit: 'bike + transit' };
            routeInfo.innerHTML = '<strong>' + distMiles + ' mi</strong> &middot; <strong>' + mins + ' min</strong> ' + (modeLabels[currentMode] || 'walking');

            // --- Render steps ---
            if (isTransitMode) {
                // Timeline view
                let html = '<ul class="timeline">';
                steps.forEach((step, i) => {
                    const isTransitStep = step.travel_mode === 'TRANSIT';
                    const isBikeStep = step.travel_mode === 'BIKE';
                    const t = step.transit;

                    // Time label
                    let timeStr = '';
                    if (isTransitStep && t && t.departure_time) {
                        const d = new Date(t.departure_time);
                        timeStr = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
                    }

                    // Dot & line style
                    let dotCls = 'tl-dot';
                    let lineCls = 'tl-line walk';
                    if (isTransitStep) { dotCls = 'tl-dot transit'; lineCls = 'tl-line transit-line'; }
                    else if (isBikeStep) { dotCls = 'tl-dot bike'; lineCls = 'tl-line bike-line'; }

                    // Content
                    let content = '';
                    if (isTransitStep && t) {
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
                        const moveMins = Math.round(step.duration / 60);
                        const moveLabel = isBikeStep ? 'Bike' : 'Walk';
                        content = '<span class="tl-label">' + moveLabel + ' ' + stepDist + '</span>'
                            + '<div class="tl-sub">' + step.maneuver.instruction + ' &middot; ' + moveMins + ' min</div>';
                    }

                    // Check what comes after this step
                    const next = steps[i + 1];
                    const isLast = !next && !(isTransitStep && t && t.arrival_time);

                    html += '<div class="tl-step">'
                        + '<div class="tl-time">' + timeStr + '</div>'
                        + '<div class="tl-track"><div class="' + dotCls + '"></div>'
                        + (isLast ? '' : '<div class="' + lineCls + '"></div>')
                        + '</div>'
                        + '<div class="tl-content">' + content + '</div>'
                        + '</div>';

                    // Arrival time for transit step
                    if (isTransitStep && t && t.arrival_time) {
                        const arrD = new Date(t.arrival_time);
                        const arrStr = arrD.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
                        if (!next || next.travel_mode !== 'TRANSIT') {
                            const hasMore = !!next;
                            const nextLineCls = (hasMore && next.travel_mode === 'BIKE') ? 'tl-line bike-line' : 'tl-line walk';
                            html += '<div class="tl-step">'
                                + '<div class="tl-time">' + arrStr + '</div>'
                                + '<div class="tl-track"><div class="tl-dot transit"></div>'
                                + (hasMore ? '<div class="' + nextLineCls + '"></div>' : '') + '</div>'
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
    }

    getDirBtn.addEventListener('click', () => fetchRoute(true));
});
"""


serve(port=5002)

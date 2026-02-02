## Tech Stack

- **Backend**: Python 3.12 with FastHTML (`python-fasthtml`)
- **Package Manager**: uv (uses `pyproject.toml` and `uv.lock`)
- **Map**: MapLibre GL JS with CARTO light grey basemap tiles
- **Routing**: OSRM public API (`router.project-osrm.org`) for walking directions
- **Geocoding**: Google Places Autocomplete (API key in `.env`)

## Commands

```bash
# Run the development server (serves on port 5002)
python app.py

# Or with uv
uv run python app.py

# Install dependencies
uv sync
```

## Architecture

- `app.py` — Single-file FastHTML app serving the full UI inline
  - `GET /` — Main page with full-screen MapLibre map and floating directions panel
  - `GET /route?start_lat=...&start_lng=...&end_lat=...&end_lng=...` — Proxies to OSRM walking profile, returns GeoJSON route
- `.env` — Contains `GOOGLE_PLACES_API_KEY` (and other keys)
- Geocoding is handled client-side via Google Places Autocomplete (no backend proxy needed)
- Map tiles served from CARTO CDN (`basemaps.cartocdn.com/light_all`)

## Environment Variables

Required in `.env`:
- `GOOGLE_PLACES_API_KEY` — Google Maps API key with Places API enabled

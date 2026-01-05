# WellX Webapp

WellX Webapp is a FastAPI backend that serves an API and a set of static
frontend modules (OneMap, Time-Series, Archie, and more).

## Repo layout

- `backend/app/main.py`: FastAPI app, mounts static frontends and API routes.
- `frontend/launcher`: entry page (`/`) that links modules.
- `frontend/onemap`, `frontend/timeseries`, `frontend/archie`, `frontend/fluidlab`,
  `frontend/impulse`, `frontend/deliverables`: static HTML/JS apps.
- `frontend/config.js`: shared API base resolver used by the frontends.

## Requirements

- Python 3.x and pip.
- Data directory containing:
  - `wells.geojson` (GeoJSON FeatureCollection; features should include
    `properties.well_name` and `geometry.coordinates`).
  - `rates.csv` with a `date` column plus any numeric/categorical fields.

## Configure environment

The API requires `DATA_DIR` pointing to the data folder.

Option A: set it in your shell:

```bash
# PowerShell
$env:DATA_DIR="C:\path\to\data"

# macOS/Linux
export DATA_DIR="/path/to/data"
```

Option B: use `backend/.env` (only loaded when `LOAD_DOTENV` is set):

```bash
# PowerShell
$env:LOAD_DOTENV="1"

# macOS/Linux
export LOAD_DOTENV=1
```

`backend/.env` example:

```ini
DATA_DIR=/path/to/data
```

Note: `LOAD_DOTENV` must be set before starting the API; otherwise the `.env`
file is ignored.

## Run the API (and bundled frontend)

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt

# set DATA_DIR (see above)
uvicorn backend.app.main:app --reload --port 8000
```

Open:

- `http://localhost:8000/` (launcher)
- `http://localhost:8000/onemap/`
- `http://localhost:8000/timeseries/`
- `http://localhost:8000/archie/`
- `http://localhost:8000/docs` (API docs)

## Run the frontend separately (optional)

```bash
cd frontend
python -m http.server 5173
```

Then point the UI at the API by setting a base URL:

- Edit `<meta name="api-base-url" content="http://localhost:8000">` in
  `frontend/onemap/index.html` and `frontend/timeseries/index.html`, or
- Define `window.API_BASE_URL` before loading `frontend/config.js`.

`frontend/config.js` normalizes the base URL and builds `/api` requests.

## prodpy integration

The core webapp does not require `prodpy`. It is used by Streamlit prototypes in:

- `frontend/timeseries/_dcadash.py`
- `frontend/timeseries/_dcadash_dataselect.py`
- `frontend/onemap/_welldash.py`

If you want to run these, install `prodpy` (plus `streamlit` and `plotly`) and
start them with `streamlit run <file>`.

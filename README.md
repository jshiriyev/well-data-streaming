# WellX Webapp

WellX Webapp is a FastAPI backend that serves an API and a set of static
frontend modules (OneMap, Time-Series, Archie, and more).

## Repo layout

- `backend/app/main.py`: FastAPI app, mounts static frontends and API routes.
- `frontend/src/pages/launcher`: entry page (`/`) that links modules.
- `frontend/src/pages/onemap`, `frontend/src/pages/timeseries`, `frontend/src/pages/archie`,
  `frontend/src/pages/fluidlab`, `frontend/src/pages/impulse`,
  `frontend/src/pages/deliverables`, `frontend/src/pages/datahub`: page-specific HTML/JS apps.
- `frontend/src/shared`: shared base (styles + API config).

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
pip install -e backend

# build the frontend (required for the bundled UI)
cd frontend
npm install
npm run build
cd ..

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
npm install
npm run dev
```

For a production build:

```bash
cd frontend
npm run build
```

Then point the UI at the API by setting a base URL:

- Edit `<meta name="api-base-url" content="http://localhost:8000">` in the page
  HTML (e.g. `frontend/src/pages/onemap/index.html`), or
- Define `window.API_BASE_URL` in an inline script before the page's module entry.
- Set `window.API_BASE_URL` in `frontend/public/api-config.js` (served as `/api-config.js`).

The shared API resolver lives in `frontend/src/shared/config.js` and is bundled into
the shared Vite chunk.

## prodpy integration

The core webapp does not require `prodpy`. It is used by Streamlit prototypes in:

- `frontend/src/pages/timeseries/_dcadash.py`
- `frontend/src/pages/timeseries/_dcadash_dataselect.py`
- `frontend/src/pages/onemap/_welldash.py`

If you want to run these, install `prodpy` (plus `streamlit` and `plotly`) and
start them with `streamlit run <file>`.

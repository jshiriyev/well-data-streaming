from contextlib import asynccontextmanager
from dotenv import load_dotenv

import json
import os

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import pandas as pd

from .api import wells, rates, logs

DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"

def _should_load_dotenv() -> bool:
    value = os.getenv("LOAD_DOTENV", "").strip().lower()
    if value in {"0", "false", "no", "off"}:
        return False
    if value in {"1", "true", "yes", "on"}:
        return True
    return not os.getenv("DATA_DIR")

if DOTENV_PATH.exists() and _should_load_dotenv():
    load_dotenv(DOTENV_PATH)

WELLS_FILENAME = "wells.geojson"
RATES_FILENAME = "rates.csv"
LAS_FOLDERNAME = "las"

def _validate_data_dir():
    data_dir_raw = os.getenv("DATA_DIR", "").strip()
    if not data_dir_raw:
        return None, (
            "DATA_DIR is required. Set DATA_DIR to the folder containing wells.geojson "
            "and rates.csv."
        )

    data_dir = Path(data_dir_raw)
    if not data_dir.exists():
        return None, f"DATA_DIR does not exist: {data_dir}"
    if not data_dir.is_dir():
        return None, f"DATA_DIR is not a directory: {data_dir}"

    return data_dir, None

def load_wells(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_rates(path: Path) -> pd.DataFrame:
    return pd.read_csv(
        path,
        parse_dates=["date"],
        dayfirst=True,
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.config_error = None
    app.state.data_dir = None
    app.state.wells = None
    app.state.rates = None
    app.state.wells_path = None
    app.state.rates_path = None
    app.state.rates_mtime = None

    data_dir, error = _validate_data_dir()
    if error or data_dir is None:
        app.state.config_error = error or "DATA_DIR validation failed"
        yield
        return

    wells_path = data_dir / WELLS_FILENAME
    rates_path = data_dir / RATES_FILENAME
    logs_path  = data_dir / LAS_FOLDERNAME

    app.state.data_dir = data_dir
    app.state.wells_path = wells_path
    app.state.rates_path = rates_path
    app.state.logs_path = logs_path

    try:
        app.state.wells = load_wells(wells_path)
        app.state.rates = load_rates(rates_path)
        app.state.rates_mtime = rates_path.stat().st_mtime
    except Exception as exc:
        app.state.config_error = f"Failed to load data files: {exc}"
        app.state.wells = None
        app.state.rates = None

    yield

app = FastAPI(title="Field Data API", version="0.1.0", lifespan=lifespan)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"
PAGES_DIR = DIST_DIR / "pages"
API_CONFIG_PATH = DIST_DIR / "api-config.js"

FRONTEND_ENABLED = PAGES_DIR.exists()

if FRONTEND_ENABLED:
    def resolve_page_dir(name: str) -> Path:
        return PAGES_DIR / name

    LAUNCHER_DIR = resolve_page_dir("launcher")
    ONEMAP_DIR = resolve_page_dir("onemap")
    WORKSPACE_DIR = resolve_page_dir("workbench")
    TIMESERIES_DIR = resolve_page_dir("timeseries")
    ARCHIE_DIR = resolve_page_dir("archie")
    FLUIDLAB_DIR = resolve_page_dir("fluidlab")
    DELIVERABLES_DIR = resolve_page_dir("deliverables")
    IMPULSE_DIR = resolve_page_dir("impulse")
    DATAHUB_DIR = resolve_page_dir("datahub")

    STATIC_DIRS = {
        "launcher": LAUNCHER_DIR,
        "datahub": DATAHUB_DIR,
        "onemap": ONEMAP_DIR,
        "workbench": WORKSPACE_DIR,
        "timeseries": TIMESERIES_DIR,
        "archie": ARCHIE_DIR,
        "fluidlab": FLUIDLAB_DIR,
        "deliverables": DELIVERABLES_DIR,
        "impulse": IMPULSE_DIR,
    }

    for path in STATIC_DIRS.values():
        if not path.exists():
            raise RuntimeError(f"Static directory not found: {path}")

    LAUNCHER_INDEX = LAUNCHER_DIR / "index.html"
    if not LAUNCHER_INDEX.exists():
        raise RuntimeError(f"Launcher index missing: {LAUNCHER_INDEX}")

ALLOWED_ORIGINS = ["*"]  # adjust per deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

if FRONTEND_ENABLED:
    assets_dir = DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    if API_CONFIG_PATH.exists():
        @app.get("/api-config.js")
        def api_config():
            return FileResponse(API_CONFIG_PATH)

    app.mount("/datahub", StaticFiles(directory=DATAHUB_DIR, html=True), name="datahub")
    app.mount("/onemap", StaticFiles(directory=ONEMAP_DIR, html=True), name="onemap")
    app.mount("/workspace", StaticFiles(directory=WORKSPACE_DIR, html=True), name="workspace")
    app.mount("/timeseries", StaticFiles(directory=TIMESERIES_DIR, html=True), name="timeseries")
    app.mount("/archie", StaticFiles(directory=ARCHIE_DIR, html=True), name="archie")
    app.mount("/fluidlab", StaticFiles(directory=FLUIDLAB_DIR, html=True), name="fluidlab")
    app.mount("/deliverables", StaticFiles(directory=DELIVERABLES_DIR, html=True), name="deliverables")
    app.mount("/impulse", StaticFiles(directory=IMPULSE_DIR, html=True), name="impulse")
    
app.include_router(wells.router, prefix="/api", tags=["wells"])
app.include_router(rates.router, prefix="/api", tags=["rates"])
app.include_router(logs.router, prefix="/api", tags=["logs"])

@app.get("/health")
def healthcheck(request: Request):
    """Minimal health endpoint for readiness probes."""
    error = getattr(request.app.state, "config_error", None)
    if error:
        return JSONResponse(status_code=503, content={"status": "error", "detail": error})
    return {"status": "ok"}

if FRONTEND_ENABLED:
    app.mount("/", StaticFiles(directory=LAUNCHER_DIR, html=True), name="launcher-root")
else:
    FRONTEND_WARNING = (
        "Frontend build not found. Run npm install && npm run build in frontend."
    )

    @app.get("/")
    def frontend_missing():
        return {"status": "frontend_missing", "detail": FRONTEND_WARNING}

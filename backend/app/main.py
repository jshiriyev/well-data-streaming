from contextlib import asynccontextmanager
from dotenv import load_dotenv

import json
import os

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import pandas as pd

from .api import wells, rates

DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"

def _should_load_dotenv() -> bool:
    value = os.getenv("LOAD_DOTENV", "").strip().lower()
    return value in {"1", "true", "yes", "on"}

if _should_load_dotenv() and DOTENV_PATH.exists():
    load_dotenv(DOTENV_PATH)

DATA_DIR_RAW = os.getenv("DATA_DIR")
if not DATA_DIR_RAW:
    raise RuntimeError(
        "DATA_DIR is required. Set DATA_DIR to the folder containing wells.geojson and rates.csv."
    )

DATA_DIR = Path(DATA_DIR_RAW)
if not DATA_DIR.exists():
    raise RuntimeError(f"DATA_DIR does not exist: {DATA_DIR}")
if not DATA_DIR.is_dir():
    raise RuntimeError(f"DATA_DIR is not a directory: {DATA_DIR}")

WELLS_FILENAME = "wells.geojson"
RATES_FILENAME = "rates.csv"

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
    wells_path = DATA_DIR / WELLS_FILENAME
    rates_path = DATA_DIR / RATES_FILENAME

    app.state.wells_path = wells_path
    app.state.rates_path = rates_path

    app.state.wells = load_wells(wells_path)
    app.state.rates = load_rates(rates_path)
    app.state.rates_mtime = rates_path.stat().st_mtime

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
    TIMESERIES_DIR = resolve_page_dir("timeseries")
    ARCHIE_DIR = resolve_page_dir("archie")
    FLUIDLAB_DIR = resolve_page_dir("fluidlab")
    DELIVERABLES_DIR = resolve_page_dir("deliverables")
    IMPULSE_DIR = resolve_page_dir("impulse")
    DATAHUB_DIR = resolve_page_dir("datahub")

    STATIC_DIRS = {
        "launcher": LAUNCHER_DIR,
        "onemap": ONEMAP_DIR,
        "timeseries": TIMESERIES_DIR,
        "archie": ARCHIE_DIR,
        "fluidlab": FLUIDLAB_DIR,
        "deliverables": DELIVERABLES_DIR,
        "impulse": IMPULSE_DIR,
        "datahub": DATAHUB_DIR,
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

    app.mount("/onemap", StaticFiles(directory=ONEMAP_DIR, html=True), name="onemap")
    app.mount("/timeseries", StaticFiles(directory=TIMESERIES_DIR, html=True), name="timeseries")
    app.mount("/archie", StaticFiles(directory=ARCHIE_DIR, html=True), name="archie")
    app.mount("/fluidlab", StaticFiles(directory=FLUIDLAB_DIR, html=True), name="fluidlab")
    app.mount("/deliverables", StaticFiles(directory=DELIVERABLES_DIR, html=True), name="deliverables")
    app.mount("/impulse", StaticFiles(directory=IMPULSE_DIR, html=True), name="impulse")
    app.mount("/datahub", StaticFiles(directory=DATAHUB_DIR, html=True), name="datahub")

app.include_router(wells.router, prefix="/api", tags=["wells"])
app.include_router(rates.router, prefix="/api", tags=["rates"])

@app.get("/health")
def healthcheck():
    """Minimal health endpoint for readiness probes."""
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

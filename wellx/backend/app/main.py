from contextlib import asynccontextmanager
from dotenv import load_dotenv

import json
import os

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import pandas as pd

from .routers import wells, rates

load_dotenv()

DATA_DIR = Path(os.getenv('DATA_DIR','/data/path'))

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    with open(DATA_DIR / "wells.geojson", "r", encoding="utf-8") as f:
        app.state.wells = json.load(f)
    
    app.state.rates = pd.read_csv(
        DATA_DIR / "rates.csv",
        parse_dates=["date"],
        dayfirst=True,
    )

    yield

app = FastAPI(title="Field Data API", version="0.1.0", lifespan=lifespan)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_DIR = PROJECT_ROOT / "launcher"
ONEMAP_DIR = PROJECT_ROOT / "onemap"
TIMESERIES_DIR = PROJECT_ROOT / "timeseries"
ARCHIE_DIR = PROJECT_ROOT / "archie"

print(ARCHIE_DIR)

for path in (LAUNCHER_DIR, ONEMAP_DIR, TIMESERIES_DIR):
    if not path.exists():
        raise RuntimeError(f"Static directory not found: {path}")

LAUNCHER_INDEX = LAUNCHER_DIR / "index.html"
LAUNCHER_CSS = LAUNCHER_DIR / "main.css"
for asset in (LAUNCHER_INDEX, LAUNCHER_CSS):
    if not asset.exists():
        raise RuntimeError(f"Launcher asset missing: {asset}")

ALLOWED_ORIGINS = ["*"]  # adjust per deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.mount("/onemap", StaticFiles(directory=ONEMAP_DIR, html=True), name="onemap")
app.mount("/timeseries", StaticFiles(directory=TIMESERIES_DIR, html=True), name="timeseries")
app.mount("/archie", StaticFiles(directory=ARCHIE_DIR, html=True), name="archie")

app.include_router(wells.router, prefix="/api", tags=["wells"])
app.include_router(rates.router, prefix="/api", tags=["rates"])

@app.get("/health")
def healthcheck():
    """Minimal health endpoint for readiness probes."""
    return {"status": "ok"}

app.mount("/", StaticFiles(directory=LAUNCHER_DIR, html=True), name="launcher-root")
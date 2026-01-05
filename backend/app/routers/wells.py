from datetime import datetime

from typing import Optional

from fastapi import APIRouter, Request
from fastapi import HTTPException, Query

from ..schemas.wells import WellOut

router = APIRouter()

def _parse_iso_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None

def _extract_coords(feature: dict) -> Optional[tuple[float, float]]:
    geometry = feature.get("geometry")
    if not isinstance(geometry, dict):
        return None
    coords = geometry.get("coordinates")
    if not isinstance(coords, (list, tuple)) or len(coords) < 2:
        return None
    try:
        lon = float(coords[0])
        lat = float(coords[1])
    except (TypeError, ValueError):
        return None
    return lon, lat

def get_wells(wells, horizon: str | None = None, date_str: str | None = None) -> list:
    """Return unique wells filtered by optional horizon and/or date."""

    selected_wells: dict[str, dict] = {}

    selected_date = datetime.fromisoformat(date_str) if date_str else None

    for feature in wells.get("features", []):
        if not isinstance(feature, dict):
            continue
        props = feature.get("properties") or {}

        # Filter by horizon only when provided
        if horizon is not None and props.get("horizon") != horizon:
            continue

        spud_raw = props.get("spud_date")
        spud_date = _parse_iso_date(spud_raw)
        if selected_date is not None and spud_date is not None:
            if spud_date > selected_date:
                continue

        well_name = props.get("well_name")
        if not well_name:
            continue

        coords = _extract_coords(feature)
        if coords is None:
            continue
        lon, lat = coords

        # Save the well only once
        if well_name not in selected_wells:
            selected_wells[well_name] = {
                "well": well_name,
                "horizon": props.get("horizon"),
                "spud_date": spud_raw if spud_date is not None else None,
                "lon": lon,
                "lat": lat,
            }

    return list(selected_wells.values())

@router.get("/wells", response_model=list[WellOut])
def list_wells(
    request: Request,
    horizon: Optional[str] = Query(None, description="Horizon name, e.g. 'FLD'"),
    date: Optional[str] = Query(None, description="ISO date, e.g. '2010-01-01'"),
):
    """
    Returns wells filtered by horizon and date.
    This is the endpoint your frontend controls will call.
    """
    try:
        wells = get_wells(
            request.app.state.wells,
            horizon=horizon,
            date_str=date,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return wells

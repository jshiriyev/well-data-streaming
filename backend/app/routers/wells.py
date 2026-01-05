from datetime import datetime

from typing import Optional

from fastapi import APIRouter, Request
from fastapi import HTTPException, Query

from ..schemas.wells import WellOut

router = APIRouter()

def get_wells(wells, horizon: str | None = None, date_str: str | None = None) -> list:
    """Return unique wells filtered by optional horizon and/or date."""

    selected_wells: dict[str, dict] = {}

    for feature in wells.get("features", []):
        props = feature.get("properties", {})

        # Filter by horizon only when provided
        if horizon is not None and props.get("horizon") != horizon:
            continue

        if date_str is not None:
            selected_date = datetime.fromisoformat(date_str)
            spud_raw = props.get("spud_date")
            if spud_raw:
                spud_date = datetime.fromisoformat(spud_raw)
                if spud_date > selected_date:
                    continue

        well_name = props.get("well_name")

        # Save the well only once
        if well_name not in selected_wells:
            selected_wells[well_name] = {
                "well": props.get("well_name"),
                "horizon": props.get("horizon"),
                "spud_date": props.get("spud_date"),
                "lon": feature["geometry"]["coordinates"][0],
                "lat": feature["geometry"]["coordinates"][1],
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
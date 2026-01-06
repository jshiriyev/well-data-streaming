from datetime import date, datetime
import math

from fastapi import APIRouter, Depends, Request
from fastapi import HTTPException

from ..schemas.wells import WellOut, WellsQuery

router = APIRouter()
MAX_ERROR_SAMPLES = 10

class WellDataError(Exception):
    def __init__(self, message: str, errors: list[dict], error_count: int) -> None:
        super().__init__(message)
        self.message = message
        self.errors = errors
        self.error_count = error_count

def _parse_iso_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None

def _extract_coords(feature: dict) -> tuple[tuple[float, float] | None, str | None]:
    geometry = feature.get("geometry")
    if not isinstance(geometry, dict):
        return None, "geometry must be an object"
    coords = geometry.get("coordinates")
    if not isinstance(coords, (list, tuple)) or len(coords) < 2:
        return None, "geometry.coordinates must be [lon, lat]"
    try:
        lon = float(coords[0])
        lat = float(coords[1])
    except (TypeError, ValueError):
        return None, "geometry.coordinates must be numeric"
    if not (math.isfinite(lon) and math.isfinite(lat)):
        return None, "geometry.coordinates must be finite numbers"
    return (lon, lat), None

def get_wells(
    wells,
    horizon: str | None = None,
    date_value: date | None = None,
) -> list:
    """Return unique wells filtered by optional horizon and/or date."""
    if not isinstance(wells, dict):
        raise WellDataError(
            "Invalid wells data: expected GeoJSON object.",
            errors=[{"code": "invalid_geojson", "detail": "Expected a GeoJSON object."}],
            error_count=1,
        )

    selected_wells: dict[str, dict] = {}
    errors: list[dict] = []
    error_count = 0

    selected_date = date_value

    features = wells.get("features")
    if not isinstance(features, list):
        raise WellDataError(
            "Invalid wells data: missing features list.",
            errors=[{"code": "invalid_geojson", "detail": "Expected 'features' to be a list."}],
            error_count=1,
        )

    for idx, feature in enumerate(features):
        if not isinstance(feature, dict):
            error_count += 1
            if len(errors) < MAX_ERROR_SAMPLES:
                errors.append({
                    "code": "invalid_feature",
                    "index": idx,
                    "detail": "Feature must be an object.",
                })
            continue
        props = feature.get("properties") or {}

        # Filter by horizon only when provided
        if horizon is not None and props.get("horizon") != horizon:
            continue

        spud_raw = props.get("spud_date")
        spud_date = _parse_iso_date(spud_raw)
        if selected_date is not None and spud_date is not None:
            if spud_date.date() > selected_date:
                continue

        well_name = props.get("well_name")
        if not well_name:
            continue

        coords, coord_error = _extract_coords(feature)
        if coord_error:
            error_count += 1
            if len(errors) < MAX_ERROR_SAMPLES:
                errors.append({
                    "code": "invalid_coordinates",
                    "index": idx,
                    "well": well_name,
                    "detail": coord_error,
                })
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

    if error_count:
        raise WellDataError(
            "Invalid wells data: one or more features have invalid coordinates.",
            errors=errors,
            error_count=error_count,
        )

    return list(selected_wells.values())

@router.get("/wells", response_model=list[WellOut])
def list_wells(
    request: Request,
    params: WellsQuery = Depends(),
):
    """
    Returns wells filtered by horizon and date.
    This is the endpoint your frontend controls will call.
    """
    try:
        wells = get_wells(
            request.app.state.wells,
            horizon=params.horizon,
            date_value=params.date,
        )
    except WellDataError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "message": e.message,
                "error_count": e.error_count,
                "errors": e.errors,
            },
        ) from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return wells

import json
import pickle
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Request, HTTPException
import pandas as pd

from ..schemas.logs import LogOut, LogQuery

router = APIRouter()

SAFE_WELL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")

class WellDataError(Exception):
    def __init__(self, message: str, errors: list[dict], error_count: int) -> None:
        super().__init__(message)
        self.message = message
        self.errors = errors
        self.error_count = error_count

def _normalize_well_name(well: str) -> str:
    if not isinstance(well, str):
        raise WellDataError(
            "Invalid well name: expected str.",
            errors=[{"code": "invalid_str", "detail": "Expected a str object."}],
            error_count=1,
        )
    name = well.strip()
    if not name:
        raise WellDataError(
            "Invalid well name: empty value.",
            errors=[{"code": "empty_well", "detail": "Well name cannot be empty."}],
            error_count=1,
        )
    if name.lower().endswith(".pkl"):
        name = name[:-4]
    if "/" in name or "\\" in name:
        raise WellDataError(
            "Invalid well name: path separators are not allowed.",
            errors=[{"code": "invalid_path", "detail": "Path separators are not allowed."}],
            error_count=1,
        )
    if not SAFE_WELL_RE.match(name):
        raise WellDataError(
            "Invalid well name format.",
            errors=[{"code": "invalid_format", "detail": "Use letters, numbers, '_' or '-'."}],
            error_count=1,
        )
    return name

def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, pd.DataFrame):
        return value.where(pd.notnull(value), None).to_dict(orient="list")
    if isinstance(value, pd.Series):
        return [v if pd.notnull(v) else None for v in value.tolist()]
    return value

def _serialize_log(log_obj: Any) -> dict[str, Any]:
    to_json = getattr(log_obj, "to_json", None)
    if callable(to_json):
        try:
            data = json.loads(to_json())
            if isinstance(data, dict):
                return data
            return {"data": data}
        except Exception:
            pass

    df_func = getattr(log_obj, "df", None)
    if callable(df_func):
        try:
            df = df_func()
            return {"data": _jsonable(df)}
        except Exception:
            pass

    if isinstance(log_obj, dict):
        return _jsonable(log_obj)

    return {"data": _jsonable(log_obj)}

def get_log(logs_dir: Path, well: str) -> dict[str, Any]:
    """Return the log content for a given well name."""
    name = _normalize_well_name(well)

    if not logs_dir.exists():
        raise FileNotFoundError(f"Logs directory does not exist: {logs_dir}")
    if not logs_dir.is_dir():
        raise FileNotFoundError(f"Logs path is not a directory: {logs_dir}")

    log_path = logs_dir / f"{name}.pkl"
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    try:
        with log_path.open("rb") as f:
            log_obj = pickle.load(f)
    except Exception as exc:
        raise ValueError(f"Failed to load log file: {log_path}") from exc

    payload = _serialize_log(log_obj)
    if not isinstance(payload, dict):
        payload = {"data": payload}

    payload.setdefault("metadata", None)
    payload.setdefault("data", None)
    payload["well"] = name
    return payload

@router.get("/logs", response_model=LogOut)
def list_logs(
    request: Request,
    params: LogQuery = Depends(),
):
    config_error = getattr(request.app.state, "config_error", None)
    if config_error:
        raise HTTPException(status_code=503, detail=config_error)

    logs_dir = getattr(request.app.state, "logs_path", None)
    if not logs_dir:
        raise HTTPException(status_code=500, detail="Logs path is not configured.")

    try:
        log = get_log(Path(logs_dir), params.well)
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
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return log 

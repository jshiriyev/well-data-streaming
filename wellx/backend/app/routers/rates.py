import json

import re
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Request
from fastapi import HTTPException, Query

import pandas as pd

router = APIRouter()

ALLOWED_AGG_FUNCTIONS = {
    "sum",
    "mean",
    "median",
    "min",
    "max",
    "count",
    "std",
    "var",
    "first",
    "last",
}

_AGG_RE = re.compile(r"^\s*(?P<col>[^:]+)\s*:\s*(?P<func>[^:]+)\s*$")

def _validate_agg_dict(agg_dict: dict):
    """
    Validate aggregation dictionary against allowed aggregation functions.
    """
    if not isinstance(agg_dict, dict):
        raise TypeError("agg_dict must be a dictionary")

    for col, funcs in agg_dict.items():
        if isinstance(funcs, str):
            funcs = [funcs]

        if not isinstance(funcs, (list, tuple, set)):
            raise TypeError(
                f"Aggregation for column '{col}' must be a string or list of strings"
            )

        invalid = set(funcs) - ALLOWED_AGG_FUNCTIONS
        if invalid:
            raise ValueError(
                f"Invalid aggregation(s) {invalid} for column '{col}'. "
                f"Allowed values: {sorted(ALLOWED_AGG_FUNCTIONS)}"
            )

def _parse_agg_params(agg: Optional[List[str]], df: pd.DataFrame) -> Dict[str, Any]:
    """
    Parse query param:
        agg=oil_rate:sum&agg=water_rate:sum&agg=choke:mean

    Returns:
        {"oil_rate": "sum", "water_rate": "sum", "choke": "mean"}

    Raises HTTPException(400) on invalid input.
    """
    if not agg:
        return {}

    agg_dict: Dict[str, Any] = {}

    for item in agg:
        if item is None:
            continue
        item = str(item).strip()
        if not item:
            continue

        m = _AGG_RE.match(item)
        if not m:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agg format '{item}'. Use 'column:func' (e.g. oil_rate:mean).",
            )

        col = m.group("col").strip()
        func = m.group("func").strip().lower()

        if col not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agg column '{col}'. Available columns: {list(df.columns)}",
            )

        if func not in ALLOWED_AGG_FUNCTIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agg function '{func}' for '{col}'. Allowed: {sorted(ALLOWED_AGG_FUNCTIONS)}",
            )

        # (Optional) guardrails: mean/std/var/median require numeric columns in most cases
        if func in {"sum", "mean", "median", "min", "max", "std", "var"}:
            if not pd.api.types.is_numeric_dtype(df[col]):
                raise HTTPException(
                    status_code=400,
                    detail=f"Aggregation '{func}' requires numeric column, but '{col}' is {df[col].dtype}.",
                )

        # If user repeats the same column, last one wins
        agg_dict[col] = func

    return agg_dict

def get_rates(df, *, date_col: str = "date", filter_dict: Dict[str, List[str]] | None = None, agg_dict=None) -> str:
    # Read the CSV file
    rates = df.copy()

    rates[date_col] = pd.to_datetime(rates[date_col], errors="coerce")
    rates = rates.dropna(subset=[date_col])

    if filter_dict is not None:
        for col, values in filter_dict.items():
            if col in rates.columns and values:
                rates = rates[rates[col].isin(values)]

    if agg_dict is not None:
        _validate_agg_dict(agg_dict)

    grouped_df = rates.groupby([date_col], dropna=False)

    grouped = (
        grouped_df.sum(numeric_only=True)
        if agg_dict is None
        else grouped_df.agg(agg_dict)
    )

    rates = grouped.reset_index()

    rates[date_col] = rates[date_col].astype(str).str.slice(0, 10)

    return rates.to_json(orient='columns')

@router.get("/rates")
def list_rates(
    request: Request,
    agg: Optional[List[str]] = Query(
        None, 
        description="Aggregations per column, e.g. agg=oil_rate:mean"
    ),
):
    df = request.app.state.rates

    reserved_keys = {"date", "agg"}

    filter_dict: Dict[str, List[str]] = {}
    for key, value in request.query_params.multi_items():
        if key in reserved_keys:
            continue
        filter_dict.setdefault(key, []).append(value)

    try:
        agg_dict = _parse_agg_params(agg, df) if agg else None

        rates_json = get_rates(
            df,
            date_col = "date",
            filter_dict = filter_dict or None,
            agg_dict = agg_dict,
        )
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Invalid column: {e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return json.loads(rates_json)

@router.get("/rates/meta")
def rates_meta(request: Request):
    df = request.app.state.rates

    # Identify date-like column (prefer explicit 'date')
    date_column = "date" if "date" in df.columns else None
    if date_column is None:
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                date_column = col
                break

    numeric_fields = [
        col for col in df.columns
        if pd.api.types.is_numeric_dtype(df[col]) and col != date_column
    ]

    categorical_fields = [
        col for col in df.columns
        if not pd.api.types.is_numeric_dtype(df[col])
        and not pd.api.types.is_datetime64_any_dtype(df[col])
        and col != date_column
    ]

    categories = {}
    category_counts = {}
    for col in categorical_fields:
        uniques = df[col].dropna().unique().tolist()
        categories[col] = sorted({str(v) for v in uniques if str(v)})
        category_counts[col] = len(categories[col])

    return {
        "date_column": date_column,
        "numeric_fields": numeric_fields,
        "categorical_fields": categorical_fields,
        "categories": categories,
        "category_counts": category_counts,
    }

if __name__ == "__main__":

    import numpy as np

    df = pd.DataFrame({
        "date": ["2025-01-01", "2025-01-01", "2025-01-02", "bad-date", None, "2025-01-02", "2025-01-03"],
        "well": ["GUN_001", "GUN_002", "GUN_004", "GUN_007", "GUN_005", "GUN_005", "GUN_002"],
        "operation": ["prod", "inject", "prod", "prod", "inject", "inject", "prod"],
        "oil_rate": np.random.randint(100, 500, size=7),
        "water_rate": np.random.randint(50, 300, size=7)
    })

    print(df)

    df_new = get_rates(df, date_col = "date", agg_dict = {"oil_rate": ["sum", "mean"]})

    out = pd.DataFrame(json.loads(df_new))

    print(out)
import datetime as dt
from typing import Any, List, Dict, Optional
from pydantic import BaseModel, Field

class NumericFilterBounds(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None

class FilterRequest(BaseModel):
    horizon: str
    time: str  # ISO string
    categorical_filters: Optional[Dict[str, List[str]]] = None
    numeric_filters: Optional[Dict[str, NumericFilterBounds]] = None

class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]

class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]

class WellOut(BaseModel):
    well: str | None = None
    horizon: str | None = None
    spud_date: str | None = None  # ISO date as string
    lon: float
    lat: float

class WellsQuery(BaseModel):
    horizon: Optional[str] = Field(
        None,
        description="Horizon name, e.g. 'FLD'.",
    )
    date: Optional[dt.date] = Field(
        None,
        description="ISO date, e.g. '2010-01-01'.",
    )

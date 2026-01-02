from typing import Any, List, Dict, Optional
from pydantic import BaseModel

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
    horizon: str
    spud_date: str  # ISO date as string
    lon: float
    lat: float
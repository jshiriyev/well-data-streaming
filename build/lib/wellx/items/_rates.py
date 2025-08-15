from dataclasses import dataclass, field, fields
from typing import Optional, Literal, Dict, Any
import datetime

import pandas as pd

@dataclass(slots=True, frozen=False)
class Rates:
    """
    Time-stamped production or injection rates for a single well or perforation.

    Geologic/engineering context
    ----------------------------
    - Each record captures the daily average rates for oil, water, and gas at a specific date.
    - `optype` defines whether this is a **production** (outflow) or **injection** (inflow) record.
    - All rates are **surface-standard** unless otherwise documented in metadata.
    - Negative rates are not allowed (use zero for shut-in periods).

    Parameters
    ----------
    date : datetime.date
        Calendar date of the measurement (required).
    days : Optional[int]
        Number of days contributing to the rate calculation (default 1).
    horizon : Optional[str]
        Horizon or completion name (optional).
    optype : Literal["production", "injection"]
        Operation type; default is "production".
    orate : Optional[float]
        Oil rate in standard barrels/day (STB/day).
    wrate : Optional[float]
        Water rate in STB/day.
    grate : Optional[float]
        Gas rate in standard cubic feet/day (SCF/day).

    Notes
    -----
    - Missing rates are treated as `None` (no measurement).
    - Use `total_liquid()` and `to_dict()` for convenience.
    - Can be extended later to include unit metadata and uncertainty.

    """

    date: pd.Series

    days: Optional[pd.Series] = None

    horizon: Optional[pd.Series] = None

    optype: Literal["production", "injection"] = "production"

    choke: Optional[pd.Series] = None
    orate: Optional[pd.Series] = None
    wrate: Optional[pd.Series] = None
    grate: Optional[pd.Series] = None

    _metadata: Dict[str, Any] = field(default_factory=dict, repr=False)

    # def __post_init__(self):
    #     # Coerce to Series where needed
    #     def as_series(x: Optional[pd.Series], name: str) -> Optional[pd.Series]:
    #         if x is None:
    #             return None
    #         if not isinstance(x, pd.Series):
    #             raise TypeError(f"{name} must be a pandas Series.")
    #         if x.ndim != 1:
    #             raise ValueError(f"{name} must be 1-D.")
    #         return x

    #     self.date = as_series(self.date, "date")
    #     self.horizon = as_series(self.horizon, "horizon")
    #     self.choke = as_series(self.choke, "choke")
    #     self.orate = as_series(self.orate, "orate")
    #     self.wrate = as_series(self.wrate, "wrate")
    #     self.grate = as_series(self.grate, "grate")

    #     # length alignment: all non-None series must match date length
    #     n = len(self.date)
    #     for name in ("horizon", "choke", "orate", "wrate", "grate"):
    #         s = getattr(self, name)
    #         if s is not None and len(s) != n:
    #             raise ValueError(f"Length mismatch: {name} has length {len(s)} but date has length {n}.")

    #     # validate date as integer-like (allow NaN)
    #     if not pd.api.types.is_integer_dtype(self.date.dropna()):
    #         # try a safe cast check: values must be whole numbers if float dtype
    #         if pd.api.types.is_float_dtype(self.date):
    #             frac = (self.date.dropna() % 1 != 0)
    #             if frac.any():
    #                 raise TypeError("date must be integers in YYYYMMDD (found non-integers).")
    #         else:
    #             raise TypeError("date must be dtype integer or integer-like floats (YYYYMMDD).")

    #     # validate horizon is string dtype if present
    #     if self.horizon is not None and not pd.api.types.is_string_dtype(self.horizon.dropna()):
    #         # allow object with strings
    #         if not (pd.api.types.is_object_dtype(self.horizon) and self.horizon.dropna().map(lambda v: isinstance(v, str)).all()):
    #             raise TypeError("horizon must be a string Series (or object with strings).")

    #     # validate numeric columns are float-like and non-negative
    #     for name in ("choke", "orate", "wrate", "grate"):
    #         s = getattr(self, name)
    #         if s is None:
    #             continue
    #         if not (pd.api.types.is_float_dtype(s) or pd.api.types.is_integer_dtype(s)):
    #             raise TypeError(f"{name} must be numeric (float or int) Series.")
    #         if (s.dropna() < 0).any():
    #             raise ValueError(f"{name} must be >= 0 where present.")

    #     # scalars
    #     if self.optype not in ("production", "injection"):
    #         raise ValueError("optype must be 'production' or 'injection'.")
    #     if self.days is not None and self.days <= 0:
    #         raise ValueError("days must be positive if provided.")

    #     # normalize date to Int64 (nullable integer) for consistent I/O
    #     self.date = self.date.astype("Int64")

    #     # optional: normalize numerics to float64
    #     for name in ("choke", "orate", "wrate", "grate"):
    #         s = getattr(self, name)
    #         if s is not None and s.dtype.kind != "f":
    #             setattr(self, name, s.astype(float))

    @staticmethod
    def fields() -> list:
        """Field names for I/O schemas."""
        return [field.name for field in fields(Rates) if field.name != "_metadata"]

    def total_liquid(self) -> Optional[float]:
        """Return oil + water rate, or None if both missing."""
        if self.orate is None and self.wrate is None:
            return None
        return (self.orate or 0) + (self.wrate or 0)

    def to_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation for DataFrame ingestion or JSON."""
        return {
            "date": self.date.isoformat(),
            "days": self.days,
            "horizon": self.horizon,
            "optype": self.optype,
            "orate": self.orate,
            "wrate": self.wrate,
            "grate": self.grate,
            **self._metadata
        }

    def set_metadata(self, **kwargs) -> None:
        """
        Attach arbitrary metadata (e.g., measurement method, source).
        Keys overwrite existing metadata.
        """
        self._metadata.update(kwargs)

    def get_metadata(self, key: str, default=None):
        """Retrieve a metadata value by key."""
        return self._metadata.get(key, default)
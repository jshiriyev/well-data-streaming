from dataclasses import dataclass, field, fields

import datetime

from typing import Optional, Literal, Dict, Any

import pandas as pd

from wellx.pipes import Table

@dataclass(slots=True, frozen=False)
class Rate:
    """
    Time-stamped surface rates for a single well.

    Domain assumptions
    ------------------
    - Rates are *surface-standard* and non-negative.
    - `otype` indicates flow direction: "production" (outflow) or "injection" (inflow).
    - `days` is the number of contributing days in the period (≥ 0). Use 0 to mark shut-in.

    Parameters
    ----------
    well : str
        Well identifier (non-empty).
    date : datetime.date
        Calendar date of record (required).
    days : int, optional
        Contributing days in the period. Defaults to 0.
    horizon : str, optional
        Horizon/completion name.
    otype : {"production", "injection"}, default "production"
        Operational type of the record.
    choke : float, optional
        Choke size (units as per project convention).
    orate : float, default 0.0
        Oil rate (e.g., STB/day).
    wrate : float, default 0.0
        Water rate (e.g., STB/day).
    grate : float, default 0.0
        Gas rate (e.g., MSCF/day).

    Notes
    -----
    - Negative rates are rejected.
    - Each numeric field (oil, water, gas rate) carries *unit information* inside
    its `metadata` dictionary. These metadata entries are immutable at the class
    level but can be read at runtime via `dataclasses.fields`. To allow flexible
    editing, a per-instance `_unit_override` dictionary is provided. This lets
    you override the default unit label for a given field without altering the
    class definition.

    Usage
    -----
    >>> from dataclasses import fields
    >>> r = Rate(well="A-12", date=date(2025, 8, 17), orate=120.0)
    >>> # Access static metadata (class schema)
    >>> [ (f.name, f.metadata.get("unit")) for f in fields(Rate) ]
    [('well', None), ('date', None), ('otype', None),
     ('orate', 'STB/d'), ('wrate', 'STB/d'), ('grate', 'MSCF/d')]

    >>> # Access through helper (checks overrides first)
    >>> r.get_unit("orate")
    'STB/d'

    >>> # Override unit at runtime
    >>> r.set_unit("orate", "m3/d")
    >>> r.get_unit("orate")
    'm3/d'

    Notes
    -----
    - Class-level `metadata` is a read-only `mappingproxy` and cannot be
      mutated in place.
    - Use `set_unit` to attach runtime overrides; these are stored in
      `_unit_override` and shadow the defaults.
    - This design separates *schema information* (immutable) from
      *instance-specific labeling* (mutable).
    - For strict unit handling and conversions, consider `pint.Quantity`
      or `typing.Annotated` instead.

    """
    well: str

    date: datetime.date

    days: Optional[int] = 0

    horizon: Optional[str] = None

    otype: Literal["production", "injection"] = "production"

    choke: Optional[float] = None

    orate: float = field(default=0., metadata={"unit": "STB/d"})
    wrate: float = field(default=0., metadata={"unit": "STB/d"})
    grate: float = field(default=0., metadata={"unit": "MSCF/d"})

    _unit_override: Dict[str, str] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        # --- basic requireds
        if not isinstance(self.date, datetime.date):
            raise TypeError("date must be a datetime.date")

        if not isinstance(self.well, str) or not self.well.strip():
            raise ValueError("well must be a non-empty string")

        # --- categorical
        if self.otype not in ("production", "injection"):
            raise ValueError("otype must be 'production' or 'injection'")

        # --- numeric invariants
        if self.days is not None and self.days < 0:
            raise ValueError("days must be >= 0")

        for name in ("orate", "wrate", "grate"):
            val = getattr(self, name)
            if val is None:
                # normalize Nones to 0.0 for convenience
                setattr(self, name, 0.)
            elif val < 0.:
                raise ValueError(f"{name} must be >= 0")

        if self.choke is not None and self.choke < 0:
            raise ValueError("choke must be >= 0")

    def get_unit(self, key: str) -> Optional[str]:
        """Return the unit for a field, checking overrides first."""
        if key in self._unit_override:
            return self._unit_override[key]
        for f in fields(self):                 # dataclasses.fields -> tuple[Field, ...]
            if f.name == key:
                return f.metadata.get("unit")  # metadata is a Mapping
        raise AttributeError(f"No field named {key!r}")

    def set_unit(self, **kwargs) -> None:
        """Override the unit for a field at runtime (does not change class metadata)."""
        for key, unit in kwargs.items():
            if key not in {f.name for f in fields(self)}:
                raise AttributeError(f"No field named {key!r}")
            self._unit_override[key] = unit

    @property
    def lrate(self) -> float:
        """Oil + water rate."""
        return self.orate + self.wrate

    @property
    def shutin(self) -> bool:
        """True if no production/injection is recorded (all rates zero or days==0)."""
        zero_rates = (self.orate == 0.0 and self.wrate == 0.0 and self.grate == 0.0)
        return zero_rates or (self.days == 0)

    @staticmethod
    def fields() -> list[str]:
        """List of dataclass field names (stable order)."""
        return [f.name for f in fields(Rate) if (f.init)]

class Rates(Table):
    """
    Time-stamped production or injection rates for wells.

    Geologic/engineering context
    ----------------------------
    - Each record captures the daily average rates for oil, water, and gas at a specific date.
    - `otype` defines whether this is a **production** (outflow) or **injection** (inflow) record.
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
    otype : Literal["production", "injection"]
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

    otype: Literal["production", "injection"] = "production"

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
    #     if self.otype not in ("production", "injection"):
    #         raise ValueError("otype must be 'production' or 'injection'.")
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
        return Rate.fields()

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
            "otype": self.otype,
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
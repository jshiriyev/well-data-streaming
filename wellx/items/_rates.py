from dataclasses import dataclass, field, fields
from typing import Optional, Literal, Dict, Any
import datetime

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
    well : str
        Well identifier (case-sensitive).
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

    date: datetime.date
    well: str

    days: Optional[int] = 1
    horizon: Optional[str] = None
    optype: Literal["production", "injection"] = "production"

    orate: Optional[float] = None
    wrate: Optional[float] = None
    grate: Optional[float] = None

    _metadata: Dict[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        if not isinstance(self.date, datetime.date):
            raise TypeError("date must be a datetime.date instance.")
        if not self.well or not isinstance(self.well, str):
            raise ValueError("well must be a non-empty string.")
        if self.days is not None and self.days <= 0:
            raise ValueError("days must be positive if provided.")
        if self.optype not in ("production", "injection"):
            raise ValueError("optype must be 'production' or 'injection'.")
        for name in ("orate", "wrate", "grate"):
            val = getattr(self, name)
            if val is not None and val < 0:
                raise ValueError(f"{name} must be >= 0.")

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
            "well": self.well,
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
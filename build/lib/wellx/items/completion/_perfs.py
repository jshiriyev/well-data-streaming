from dataclasses import dataclass, field, fields, replace

import datetime

from typing import Optional, Literal, Iterable, Self, Union, Tuple, Dict, Any

from wellx.pipes import Table

@dataclass(slots=True, frozen=True, order=True)
class PerfInterval:
    """
    Closed interval along measured depth (MD).

    Semantics
    ---------
    - `top` is the shallower MD, `base` is the deeper MD.
    - Units are not enforced; add `unit` metadata in consumers or keep consistent project-wide.
    - Bounds are inclusive: [top, base].
    - `base` must be >= `top`.

    Examples
    --------
    >>> PerfInterval(1005.0, 1092.0)
    PerfInterval(top=1005.0, base=1092.0)
    >>> PerfInterval.from_str("1005-1092")
    PerfInterval(top=1005.0, base=1092.0)
    >>> PerfInterval(1500.0, 1500.0).length
    0.0
    """

    top: float = field(metadata={"unit": "m"})
    base: float = field(default=None, metadata={"unit": "m"})

    _unit_override: Dict[str, str] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:

        top = float(self.top)
        base = top if self.base is None else float(self.base)

        if base < top:
            raise ValueError(f"PerfInterval base ({base}) must be >= top ({top}).")

        object.__setattr__(self, "top", top)
        object.__setattr__(self, "base", base)

    # convenience --------------------------------------------------------------
    @property
    def length(self) -> float:
        """Interval length (MD units)."""
        return self.base - self.top

    @property
    def midpoint(self) -> float:
        """Midpoint MD of the interval."""
        return 0.5 * (self.top + self.base)

    def contains(self, depth: float) -> bool:
        """True if `depth` lies within [top, base] (inclusive)."""
        return self.top <= depth <= self.base

    def overlaps(self, other: Self) -> bool:
        # Closed intervals overlap when max(top) <= min(base)
        return max(self.top, other.top) <= min(self.base, other.base)

    def to_str(self, template: str = "{top}-{base}") -> str:
        return template.format(top=self.top, base=self.base)

    def to_list(self) -> list[float]:
        return [self.top, self.base]

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

    @classmethod
    def from_any(cls, value: Union[Self, tuple[float, float], list[float], str],
                 delimiter: str = "-", decsep: str = ".") -> Self:
        if isinstance(value, PerfInterval):
            return value
        if isinstance(value, (tuple, list)):
            if len(value) != 2:
                raise ValueError("PerfInterval tuple/list must have exactly two numbers: (top, base).")
            top, base = min(value),max(value)
            return cls(float(top), float(base))
        if isinstance(value, str):
            return cls.from_str(value, delimiter=delimiter, decsep=decsep)
        raise TypeError("Unsupported interval type. Use PerfInterval, (top, base), or 'top-base' string.")

    @classmethod
    def from_str(cls, s: str, delimiter: str = "-", decsep: str = ".") -> Self:
        """Converts a string interval into a list of floats.

        Parameters:
        ----------
        s         : The interval string (e.g., "1005-1092").
        delimiter : The delimiter separating depths in the interval. Defaults to "-".
        decsep    : The decimal separator in the depth of the interval. Defaults to ".".
        
        Returns:
        -------
        List: A list containing one or two float values. If only one value
            is provided, the second element will be None.

        """
        try:
            parts = [p.strip() for p in s.split(delimiter)]
            if len(parts) != 2:
                raise ValueError(f"Expected 'top{delimiter}base'. Got: {s!r}")
            parts[0] = float(parts[0].replace(decsep, "."))
            parts[1] = float(parts[1].replace(decsep, "."))
            return cls(min(parts), max(parts))
        except Exception as e:
            raise ValueError(f"Invalid interval string {s!r}: {e}") from e

GUN_TYPES: set[str] = {"TCP", "HSD", "JET", "BULLET", "ABRASIVE", "PROPELLANT"}

@dataclass(slots=True, frozen=False)
class Perf:
    """
    Perforation descriptor for a well.

    What this represents
    --------------------
    A single perforated interval (in **measured depth, MD**) with optional
    metadata such as horizon and gun type.

    Domain assumptions
    ------------------
    - Depths are MD (measured depth); if you work in TVD or TMD, state that and be consistent.
    - Units are project-defined (e.g., meters or feet). Keep them consistent or
      record units at a higher level (dataset/track).
    - interval top must be shallower or equal to interval base.
    - A `date` can represent the operational date the perforation was made or recorded.

    Parameters
    ----------
    well : str
        Well identifier (non-empty).
    top : float
        Top of the perforation interval (MD).
    base : float
        Base of the perforation interval (MD). If omitted, equals `top`.
    date : datetime.date, optional
        Perforation date (or record date).
    horizon : str, optional
        Zone/formation label.
    guntype : str, optional
        Perforation gun/type descriptor. A small vocabulary is provided in `GUN_TYPES`
        but free-form values are allowed (will be uppercased in normalization).

    Convenience
    -----------
    - `sort_key()` returns a `(well, top, base)` tuple for stable sorting.
    - `length` property forwards to interval `length`.
    - `fields()` returns declared dataclass fields in order (handy for tabular exports).

    """
    well: str

    top: float = field(metadata={"unit": "m"})
    base: float = field(default=None, metadata={"unit": "m"})

    date: Optional[datetime.date] = None
    horizon: Optional[str] = None
    guntype: Optional[str] = None

    _unit_override: Dict[str, str] = field(default_factory=dict, init=False, repr=False)

    # normalize/validate -------------------------------------------------------
    def __post_init__(self) -> None:
        if not isinstance(self.well, str) or not self.well.strip():
            raise ValueError("well must be a non-empty string")

        if self.date is not None and not isinstance(self.date, datetime.date):
            raise TypeError("date must be a datetime.date (or None)")

        top = float(self.top)
        base = top if self.base is None else float(self.base)

        gt = None
        if self.guntype is not None:
            gt = self.guntype.strip().upper()

        object.__setattr__(self, "top", top)
        object.__setattr__(self, "base", base)
        object.__setattr__(self, "guntype", gt)

    # convenience --------------------------------------------------------------
    @property
    def length(self) -> float:
        """PerfInterval length in depth units (project-defined)."""
        return PerfInterval(self.top,self.base).length

    @property
    def midpoint(self) -> float:
        """Midpoint MD of the interval."""
        return PerfInterval(self.top,self.base).midpoint

    def contains(self, depth: float) -> bool:
        """True if `depth` lies within [top, base] (inclusive)."""
        return PerfInterval(self.top,self.base).contains(depth)

    def overlaps(self, other: Self) -> bool:
        # Closed intervals overlap when max(top) <= min(base)
        return PerfInterval(self.top,self.base).overlaps(PerfInterval(other.top,other.base))

    def sort_key(self) -> tuple[str, float, float]:
        """Stable sort key: (well, top, base)."""
        return (self.well, self.top, self.base)

    def to_dict(self) -> Dict[str, Any]:
        """JSON/DF-friendly representation."""
        out = {
            "well": self.well,
            "top": self.top,
            "base": self.base,
            "date": self.date.isoformat() if self.date else None,
            "horizon": self.horizon,
            "guntype": self.guntype,
        }
        return out

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

    @staticmethod
    def fields() -> list[str]:
        """List of dataclass field names (stable order)."""
        return [f.name for f in fields(Perf) if f.init]

class PerfTable():
    """A collection of 'Perf' objects with list-like access."""

    def __init__(self,*args:Perf):

        self._list = list(args)

    @staticmethod
    def fields() -> list:
        """Returns the list of field names in the Perf dataclass."""
        return Perf.fields()

    def __getitem__(self,key):
        """Retrieves a 'Perf' object by index."""
        return self._list[key]

    def __iter__(self):
        """Allows iteration over the 'Perf' objects."""
        return iter(self._list)

    def __len__(self) -> int:
        """Returns the number of 'Perf' objects."""
        return len(self._list)

    def add(self,**kwargs):
        """Adds one perforation item."""
        self._list.append(Perf(**kwargs))

    def append(self,perf:Perf) -> None:
        """Adds a new 'Perf' object to the collection."""
        if not isinstance(perf, Perf):
            raise TypeError("Only Perf objects can be added.")
        self._list.append(perf)

    def extend(self,perfs:Perf) -> None:
        """Adds a new 'Perf' object to the collection."""
        for perf in perfs:
            self.append(perf)

    def __getattr__(self,key):
        """Forwards attribute access to the internal list object."""
        return getattr(self._list,key)

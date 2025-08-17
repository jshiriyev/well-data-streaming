from dataclasses import dataclass, fields

import datetime

from typing import Optional, Literal, Iterable, Self, Union

from wellx.pipes import Table

@dataclass(slots=True, frozen=True, order=True)
class Interval:
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
    >>> Interval(1005.0, 1092.0)
    Interval(top=1005.0, base=1092.0)
    >>> Interval.from_str("1005-1092")
    Interval(top=1005.0, base=1092.0)
    >>> Interval(1500.0, 1500.0).length
    0.0
    """

    top: float
    base: float

    def __post_init__(self) -> None:
        if self.base < self.top:
            raise ValueError(f"Interval base ({self.base}) must be >= top ({self.top}).")

    # convenience --------------------------------------------------------------
    @property
    def length(self) -> float:
        return self.base - self.top

    def contains(self, depth: float) -> bool:
        return self.top <= depth <= self.base

    def overlaps(self, other: Self) -> bool:
        # Closed intervals overlap when max(top) <= min(base)
        return max(self.top, other.top) <= min(self.base, other.base)

    def to_str(self, template: str = "{top}-{base}") -> str:
        return template.format(top=self.top, base=self.base)

    def to_list(self) -> list[float]:
        return [self.top, self.base]

    @classmethod
    def from_any(cls, value: Union[Self, tuple[float, float], list[float], str],
                 delimiter: str = "-", decsep: str = ".") -> Self:
        if isinstance(value, Interval):
            return value
        if isinstance(value, (tuple, list)):
            if len(value) != 2:
                raise ValueError("Interval tuple/list must have exactly two numbers: (top, base).")
            top, base = min(value),max(value)
            return cls(float(top), float(base))
        if isinstance(value, str):
            return cls.from_str(value, delimiter=delimiter, decsep=decsep)
        raise TypeError("Unsupported interval type. Use Interval, (top, base), or 'top-base' string.")

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

@dataclass(slots=True, frozen=False)
class Perf:
    """
    Perforation descriptor for a well.

    What this represents
    --------------------
    A single perforated interval (in **measured depth, MD**) with optional
    metadata such as horizon and gun type. The interval is **inclusive** and
    normalized to an `Interval` object (`top <= base`) during initialization.

    Domain assumptions
    ------------------
    - Depths are MD (measured depth); if you work in TVD or TMD, state that and be consistent.
    - Units are project-defined (e.g., meters or feet). Keep them consistent or
      record units at a higher level (dataset/track).
    - `interval.top` must be shallower or equal to `interval.base`.
    - A `date` can represent the operational date the perforation was made or recorded.

    Parameters
    ----------
    well : str
        Well identifier (non-empty).
    interval : Interval | tuple[float, float] | list[float] | str
        Perforation as either an `Interval`, a pair `(top, base)`, or a string "top-base".
        Examples: `Interval(1005, 1092)`, `(1005, 1092)`, `"1005-1092"`.
    date : datetime.date, optional
        Perforation date (or record date).
    horizon : str, optional
        Horizon/completion/zone label.
    guntype : {'TCP','HSD','Jet','Bullet','Abrasive','Propellant'}, optional
        Perforation gun/type descriptor; keep free-form `str` if your data varies.

    Convenience
    -----------
    - `sort_key()` returns a `(well, interval.top, interval.base)` tuple for stable sorting.
    - `length` property forwards to `interval.length`.
    - `fields()` returns declared dataclass fields in order (handy for tabular exports).

    Examples
    --------
    >>> Perf(well="G-12", interval=(1005, 1092)).interval.to_str()
    '1005-1092'
    >>> Perf(well="G-12", interval="1005-1092").length
    87.0
    """
    well: str
    interval: Union[Interval, tuple[float, float], list[float], str]

    date: Optional[datetime.date] = None
    horizon: Optional[str] = None
    guntype: Optional[str] = None

    # normalize/validate -------------------------------------------------------
    def __post_init__(self) -> None:
        if not isinstance(self.well, str) or not self.well.strip():
            raise ValueError("well must be a non-empty string")

        # normalize interval
        self.interval = Interval.from_any(self.interval)

    # convenience --------------------------------------------------------------
    @property
    def length(self) -> float:
        """Interval length in depth units (project-defined)."""
        return self.interval.length

    def sort_key(self) -> tuple[str, float, float]:
        """Stable sort key: (well, interval.top, interval.base)."""
        return (self.well, self.interval.top, self.interval.base)

    @staticmethod
    def fields() -> list[str]:
        """List of dataclass field names (stable order)."""
        return [f.name for f in fields(Perf)]

class Perfs():
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

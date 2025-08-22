from dataclasses import dataclass, field, fields as dcfields, is_dataclass

import datetime

from typing import Iterable, Mapping, Optional, Literal, Dict, Any, List, Union, Sequence

import pandas as pd

from wellx.pipes import Table

@dataclass(slots=True, frozen=False)
class Rate:
    """
    Time-stamped surface rates for a single well.

    Domain assumptions
    ------------------
    - Rate is *surface-standard* and non-negative.
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
    formation : str, optional
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

    formation: Optional[str] = None

    otype: Literal["production", "injection"] = "production"

    method: Optional[str] = None # production or injection method such as fountain, gas-lift, etc.

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
        for f in dcfields(self):                 # dataclasses.fields -> tuple[Field, ...]
            if f.name == key:
                return f.metadata.get("unit")  # metadata is a Mapping
        raise AttributeError(f"No field named {key!r}")

    def set_unit(self, **kwargs) -> None:
        """Override the unit for a field at runtime (does not change class metadata)."""
        for key, unit in kwargs.items():
            if key not in {f.name for f in dcfields(self)}:
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
        return [f.name for f in dcfields(Rate) if f.init]

RateLike = Union["Rate", Mapping[str, Any]]

RateUnit = {f.name: unit for f in dcfields(Rate) if (unit := f.metadata.get("unit"))}

class RateTable(Table):
    """
    Table of well rates with schema taken from Rate dataclass.

    - Keys of `tiein` are exactly the Rate.fields() names (date, well, orate, ...).
    - Values of `tiein` point to actual column names in the frame (default: identity).
    - Uses Rate(**row) to coerce/validate rows when requested.
    """

    # Optional default unit scales: column_name -> multiplicative factor
    # Example: {"orate": 1/6.2898}  # STB/d -> m3/d
    DEFAULT_UNITS: Dict[str, float] = RateUnit

    # -------- core construction --------
    def __init__(
        self,
        data: Optional[Iterable[RateLike] | pd.DataFrame] = None,
        *,
        tiein: Optional[Dict[str, str]] = None,
        coerce: bool = True,
        copy: bool = False,
        **kwargs: Any,
    ):

        # Build tiein: keys must be Rate fields
        if tiein is None:
            tiein = {k: k for k in Rate.fields()}
        else:
            # ensure we at least have identity for unspecified fields
            tiein = {**{k: k for k in Rate.fields()}, **tiein}

        if isinstance(data, pd.DataFrame):
            # align/rename dataframe columns according to tiein values
            df = data.copy() if copy else data
        else:
            rows = []
            if data is not None:
                for item in data:
                    rows.append(self._row_to_dict(item, validate=validate, coerce=coerce))
            df = pd.DataFrame(rows, columns=Rate.fields()).copy() if copy else pd.DataFrame(rows, columns=Rate.fields())

        # Guarantee a dict so Table.__getattr__ doesn't trip on None
        kwargs["tiein"] = dict(tiein)

        super().__init__(df, **kwargs)

    # Keep subclass through pandas ops
    @property
    def _constructor(self):
        def _c(*args, **kwargs):
            out = RateTable(*args, **kwargs)
            # Ensure tiein survives pandas operations
            current = getattr(self, "_tiein", None) or {}
            object.__setattr__(out, "_tiein", dict(current))
            return out
        return _c

    def _row_to_dict(self, item: RateLike, *, validate: bool, coerce: bool) -> Dict[str, Any]:

        if is_dataclass(item) and isinstance(item, Rate):
            row = {f.name: getattr(item, f.name) for f in dcfields(Rate) if f.init}
        elif isinstance(item, Mapping):
            row = dict(item)
        else:
            raise TypeError(f"Unsupported row type: {type(item)!r}. Expected Rate or Mapping.")

        # Drop extras; add missing as None
        cleaned = {k: row.get(k, None) for k in Rate.fields()}

        if validate:
            if coerce:
                # (1) enforce required types/rules using Rate; (2) normalize out values
                coerced = Rate(**cleaned)
                cleaned = {f.name: getattr(coerced, f.name) for f in dcfields(Rate) if f.init}
            else:
                self._basic_row_checks(cleaned)

        return cleaned

    def _basic_row_checks(self, row: Mapping[str, Any]) -> None:
        # mirror Rate.__post_init__ invariants lightly (no coercion)
        must = ("well", "date", "otype", "orate", "wrate", "grate")
        for k in must:
            if k not in row:
                raise ValueError(f"Missing required field: {k}")

        if not isinstance(row["date"], datetime.date):
            raise TypeError("date must be a datetime.date")
        if not isinstance(row["well"], str) or not row["well"].strip():
            raise ValueError("well must be a non-empty string")
        if row["otype"] not in ("production", "injection"):
            raise ValueError("otype must be 'production' or 'injection'")

        for k in ("orate", "wrate", "grate"):
            v = row.get(k)
            if v is not None and float(v) < 0.0:
                raise ValueError(f"{k} must be >= 0")

        if row.get("days") is not None and row["days"] < 0:
            raise ValueError("days must be >= 0")
        if row.get("choke") is not None and row["choke"] < 0:
            raise ValueError("choke must be >= 0")

    # -------- alt constructors / round-trips --------
    @classmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        *,
        tiein: Optional[Dict[str, str]] = None,
        unit_scales: Optional[Dict[str, float]] = None,
        validate: bool = True,
        coerce: bool = True,
        **kwargs: Any,
    ) -> "RateTable":
        return cls(df, tiein=tiein, unit_scales=unit_scales, validate=validate, coerce=coerce, **kwargs)

    @classmethod
    def from_rates(cls, rates: Iterable["Rate"], **kwargs: Any) -> "RateTable":
        return cls(rates, **kwargs)

    def to_rates(self) -> List["Rate"]:
        out: List["Rate"] = []
        for _, row in self.iterrows():
            payload = {k: row[k] for k in Rate.fields()}
            out.append(Rate(**payload))
        return out

    def append_rate(self, rate: "Rate") -> "RateTable":
        row = self._row_to_dict(rate, validate=True, coerce=False)
        new_df = pd.concat([pd.DataFrame(self), pd.DataFrame([row])], ignore_index=True)
        # preserve current tiein
        tie = getattr(self, "_tiein", {}) or {}
        return RateTable.from_dataframe(new_df, tiein=dict(tie), validate=True)

    # -------- units --------
    def convert_units(self, unit_scales: Dict[str, float]) -> "RateTable":
        """
        Return a new RateTable with column-wise multiplicative scales applied.
        Only affects numeric columns present in 'unit_scales'.
        """
        df = pd.DataFrame(self).copy()
        for col, s in (unit_scales or {}).items():
            if col in df.columns and s not in (None, 1):
                df[col] = df[col].astype(float) * float(s)

        tie = getattr(self, "_tiein", {}) or {}
        return RateTable.from_dataframe(df, tiein=dict(tie), validate=False)

    @staticmethod
    def get_current_formation(rates:pd.DataFrame,well:str,date:datetime.date=None):
        return rates[rates["well"] == well].iloc[-1].formation

    @staticmethod
    def fields() -> list[str]:
        return Rate.fields()
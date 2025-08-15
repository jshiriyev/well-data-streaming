from dataclasses import dataclass, replace
from dataclasses import field as dataclassfield

from typing import Optional, Tuple, Dict, Any

from .general import Name, Status
from .location import Survey, Tops
from .completion import Perfs, Layout

@dataclass(frozen=True, slots=True)
class Well:
    """
    Well — immutable-ish aggregate for all well-centric data.

    Purpose
    -------
    Acts as the **single source of truth** for one well. It aggregates strongly-typed
    sub-objects (location, completion, operational status) and exposes *builder-style*
    methods that return **new** `Well` instances on change, preserving invariants and
    making the object safe for web apps and multi-user flows.

    Key ideas
    ---------
    - **Immutable-ish**: public "setters" are not mutating; they return a new Well via `dataclasses.replace`.
    - **Typed sub-objects**: `Survey`, `Tops`, `Perfs`, `Layout`, `Status`.
    - **Validation light**: high-level checks in `.validate()`; detailed checks live in sub-classes.

    Attributes
    ----------
    name : Name
        Well name wrapper (e.g., supports canonical formatting).
    status : Optional[Status]
        Current operational status **interval** (e.g., drilling, production). May be None.
    survey : Optional[Survey]
        Trajectory data container.
    tops : Optional[Tops]
        Formation tops (MD-based).
    layout : Optional[Layout]
        Surface/subsurface equipment layout (if modeled).
    perfs : Optional[Perfs]
        Perforation dataset (intervals).
    logs : Tuple[str, ...]
        Paths/IDs of LAS (or other) evaluation files attached to the well.
    plts : Optional[str]
        Pointer/ID to most recent PLT dataset (or a human label).
    units : Dict[str, str]
        Lightweight units metadata (e.g., {"MD": "m", "TVD": "m", "oil": "bbl/d"}).

    Notes
    -----
    - Prefer creating/attaching validated objects: e.g., `Well.with_survey(Survey(...))`.
    - Keep heavy analytics (curves, correlations) in the respective modules; `Well` is orchestration.
    """

    # ---- core identity ----
    name     : Name

    operator : str = None
    field    : str = None
    county   : str = None
    state    : str = None
    country  : str = None
    service  : str = None

    status   : Optional[Status] = None            # current interval (from your Status class)

    # ---- location data ----
    survey: Optional[Survey] = None
    tops: Optional[Tops] = None

    # ---- completion data ----
    layout: Optional[Layout] = None
    perfs: Optional[Perfs] = None

    # ---- formation evaluation data ----
    logs: Tuple[str, ...] = dataclassfield(default_factory=tuple)

    # ---- production surveillance data ----
    plts: Optional[str] = None                  # e.g., latest PLT run id/label

    # ---- metadata ----
    units: Dict[str, str] = dataclassfield(default_factory=dict)

    # ------------------------------------------------------------------
    # Builder-style "updaters" (return **new** Well; do not mutate self)
    # ------------------------------------------------------------------
    def with_name(self, value: str | Name) -> "Well":
        """Return a new Well with a different name."""
        nm = value if isinstance(value, Name) else Name(str(value))
        return replace(self, name=nm)

    def with_status(self, status: Optional[Status]) -> "Well":
        """Return a new Well with the current operational Status set/cleared."""
        return replace(self, status=status)

    def with_survey(self, survey: Optional[Survey]) -> "Well":
        """Return a new Well with a (new) Survey."""
        return replace(self, survey=survey)

    def with_tops(self, tops: Optional[Tops]) -> "Well":
        """Return a new Well with (new) formation Tops."""
        return replace(self, tops=tops)

    def with_layout(self, layout: Optional[Layout]) -> "Well":
        """Return a new Well with a (new) Layout."""
        return replace(self, layout=layout)

    def with_perfs(self, perfs: Optional[Perfs]) -> "Well":
        """Return a new Well with a (new) Perfs collection."""
        return replace(self, perfs=perfs)

    def with_units(self, units: Dict[str, str]) -> "Well":
        """Return a new Well with merged units metadata (existing keys are overridden)."""
        merged = {**self.units, **(units or {})}
        return replace(self, units=merged)

    def add_log(self, *paths: str) -> "Well":
        """
        Return a new Well with LAS (or other) file identifiers appended.
        Duplicate suppression is applied while preserving order.
        """
        new = list(self.logs)
        for p in paths:
            if p and p not in new:
                new.append(p)
        return replace(self, logs=tuple(new))

    # ------------------------------------------------------------------
    # Convenience accessors / summaries
    # ------------------------------------------------------------------
    @property
    def name_text(self) -> str:
        """Raw well name as text (convenience)."""
        # Assume Name dataclass has attribute .name; otherwise fallback to str(Name)
        return getattr(self.name, "name", str(self.name))

    def current_status_code(self) -> Optional[str]:
        """Current status code as text (e.g., 'drilling'), or None."""
        if self.status is None:
            return None
        # Your Status class carries `.code.value`
        return getattr(getattr(self.status, "code", None), "value", None)

    def status_color(self, palette: Optional[Dict[Any, str]] = None) -> Optional[str]:
        """
        Recommended color for the current status, if any.
        Delegates to your Status.color(...) method.
        """
        if self.status is None:
            return None
        color_fn = getattr(self.status, "color", None)
        return color_fn(palette) if callable(color_fn) else None

    def summary(self) -> Dict[str, Any]:
        """
        Lightweight summary for dashboards/logs.
        Safely handles missing sub-objects.
        """
        md_end = float(self.survey.MD[-1]) if (self.survey and getattr(self.survey, "MD", None) is not None) else None
        tvd_end = float(self.survey.TVD[-1]) if (self.survey and getattr(self.survey, "TVD", None) is not None) else None
        tops_count = len(self.tops.formations) if self.tops else 0
        perfs_count = len(getattr(self.perfs, "intervals", [])) if self.perfs and hasattr(self.perfs, "intervals") else 0
        return {
            "name": self.name_text,
            "status": self.current_status_code(),
            "status_color": self.status_color(),
            "md_end": md_end,
            "tvd_end": tvd_end,
            "tops": tops_count,
            "perfs": perfs_count,
            "log_files": len(self.logs),
        }

    # ------------------------------------------------------------------
    # I/O helpers (JSON / dict friendly)
    # ------------------------------------------------------------------
    def to_dict(self, deep: bool = False) -> Dict[str, Any]:
        """
        Serialize Well to a plain dict. If `deep=True`, include nested object dicts
        using their own `to_dict()` when available; otherwise include light markers.
        """
        def maybe(obj):
            if not obj:
                return None
            # Prefer an object's to_dict(); otherwise return a light marker
            if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
                return obj.to_dict()
            # Fall back to key highlights to avoid heavy payloads
            if isinstance(obj, Survey):
                return {"stations": int(obj.MD.size) if getattr(obj, "MD", None) is not None else 0}
            if isinstance(obj, Tops):
                return {"formations": obj.formations}
            if isinstance(obj, Perfs):
                return {"count": len(getattr(obj, "intervals", []))}
            if isinstance(obj, Layout):
                return {"type": "layout"}
            return str(obj)

        return {
            "name": self.name_text,
            "units": dict(self.units),
            "status": self.status.to_dict() if (self.status and hasattr(self.status, "to_dict")) else self.current_status_code(),
            "survey": maybe(self.survey) if deep else ("survey" if self.survey else None),
            "tops": maybe(self.tops) if deep else ("tops" if self.tops else None),
            "layout": maybe(self.layout) if deep else ("layout" if self.layout else None),
            "perfs": maybe(self.perfs) if deep else ("perfs" if self.perfs else None),
            "logs": list(self.logs),
            "plts": self.plts,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Well":
        """
        Construct a Well from a minimal dict (expects plain fields; nested objects
        should be built by their own constructors beforehand).
        """
        nm = data.get("name")
        name_obj = nm if isinstance(nm, Name) else Name(str(nm))
        status_obj = data.get("status")
        # Accept a dict (Status.to_dict form), an instance, or a plain code string
        if isinstance(status_obj, dict) and "code" in status_obj and hasattr(Status, "from_dict"):
            status_obj = Status.from_dict(status_obj)  # optional, if you implement it
        elif isinstance(status_obj, str) and hasattr(Status, "make_status"):
            # if you kept make_status helper; otherwise leave as None or map yourself
            status_obj = None  # avoid guessing if helper is absent
        return cls(
            name=name_obj,
            status=status_obj if isinstance(status_obj, Status) else None,
            survey=data.get("survey") if isinstance(data.get("survey"), Survey) else None,
            tops=data.get("tops") if isinstance(data.get("tops"), Tops) else None,
            layout=data.get("layout") if isinstance(data.get("layout"), Layout) else None,
            perfs=data.get("perfs") if isinstance(data.get("perfs"), Perfs) else None,
            logs=tuple(data.get("logs", []) or []),
            units=dict(data.get("units", {}) or {}),
            plts=data.get("plts"),
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate(self) -> None:
        """
        Raise ValueError if internal consistency is broken.
        (Defer heavy validation to sub-objects.)
        """
        if not self.name_text:
            raise ValueError("Well.name must be non-empty.")
        if self.survey and getattr(self.survey, "MD", None) is None:
            raise ValueError("Survey present but MD is missing.")
        if self.tops and not getattr(self.tops, "formations", None):
            raise ValueError("Tops present but contains no formations.")
        # Example cross-check: tops must be within survey MD range if both present
        if self.survey and self.tops and getattr(self.survey, "MD", None) is not None:
            md_min, md_max = float(self.survey.MD[0]), float(self.survey.MD[-1])
            for md in getattr(self.tops, "depths", []):
                if md < md_min or md > md_max:
                    # Soft rule—choose warning/log instead if you prefer
                    raise ValueError(f"Top MD {md} outside survey range [{md_min}, {md_max}].")

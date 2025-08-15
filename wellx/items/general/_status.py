from dataclasses import dataclass, field, fields, replace
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta


class StatusCode(str, Enum):
    # Planning / construction
    PROSPECT       = "prospect"
    CONSTRUCTION   = "construction"
    MOBILIZATION   = "mobilization"

    # Drilling & wellbore ops
    DRILLING       = "drilling"
    SIDETRACK      = "sidetrack"
    FISHING        = "fishing"
    WORKOVER       = "workover"
    COMPLETION     = "completion"
    INSTALLATION   = "installation"
    RECOMPLETION   = "recompletion"

    # Production / injection / testing
    PRODUCTION     = "production"
    INJECTION      = "injection"
    TESTING        = "testing"      # well tests / flowback
    OPTIMIZATION   = "optimization"
    REMEDIATION    = "remediation"  # e.g., scale, conformance

    # Downtime / logistics
    DELAY          = "delay"        # generic waiting on …
    NPT            = "npt"          # non-productive time
    MAINTENANCE    = "maintenance"
    SUSPENDED      = "suspended"    # temporarily abandoned
    SHUT_IN        = "shut_in"
    ABANDONMENT    = "abandonment"  # P&A


# GitHub/Plotly-friendly palette (hex). You can override with your own dict.
DEFAULT_PALETTE: Dict[StatusCode, str] = {
    StatusCode.PROSPECT:     "#e5e7eb",  # light gray
    StatusCode.CONSTRUCTION: "#9ca3af",  # gray
    StatusCode.MOBILIZATION: "#111827",  # near black

    StatusCode.DRILLING:     "#7c3aed",  # purple
    StatusCode.SIDETRACK:    "#1d4ed8",  # blue (dark)
    StatusCode.FISHING:      "#ef4444",  # red
    StatusCode.WORKOVER:     "#0ea5e9",  # sky blue
    StatusCode.COMPLETION:   "#f59e0b",  # amber
    StatusCode.INSTALLATION: "#ec4899",  # pink
    StatusCode.RECOMPLETION: "#22c55e",  # green

    StatusCode.PRODUCTION:   "#166534",  # dark green
    StatusCode.INJECTION:    "#2563eb",  # blue
    StatusCode.TESTING:      "#a855f7",  # violet
    StatusCode.OPTIMIZATION: "#86efac",  # light green
    StatusCode.REMEDIATION:  "#34d399",  # green

    StatusCode.DELAY:        "#e5e7eb",  # light gray
    StatusCode.NPT:          "#f87171",  # salmon red
    StatusCode.MAINTENANCE:  "#fb923c",  # orange
    StatusCode.SUSPENDED:    "#94a3b8",  # slate
    StatusCode.SHUT_IN:      "#475569",  # deep slate
    StatusCode.ABANDONMENT:  "#0f172a",  # very dark slate
}


def parse_status(value: str) -> StatusCode:
    """
    Map a free-text status to StatusCode (case-insensitive, handles common aliases).
    Raises ValueError if no mapping found.
    """
    v = value.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "prod": "production",
        "inject": "injection",
        "recomp": "recompletion",
        "p_and_a": "abandonment",
        "pa": "abandonment",
        "wait_on_weather": "delay",
        "wow": "delay",
        "testing": "testing",
        "well_test": "testing",
        "shutin": "shut_in",
        "npt": "npt",
    }
    v = aliases.get(v, v)
    try:
        return StatusCode(v)
    except ValueError as e:
        raise ValueError(f"Unknown status '{value}'. Allowed: {[s.value for s in StatusCode]}") from e


@dataclass(frozen=True, slots=True)
class Status:
    """
    A single status interval for a well (immutable-ish record).

    Parameters
    ----------
    code : StatusCode
        Normalized status code (see StatusCode enum).
    started_at : datetime
        UTC timestamp when status began.
    ended_at : Optional[datetime]
        UTC timestamp when status ended (None -> ongoing).
    well : str
        Well identifier.
    description : Optional[str]
        Free-text note (e.g., 'WOB high, ROP steady', 'Shut-in for PLT').
    source : Optional[str]
        Data origin (e.g., 'daily_report', 'rt_stream', 'manual').
    meta : Dict[str, Any]
        Arbitrary metadata (units, tags, responsible team, etc.)

    Notes
    -----
    - All times should be timezone-aware UTC.
    - Use `.color()` to fetch a plotting color for the status (override palette if needed).
    """
    code: StatusCode
    started_at: datetime
    ended_at: Optional[datetime]
    well: str
    description: Optional[str] = None
    source: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict, repr=False)

    # ---- Validation ----
    def __post_init__(self):
        if self.started_at.tzinfo is None or self.started_at.utcoffset() is None:
            raise ValueError("started_at must be timezone-aware (UTC).")
        if self.ended_at is not None:
            if self.ended_at.tzinfo is None or self.ended_at.utcoffset() is None:
                raise ValueError("ended_at must be timezone-aware (UTC).")
            if self.ended_at < self.started_at:
                raise ValueError("ended_at cannot be earlier than started_at.")
        if not self.well:
            raise ValueError("well must be a non-empty string.")

    # ---- Convenience ----
    @property
    def is_active(self) -> bool:
        """True if the status has no end time."""
        return self.ended_at is None

    def duration_hours(self) -> Optional[float]:
        """Return duration in hours (None if ongoing)."""
        if self.ended_at is None:
            return None
        delta: timedelta = self.ended_at - self.started_at
        return delta.total_seconds() / 3600.0

    def color(self, palette: Optional[Dict[StatusCode, str]] = None) -> str:
        """Return hex color for this status (falls back to DEFAULT_PALETTE)."""
        pal = palette or DEFAULT_PALETTE
        return pal.get(self.code, "#64748b")  # fallback: slate-500

    def to_dict(self) -> Dict[str, Any]:
        """JSON/DataFrame friendly representation."""
        d = {
            "well": self.well,
            "code": self.code.value,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "description": self.description,
            "source": self.source,
        }
        d.update(self.meta)
        return d

    @staticmethod
    def fields() -> list:
        """Field names for I/O schemas."""
        return [f.name for f in fields(Status) if f.name != "meta"]

    # Immutable-ish "updaters"
    def with_end(self, ended_at: datetime) -> "Status":
        """Return a copy with an end time set (validates chronology)."""
        return replace(self, ended_at=ended_at)

    def with_description(self, text: str) -> "Status":
        return replace(self, description=text)

    def with_meta(self, **kwargs) -> "Status":
        new_meta = dict(self.meta)
        new_meta.update(kwargs)
        return replace(self, meta=new_meta)

# --- Example helper to construct from simple strings/datetimes ---
def make_status(
    well: str,
    status: str | StatusCode,
    start_utc: datetime,
    end_utc: Optional[datetime] = None,
    **kwargs: Any
) -> Status:
    """
    Quickly create a Status from a free-text status or StatusCode.
    `start_utc` / `end_utc` must be timezone-aware (UTC).
    """
    code = parse_status(status) if isinstance(status, str) else status
    return Status(code=code, started_at=start_utc, ended_at=end_utc, well=well, **kwargs)

if __name__ == "__main__":

    from datetime import datetime, timezone, timedelta

    ws = make_status(
        well="GUN-38",
        status="drilling",
        start_utc=datetime(2025, 8, 14, 6, 0, tzinfo=timezone.utc),
        description="Section 12-1/4 in progress",
        source="daily_report",
    )

    print(ws.code.value)       # 'drilling'
    print(ws.color())          # '#7c3aed' (purple)
    print(ws.is_active)        # True

    ws2 = ws.with_end(datetime(2025, 8, 14, 18, 0, tzinfo=timezone.utc))
    print(ws2.duration_hours())  # 12.0
    print(ws2.to_dict())
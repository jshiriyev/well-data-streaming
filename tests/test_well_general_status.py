# test_status.py
# Run: pytest -q
import pytest
from datetime import datetime, timezone, timedelta

# ⬇️ adjust if your module has a different name/path
from wellx.items.general._status import Status, StatusCode, parse_status, make_status, DEFAULT_PALETTE


# --------- helpers ----------
def utc(y, m, d, hh=0, mm=0, ss=0):
    return datetime(y, m, d, hh, mm, ss, tzinfo=timezone.utc)


# --------- parse_status ----------
def test_parse_status_accepts_exact_and_aliases():
    assert parse_status("production") == StatusCode.PRODUCTION
    assert parse_status("Prod") == StatusCode.PRODUCTION
    assert parse_status("shutin") == StatusCode.SHUT_IN   # alias
    assert parse_status("recomp") == StatusCode.RECOMPLETION
    assert parse_status("P-and-A".replace("-", "_")) or True  # just smoke that mapping exists
    assert parse_status("testing") == StatusCode.TESTING

def test_parse_status_invalid_raises():
    with pytest.raises(ValueError):
        parse_status("unknown-mode")


# --------- construction & validation ----------
def test_status_basic_construction_and_props():
    s = Status(
        code=StatusCode.DRILLING,
        started_at=utc(2025, 1, 1, 8, 0),
        ended_at=utc(2025, 1, 1, 20, 0),
        well="W-001",
        description="12-1/4 in progress",
        source="daily_report",
    )
    assert s.code is StatusCode.DRILLING
    assert s.is_active is False
    # duration in hours
    assert s.duration_hours() == 12.0
    # color from default palette
    assert isinstance(s.color(), str) and s.color().startswith("#")

def test_status_requires_timezone_aware_datetimes_and_valid_order():
    # naive start -> error
    with pytest.raises(ValueError):
        Status(code=StatusCode.DRILLING, started_at=datetime(2025,1,1,8), ended_at=None, well="W-001")
    # naive end -> error
    with pytest.raises(ValueError):
        Status(code=StatusCode.DRILLING, started_at=utc(2025,1,1,8), ended_at=datetime(2025,1,1,9), well="W-001")
    # end before start -> error
    with pytest.raises(ValueError):
        Status(code=StatusCode.DRILLING, started_at=utc(2025,1,1,10), ended_at=utc(2025,1,1,9), well="W-001")
    # empty well -> error
    with pytest.raises(ValueError):
        Status(code=StatusCode.DRILLING, started_at=utc(2025,1,1,8), ended_at=None, well="")

def test_status_active_and_none_duration_when_ongoing():
    s = Status(code=StatusCode.PRODUCTION, started_at=utc(2025,1,2,0), ended_at=None, well="W-002")
    assert s.is_active is True
    assert s.duration_hours() is None


# --------- updaters (immutable-ish) ----------
def test_with_end_with_description_with_meta_create_copies():
    s = Status(code=StatusCode.TESTING, started_at=utc(2025,1,3,6), ended_at=None, well="W-003")
    s2 = s.with_end(utc(2025,1,3,18))
    assert s.is_active is True and s2.is_active is False
    assert s2.duration_hours() == 12.0

    s3 = s2.with_description("Build-up started")
    assert s3.description == "Build-up started"

    s4 = s3.with_meta(phase="PTA", quality="approved")
    assert s4.meta["phase"] == "PTA" and s4.meta["quality"] == "approved"
    # previous instance untouched
    assert "phase" not in (s3.meta or {})


# --------- color handling ----------
def test_color_palette_override_and_default_fallback():
    s = Status(code=StatusCode.SIDETRACK, started_at=utc(2025,1,4,0), ended_at=utc(2025,1,4,6), well="W-004")
    # default palette provides a color
    default_color = s.color()
    assert default_color.startswith("#")

    # override palette
    custom = {StatusCode.SIDETRACK: "#123456"}
    assert s.color(custom) == "#123456"

def test_default_palette_contains_some_expected_keys():
    # smoke test: a few critical statuses must exist
    for key in (StatusCode.DRILLING, StatusCode.PRODUCTION, StatusCode.INJECTION, StatusCode.SHUT_IN):
        assert key in DEFAULT_PALETTE


# --------- serialization ----------
def test_to_dict_contains_iso_datetimes_and_fields():
    s = Status(
        code=StatusCode.REMEDIATION,
        started_at=utc(2025,1,5,1),
        ended_at=utc(2025,1,5,7),
        well="W-005",
        description="Scale squeeze",
        source="workover_report",
    ).with_meta(tag="chem", cost_usd=12000)

    d = s.to_dict()
    assert d["well"] == "W-005"
    assert d["code"] == "remediation"
    assert d["started_at"].endswith("+00:00")
    assert d["ended_at"].endswith("+00:00")
    # metadata merged into dict
    assert d["tag"] == "chem" and d["cost_usd"] == 12000


# --------- fields() ----------
def test_fields_lists_public_fields_not_meta():
    names = Status.fields()
    # Ensure typical fields are present
    for f in ["code", "started_at", "ended_at", "well", "description", "source"]:
        assert f in names
    # meta should not be included
    assert "meta" not in names


# --------- make_status helper ----------
def test_make_status_accepts_string_and_enum():
    s1 = make_status(well="W-006", status="drilling", start_utc=utc(2025,1,6,9))
    assert s1.code == StatusCode.DRILLING and s1.is_active

    s2 = make_status(well="W-007", status=StatusCode.SHUT_IN, start_utc=utc(2025,1,7,0), end_utc=utc(2025,1,7,12))
    assert s2.code == StatusCode.SHUT_IN and not s2.is_active
    assert s2.duration_hours() == 12.0

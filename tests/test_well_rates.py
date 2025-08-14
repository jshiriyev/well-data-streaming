# test_rates.py
# Run: pytest -q
import datetime as dt
import pytest

# Adjust this import to your actual module filename
from wellx.items import Rates


# ---------- Helpers ----------
def d(y, m, day):
    return dt.date(y, m, day)


# ---------- Schema ----------
def test_fields_schema():
    assert Rates.fields() == [
        "date", "well", "days", "horizon", "optype", "orate", "wrate", "grate"
    ]


# ---------- Happy path construction ----------
def test_basic_construction_and_defaults():
    r = Rates(date=d(2024, 1, 1), well="W-001", orate=100.0, wrate=20.0)
    assert r.date == d(2024, 1, 1)
    assert r.well == "W-001"
    assert r.days == 1  # default
    assert r.horizon is None
    assert r.optype == "production"
    assert r.orate == 100.0
    assert r.wrate == 20.0
    assert r.grate is None


def test_all_zero_rates_allowed():
    r = Rates(date=d(2024, 1, 2), well="W-002", orate=0.0, wrate=0.0, grate=0.0)
    assert r.orate == 0.0 and r.wrate == 0.0 and r.grate == 0.0


# ---------- Validation errors ----------
def test_date_must_be_date():
    with pytest.raises(TypeError):
        Rates(date="2024-01-01", well="W-001")  # not a datetime.date

def test_well_must_be_non_empty_string():
    with pytest.raises(ValueError):
        Rates(date=d(2024, 1, 1), well="")

def test_days_must_be_positive_if_provided():
    with pytest.raises(ValueError):
        Rates(date=d(2024, 1, 1), well="W-001", days=0)

def test_negative_rates_raise():
    with pytest.raises(ValueError):
        Rates(date=d(2024, 1, 1), well="W-001", orate=-1.0)
    with pytest.raises(ValueError):
        Rates(date=d(2024, 1, 1), well="W-001", wrate=-0.1)
    with pytest.raises(ValueError):
        Rates(date=d(2024, 1, 1), well="W-001", grate=-5.0)

def test_invalid_optype_raises():
    with pytest.raises(ValueError):
        Rates(date=d(2024, 1, 1), well="W-001", optype="anything")


# ---------- Convenience: totals ----------
def test_total_liquid_none_cases():
    r1 = Rates(date=d(2024, 1, 1), well="W-001")  # both None
    assert r1.total_liquid() is None
    r2 = Rates(date=d(2024, 1, 1), well="W-001", orate=10.0)  # water None
    assert r2.total_liquid() == 10.0
    r3 = Rates(date=d(2024, 1, 1), well="W-001", wrate=5.0)   # oil None
    assert r3.total_liquid() == 5.0

def test_total_liquid_sum():
    r = Rates(date=d(2024, 1, 1), well="W-001", orate=100.0, wrate=40.0)
    assert r.total_liquid() == 140.0


# ---------- Metadata & export ----------
def test_metadata_set_get_and_to_dict_includes_iso_and_metadata():
    r = Rates(date=d(2024, 1, 3), well="W-003", orate=12.3, wrate=4.5, grate=100.0)
    r.set_metadata(source="daily_report", quality="approved")
    assert r.get_metadata("source") == "daily_report"
    assert r.get_metadata("missing", default="none") == "none"

    out = r.to_dict()
    # ISO date string
    assert out["date"] == "2024-01-03"
    # base fields
    assert out["well"] == "W-003"
    assert out["orate"] == 12.3 and out["wrate"] == 4.5 and out["grate"] == 100.0
    # metadata merged
    assert out["source"] == "daily_report"
    assert out["quality"] == "approved"

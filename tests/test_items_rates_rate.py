# test_rate.py
import datetime as dt
import pytest

# ⬇️ UPDATE THIS IMPORT to match your package layout
# e.g., from mypkg.rate import Rate
from wellx.items import Rate

# ---------- construction & defaults

def test_valid_init_with_defaults():
    r = Rate(well="A-12", date=dt.date(2025, 8, 17))
    assert r.well == "A-12"
    assert r.days == 0
    assert r.horizon is None
    assert r.otype == "production"
    assert r.choke is None
    assert r.orate == 0.0
    assert r.wrate == 0.0
    assert r.grate == 0.0
    # metadata-driven units (no overrides yet)
    assert r.get_unit("orate") == "STB/d"
    assert r.get_unit("wrate") == "STB/d"
    assert r.get_unit("grate") == "MSCF/d"


def test_none_rates_are_normalized_to_zero():
    r = Rate(
        well="B-01",
        date=dt.date(2025, 1, 1),
        orate=None, wrate=None, grate=None,  # type: ignore[arg-type]
    )
    assert r.orate == 0.0
    assert r.wrate == 0.0
    assert r.grate == 0.0


# ---------- invariants & validation

@pytest.mark.parametrize("bad", ["", "   "])
def test_invalid_well_raises(bad):
    with pytest.raises(ValueError, match="well must be a non-empty string"):
        Rate(well=bad, date=dt.date(2025, 8, 17))


def test_invalid_date_type_raises():
    with pytest.raises(TypeError, match="date must be a datetime\\.date"):
        Rate(well="A-12", date="2025-08-17")  # type: ignore[arg-type]


def test_invalid_otype_raises():
    with pytest.raises(ValueError, match="otype must be 'production' or 'injection'"):
        Rate(well="A-12", date=dt.date(2025, 8, 17), otype="test")  # type: ignore[arg-type]


def test_negative_days_raises():
    with pytest.raises(ValueError, match="days must be >= 0"):
        Rate(well="A-12", date=dt.date(2025, 8, 17), days=-1)


@pytest.mark.parametrize("field_name", ["orate", "wrate", "grate"])
def test_negative_rate_raises(field_name):
    kwargs = dict(well="A-12", date=dt.date(2025, 8, 17), orate=0.0, wrate=0.0, grate=0.0)
    kwargs[field_name] = -0.1
    with pytest.raises(ValueError, match=f"{field_name} must be >= 0"):
        Rate(**kwargs)


def test_negative_choke_raises():
    with pytest.raises(ValueError, match="choke must be >= 0"):
        Rate(well="A-12", date=dt.date(2025, 8, 17), choke=-1.0)


# ---------- convenience properties

def test_lrate_adds_oil_and_water():
    r = Rate(well="A-12", date=dt.date(2025, 8, 17), orate=100.0, wrate=25.0, grate=5.0)
    assert r.lrate == 125.0


def test_shutin_true_when_all_rates_zero():
    r = Rate(well="A-12", date=dt.date(2025, 8, 17), orate=0.0, wrate=0.0, grate=0.0, days=10)
    assert r.shutin is True


def test_shutin_true_when_days_zero_even_if_rates_nonzero():
    r = Rate(well="A-12", date=dt.date(2025, 8, 17), orate=10.0, wrate=0.0, grate=0.0, days=0)
    assert r.shutin is True


def test_shutin_false_when_has_rates_and_days_positive():
    r = Rate(well="A-12", date=dt.date(2025, 8, 17), orate=10.0, wrate=5.0, grate=0.0, days=1)
    assert r.shutin is False


# ---------- unit metadata access & overrides

def test_get_unit_returns_metadata_default():
    r = Rate(well="A-12", date=dt.date(2025, 8, 17))
    assert r.get_unit("orate") == "STB/d"
    assert r.get_unit("wrate") == "STB/d"
    assert r.get_unit("grate") == "MSCF/d"


def test_set_unit_overrides_take_precedence():
    r = Rate(well="A-12", date=dt.date(2025, 8, 17))
    r.set_unit(orate="m3/d", grate="Sm3/d")
    assert r.get_unit("orate") == "m3/d"
    assert r.get_unit("grate") == "Sm3/d"
    # Unchanged field still uses metadata default
    assert r.get_unit("wrate") == "STB/d"


def test_get_unit_unknown_field_raises():
    r = Rate(well="A-12", date=dt.date(2025, 8, 17))
    with pytest.raises(AttributeError, match="No field named 'xyz'"):
        r.get_unit("xyz")


def test_set_unit_unknown_field_raises():
    r = Rate(well="A-12", date=dt.date(2025, 8, 17))
    with pytest.raises(AttributeError, match="No field named 'xyz'"):
        r.set_unit(xyz="m3/d")  # type: ignore[call-arg]


# ---------- fields() helper

def test_fields_returns_stable_field_names_in_order():
    names = Rate.fields()
    # Must contain all declared dataclass fields in their definition order
    # (including private one `_unit_override`)
    expected_subset = [
        "well", "date", "days", "horizon", "otype", "choke",
        "orate", "wrate", "grate",
    ]
    # Maintain order for the public portion at least up to grate
    assert names[:9] == expected_subset[:9]
    # And ensure every expected name is present
    for n in expected_subset:
        assert n in names

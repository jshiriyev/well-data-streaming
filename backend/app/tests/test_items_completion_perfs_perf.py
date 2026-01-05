import datetime as dt
import pytest
from dataclasses import fields as dc_fields

from wellx.items.completion import PerfInterval, Perf

def test_init_defaults_and_normalization():
    # base defaults to top; guntype uppercased; date can be None
    p = Perf(well="G-01", top=1234.5, base=None, date=None, guntype="  hpx  ")
    assert p.top == pytest.approx(1234.5)
    assert p.base == pytest.approx(1234.5)          # default equals top
    assert p.guntype == "HPX"                       # normalized upper
    assert p.date is None

    # explicit base kept; stringy inputs cast to float
    q = Perf(well="G-02", top="1000", base="1025.5")
    assert isinstance(q.top, float) and isinstance(q.base, float)
    assert q.top == pytest.approx(1000.0)
    assert q.base == pytest.approx(1025.5)


@pytest.mark.parametrize("bad", ["", "   ", None])
def test_invalid_well_raises(bad):
    with pytest.raises(ValueError):
        Perf(well=bad, top=1000.0)


def test_invalid_date_type_raises():
    with pytest.raises(TypeError):
        Perf(well="A-1", top=1000.0, date="2024-01-01")  # not a datetime.date


def test_guntype_none_is_preserved():
    p = Perf(well="X", top=10.0, guntype=None)
    assert p.guntype is None


def test_length_midpoint_contains_overlaps():
    p = Perf(well="A", top=1500.0, base=1512.0)
    # These properties/methods delegate to PerfInterval
    assert p.length == pytest.approx(12.0)
    assert p.midpoint == pytest.approx((1500.0 + 1512.0) / 2.0)

    assert p.contains(1500.0) is True
    assert p.contains(1512.0) is True
    assert p.contains(1499.9) is False
    assert p.contains(1512.1) is False

    q = Perf(well="A", top=1512.0, base=1520.0)
    r = Perf(well="A", top=1520.1, base=1530.0)
    assert p.overlaps(q) is True        # closed interval overlap at 1512
    assert p.overlaps(r) is False


def test_sort_key_and_to_dict():
    d = dt.date(2023, 7, 1)
    p = Perf(well="B", top=900.0, base=925.0, date=d, horizon="D2", guntype="HPX")
    assert p.sort_key() == ("B", 900.0, 925.0)

    out = p.to_dict()
    assert out["well"] == "B"
    assert out["top"] == 900.0 and out["base"] == 925.0
    assert out["date"] == "2023-07-01"       # ISO-8601
    assert out["horizon"] == "D2"
    assert out["guntype"] == "HPX"

def test_fields_excludes_non_init_and_order():
    # fields() should list only init=True fields in stable order
    expected = ["well", "top", "base", "date", "horizon", "guntype"]
    assert Perf.fields() == expected

    # Double-check _unit_override is non-init and excluded
    init_names = [f.name for f in dc_fields(Perf) if f.init]
    assert "_unit_override" not in init_names


def test_get_unit_metadata_defaults():
    p = Perf(well="C", top=100.0, base=120.0)
    # Metadata on the class for top/base is "m"
    assert p.get_unit("top") == "m"
    assert p.get_unit("base") == "m"

    # Fields without unit metadata return None
    assert p.get_unit("well") is None
    assert p.get_unit("horizon") is None
    assert p.get_unit("guntype") is None
    assert p.get_unit("date") is None


def test_get_unit_unknown_field_raises():
    p = Perf(well="C", top=100.0)
    with pytest.raises(AttributeError):
        p.get_unit("does_not_exist")


def test_set_unit_override_and_lookup_order():
    p = Perf(well="D", top=10.0, base=20.0)
    # override should take precedence over class metadata
    p.set_unit(top="ft", base="ft", horizon="code")
    assert p.get_unit("top") == "ft"
    assert p.get_unit("base") == "ft"
    assert p.get_unit("horizon") == "code"
    # unaffected field without override remains None
    assert p.get_unit("well") is None


def test_set_unit_rejects_unknown_field():
    p = Perf(well="E", top=0.0)
    with pytest.raises(AttributeError):
        p.set_unit(not_a_field="m")


def test_unit_override_is_per_instance_and_not_class_level():
    p1 = Perf(well="F1", top=1.0, base=2.0)
    p2 = Perf(well="F2", top=1.0, base=2.0)

    # Override only on p1
    p1.set_unit(top="ft")
    assert p1.get_unit("top") == "ft"
    assert p2.get_unit("top") == "m"          # still default

    # Class metadata should remain unchanged
    top_field = next(f for f in dc_fields(Perf) if f.name == "top")
    assert top_field.metadata.get("unit") == "m"


def test_date_none_vs_valid_serialization_and_validation():
    p_none = Perf(well="G", top=100.0, date=None)
    assert p_none.to_dict()["date"] is None

    d = dt.date(2025, 1, 31)
    p_ok = Perf(well="G", top=100.0, date=d)
    assert p_ok.to_dict()["date"] == "2025-01-31"

import datetime as dt

import pytest

from wellx.items.completion import Interval, Perf

# --------------------------- construction & normalization ---------------------------

@pytest.mark.parametrize(
    "interval_in, expected",
    [
        ((1005.0, 1092.0), Interval(1005.0, 1092.0)),  # tuple
        ([1005.0, 1092.0], Interval(1005.0, 1092.0)),  # list
        ("1005-1092",       Interval(1005.0, 1092.0)),  # string
        (Interval(1005.0, 1092.0), Interval(1005.0, 1092.0)),  # Interval
    ],
)
def test_interval_normalization(interval_in, expected):
    p = Perf(well="G-12", interval=interval_in)
    assert isinstance(p.interval, Interval)
    assert p.interval == expected


def test_invalid_well_raises():
    with pytest.raises(ValueError, match="well must be a non-empty string"):
        Perf(well="  ", interval=(1000.0, 1010.0))


def test_unsupported_interval_type_raises():
    with pytest.raises(TypeError, match="Unsupported interval type"):
        Perf(well="G-12", interval=12345)  # type: ignore[arg-type]


# --------------------------- optional fields & defaults ---------------------------

def test_optional_fields_defaults():
    p = Perf(well="G-12", interval=(1005.0, 1092.0))
    assert p.date is None
    assert p.horizon is None
    assert p.guntype is None


def test_optional_fields_settable():
    d = dt.date(2025, 8, 17)
    p = Perf(
        well="G-12",
        interval=(1005.0, 1092.0),
        date=d,
        horizon="Perma",
        guntype="TCP",
    )
    assert p.date == d
    assert p.horizon == "Perma"
    assert p.guntype == "TCP"


# --------------------------- convenience API ---------------------------

def test_length_forwards_to_interval_length():
    p = Perf(well="G-12", interval=(1005.0, 1092.0))
    assert p.length == 87.0


def test_sort_key_returns_expected_tuple():
    p = Perf(well="G-12", interval=(1005.0, 1092.0))
    assert p.sort_key() == ("G-12", 1005.0, 1092.0)


def test_fields_returns_declared_names_in_order():
    names = Perf.fields()
    # Expected order as declared in the dataclass
    assert names[:5] == ["well", "interval", "date", "horizon", "guntype"]
    # All must be present
    for n in ["well", "interval", "date", "horizon", "guntype"]:
        assert n in names

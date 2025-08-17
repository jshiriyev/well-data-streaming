import pytest
from dataclasses import FrozenInstanceError

from wellx.items.completion import PerfInterval


# ------------------------ construction & validation -------------------------

def test_valid_init_and_properties():
    iv = PerfInterval(1005.0, 1092.0)
    assert iv.top == 1005.0
    assert iv.base == 1092.0
    assert iv.length == 87.0
    assert iv.contains(1005.0) is True      # inclusive
    assert iv.contains(1092.0) is True      # inclusive
    assert iv.contains(1004.99) is False
    assert iv.contains(1092.01) is False

def test_zero_length_interval_allowed():
    iv = PerfInterval(1500.0, 1500.0)
    assert iv.length == 0.0
    assert iv.contains(1500.0)

def test_invalid_when_base_less_than_top():
    with pytest.raises(ValueError, match=r"base .* must be >= top"):
        PerfInterval(1200.0, 1199.9)

def test_frozen_dataclass_is_immutable():
    iv = PerfInterval(1000.0, 1001.0)
    with pytest.raises(FrozenInstanceError):
        iv.top = 999.0  # type: ignore[misc]


# ----------------------------- ordering & equality --------------------------

def test_ordering_by_top_then_base():
    a = PerfInterval(1000.0, 1010.0)
    b = PerfInterval( 995.0, 1005.0)
    c = PerfInterval(1000.0, 1009.0)
    sorted_ivs = sorted([a, b, c])
    assert sorted_ivs == [b, c, a]  # order=True (top, then base)


# ----------------------------- overlaps logic -------------------------------

@pytest.mark.parametrize(
    "iv1, iv2, expected",
    [
        (PerfInterval(1000, 1010), PerfInterval(1005, 1015), True),   # overlap
        (PerfInterval(1000, 1010), PerfInterval(1010, 1020), True),   # touching at boundary counts as overlap
        (PerfInterval(1000, 1010), PerfInterval(1011, 1020), False),  # separated
        (PerfInterval(1000, 1000), PerfInterval(1000, 1000), True),   # identical zero-length
    ],
)
def test_overlaps(iv1, iv2, expected):
    assert iv1.overlaps(iv2) is expected
    assert iv2.overlaps(iv1) is expected  # symmetric


# ----------------------------- string & list I/O ----------------------------

def test_to_str_default_and_template():
    iv = PerfInterval(1005.0, 1092.0)
    assert iv.to_str() == "1005.0-1092.0"
    s = iv.to_str(template="MD {top:.1f}–{base:.1f} m")
    assert s == "MD 1005.0–1092.0 m"

def test_to_list():
    iv = PerfInterval(123.0, 456.0)
    assert iv.to_list() == [123.0, 456.0]

def test_from_str_default_delims():
    iv = PerfInterval.from_str("1005-1092")
    assert iv == PerfInterval(1005.0, 1092.0)

def test_from_str_custom_delimiter_and_decimal():
    iv = PerfInterval.from_str("1005,5|1092,25", delimiter="|", decsep=",")
    assert iv == PerfInterval(1005.5, 1092.25)

def test_from_str_bad_format_raises():
    with pytest.raises(ValueError, match=r"Expected 'top.*base'"):
        PerfInterval.from_str("1005")  # missing second bound
    with pytest.raises(ValueError):
        PerfInterval.from_str("a-b")   # not parseable as floats


# ------------------------------ from_any ------------------------------------

def test_from_any_accepts_interval_tuple_list_and_str():
    base_iv = PerfInterval(1000.0, 1010.0)
    assert PerfInterval.from_any(base_iv) == base_iv

    assert PerfInterval.from_any((1000, 1010)) == base_iv
    assert PerfInterval.from_any([1000, 1010]) == base_iv
    assert PerfInterval.from_any("1000-1010") == base_iv

def test_from_any_tuple_wrong_length_raises():
    with pytest.raises(ValueError, match="must have exactly two numbers"):
        PerfInterval.from_any((1000.0,))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must have exactly two numbers"):
        PerfInterval.from_any((1000.0, 1010.0, 1020.0))  # type: ignore[arg-type]

def test_from_any_unsupported_type_raises():
    with pytest.raises(TypeError, match="Unsupported interval type"):
        PerfInterval.from_any(12345)  # type: ignore[arg-type]

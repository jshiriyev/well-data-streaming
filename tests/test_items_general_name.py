# test_name.py
# Run with: pytest -q

import re
import pytest

# ---- Import your class here ----
from wellx.items import Name


# ---------- Fixtures ----------
@pytest.fixture
def w():
    # Example from your prompt
    return Name("GUN-38")

@pytest.fixture
def w_padded():
    return Name("WELL-007")

@pytest.fixture
def w_non_numeric():
    return Name("ALPHA")


# ---------- Representation ----------
def test_str_and_repr(w):
    assert str(w) == "GUN-38"
    assert "Name(name='GUN-38')" in repr(w)


# ---------- Normalization ----------
@pytest.mark.parametrize(
    "name, sep, expected",
    [
        (" gun-38 ", " ", "GUN-38"),
        ("GUN   38", "-", "GUN-38"),   # spaces collapse then replaced by default sep (space -> '-') inside slug test
    ],
)
def test_canonical(name, sep, expected):
    # canonical collapses whitespace and uppercases; keeps spaces by default
    n = Name(name)
    assert n.canonical(sep=sep) == expected  # canonical uses spaces


@pytest.mark.parametrize(
    "name, sep, expected",
    [
        (" gun  38 ", "-", "GUN-38"),
        ("Well  1/A", "-", "WELL-1A"),       # removes non A-Z0-9 and sep, collapses repeats
        ("Well__1__A", "_", "WELL_1_A"),     # custom separator kept
    ],
)
def test_slug(name, sep, expected):
    n = Name(name)
    assert n.slug(sep=sep) == expected


# ---------- Parsing ----------
def test_split_default_regex(w):
    prefix, idx, suffix = w.split()
    assert prefix == "GUN-"
    assert idx == 38
    assert suffix == ""

def test_split_no_number_returns_name(w_non_numeric):
    prefix, idx, suffix = w_non_numeric.split()
    assert prefix == "ALPHA"
    assert idx is None
    assert suffix == ""

def test_split_custom_regex():
    n = Name("PLAT-12/SLOT-03A")
    # Only grab the first number using a custom regex similar to the default
    custom = re.compile(r"(?P<prefix>.*?)(?P<index>\d+)(?P<suffix>.*)$")
    prefix, idx, suffix = n.split(regex=custom)
    assert prefix == "PLAT-"
    assert idx == 12
    assert suffix == "/SLOT-03A"


def test_extract_first_digits(w):
    assert w.extract(r"\d+") == "38"

def test_extract_group_capture():
    n = Name("PAD-B/04X")
    assert n.extract(r"PAD-([A-Z])/\d+", group=1) == "B"

def test_extract_default_when_no_match(w):
    assert w.extract(r"XYZ", default="Not found") == "Not found"

def test_extract_none_when_no_default(w):
    assert w.extract(r"XYZ") is None


# ---------- Formatting / generation ----------
def test_apply_default_template():
    assert Name.apply(42) == "Well-42"

def test_apply_positional_template():
    assert Name.apply(42, template="GUN-{}") == "GUN-42"

def test_apply_named_template_with_padding():
    assert Name.apply(42, template="Well-{index:03d}") == "Well-042"

def test_apply_template_without_placeholder_returns_string_unchanged():
    # Current implementation passes extra kwargs to format(); unused are ignored by str.format.
    assert Name.apply(99, template="Well") == "Well"

def test_apply_invalid_template_raises_valueerror():
    # An actually invalid format string should raise ValueError
    with pytest.raises(ValueError):
        Name.apply(5, template="Well-{index:0z3d}")  # invalid format spec

def test_from_components_basic():
    n = Name.from_components(prefix="GUN-", index=42)
    assert isinstance(n, Name)
    assert str(n) == "GUN-42"

def test_from_components_with_padding():
    n = Name.from_components(prefix="GUN-", index=7, pad=4)
    assert str(n) == "GUN-0007"

def test_from_components_without_index_builds_prefix_suffix_only():
    n = Name.from_components(prefix="WELL-", index=None, suffix="A")
    assert str(n) == "WELL-A"


def test_with_index_padding_adds_padding(w):
    padded = w.with_index_padding(4)
    assert isinstance(padded, Name)
    assert str(padded) == "GUN-0038"

def test_with_index_padding_no_number_returns_self(w_non_numeric):
    same = w_non_numeric.with_index_padding(3)
    assert same is w_non_numeric  # should return the same object (class is frozen)


# ---------- Validation ----------
def test_matches_true(w):
    assert w.matches(r"^GUN-\d+$")

def test_matches_false(w):
    assert not w.matches(r"^WELL-\d+$")

def test_matches_with_flags():
    n = Name("pad-b/04")
    assert n.matches(r"^PAD-B/\d+$", flags=re.IGNORECASE)


# ---------- (De)serialization ----------
def test_to_dict(w):
    d = w.to_dict()
    assert d == {"name": "GUN-38", "prefix": "GUN-", "index": 38, "suffix": ""}

def test_from_dict_full():
    n = Name.from_dict({"prefix": "GUN-", "index": 42, "suffix": ""})
    assert isinstance(n, Name)
    assert str(n) == "GUN-42"

def test_from_dict_name_wins():
    n = Name.from_dict({"name": "GUN-99", "prefix": "IGNORED-", "index": 1, "suffix": "X"})
    assert str(n) == "GUN-99"

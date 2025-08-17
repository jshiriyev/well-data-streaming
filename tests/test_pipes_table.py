# test_table.py
import pandas as pd
import pytest

# ⬇️ Update this import to match your package layout, e.g.:
# from mypkg.table import Table
from wellx.pipes import Table


# --------------------------------- Fixtures ---------------------------------

@pytest.fixture
def base_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "tarix": [1, 2, 3, 4],  # int
            "qoil": [10.0, 11.5, 9.7, 12.0],  # float
            "name": ["A", "B", "C", "A"],  # object
            "when": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]),
        }
    )

@pytest.fixture
def tiein() -> dict:
    return {"date": "tarix", "orate": "qoil"}

@pytest.fixture
def tf(base_df, tiein) -> Table:
    return Table(base_df, tiein=tiein)


# ------------------------------- Attribute access ----------------------------

def test_tiein_attribute_returns_mapped_column(tf: Table, base_df: pd.DataFrame):
    s = tf.date
    assert isinstance(s, pd.Series)
    assert s.name == "tarix"
    pd.testing.assert_series_equal(s, base_df["tarix"])

def test_attribute_mapped_but_missing_column_raises(base_df):
    t = Table(base_df[["qoil"]].copy(), tiein={"orate": "qoil", "date": "tarix"})
    with pytest.raises(AttributeError, match=r"tied to column 'tarix'"):
        _ = t.date

def test_fallback_attribute_to_existing_column(tf: Table):
    s = tf.qoil  # not in tiein; should still work
    pd.testing.assert_series_equal(s, tf["qoil"])

def test_unknown_attribute_raises(tf: Table):
    with pytest.raises(AttributeError):
        _ = tf.not_a_real_attr


# ----------------------------- __getitem__ behavior --------------------------

def test_getitem_single_column_returns_series(tf: Table):
    out = tf["qoil"]
    assert isinstance(out, pd.Series)
    assert not isinstance(out, Table)

def test_getitem_multiple_columns_returns_table_and_copies_tiein(tf: Table):
    out = tf[["qoil", "tarix"]]
    assert isinstance(out, Table)
    assert hasattr(out, "_tiein")
    assert out._tiein == tf._tiein
    assert out._tiein is not tf._tiein  # ensure copy, not same object

def test_constructor_chain_preserves_table_subclass(tf: Table):
    sub1 = tf[["qoil"]]
    assert isinstance(sub1, Table)
    sub2 = sub1[["qoil"]]
    assert isinstance(sub2, Table)

def test_child_tiein_mutation_does_not_affect_parent(tf: Table):
    child = tf[["tarix", "qoil"]]
    child._tiein["date"] = "SOMETHING_ELSE"
    assert tf._tiein["date"] == "tarix"
    assert child._tiein["date"] == "SOMETHING_ELSE"


# ----------------------------- dtype-based properties ------------------------

def test_datetimes_returns_datetime_columns_as_set(tf: Table):
    # utils.heads uses set() internally → order not guaranteed; compare as sets
    out = set(tf.datetimes)
    assert out == {"when"}

def test_numbers_returns_numeric_columns_as_set(tf: Table):
    out = set(tf.numbers)
    # 'number' should include ints and floats (not objects)
    assert out == {"tarix", "qoil"}

def test_nominals_excludes_numbers_and_datetimes(tf: Table):
    out = set(tf.nominals)
    assert out == {"name"}


# ----------------------------- Construction / docstring ----------------------

def test_init_from_dataframe_keeps_data(base_df, tiein):
    t = Table(base_df, tiein=tiein)
    pd.testing.assert_frame_equal(pd.DataFrame(t), base_df)

def test_docstring_example_equivalence():
    df = pd.DataFrame({"tarix": [1, 2, 3], "qoil": [10.0, 11.5, 9.7]})
    tf = Table(df, tiein={"date": "tarix", "orate": "qoil"})
    assert tf.date.tolist() == [1, 2, 3]
    assert pytest.approx(tf.orate.mean()) == 10.4

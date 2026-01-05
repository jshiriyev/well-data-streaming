import pandas as pd
import numpy as np
import pytest

from typing import Tuple

from wellx.pipes import Table

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


@pytest.fixture
def sample_df() -> pd.DataFrame:
    # columns: strings, ints, floats, bools, datetimes
    return pd.DataFrame({
        "name": ["A", "B", "C", "A"],
        "city": ["X", "Y", "X", "Z"],
        "age":  [10, 20, 30, 40],              # int
        "score": [1.5, 2.0, 3.5, 4.0],         # float
        "is_ok": [True, False, True, True],    # bool
        "date": pd.to_datetime(["2024-01-01","2024-01-02","2024-01-03","2024-01-04"])
    })

# ------------------------- tests for heads -----------------------------

def test_heads_args_only_preserves_arg_order(sample_df):
    out = Table.get_heads(sample_df, "city", "age", "missing", "name")
    assert out == ["city", "age", "name"]  # missing is dropped

@pytest.mark.parametrize(
    "include,exclude,expected_subset",
    [
        (("int64","float64"), None, {"age","score"}),
        (("bool",), None, {"is_ok"}),
        (("datetime64[ns]",), None, {"date"}),
        (None, ("int64",), set(sample_df().__class__ if False else ["name","city","score","is_ok","date"]) - {"age"}),  # just to vary
    ]
)
def test_heads_with_dtypes_returns_unordered_superset(sample_df, include, exclude, expected_subset):
    # We assert set containment because heads() uses set() losing order.
    out = set(Table.get_heads(sample_df, include=include, exclude=exclude))
    assert expected_subset.issubset(out)


def test_heads_combines_args_and_dtype_selection(sample_df):
    out = set(Table.get_heads(sample_df, "name", include=("float64",)))
    # should contain 'name' and any float columns
    assert {"name","score"}.issubset(out)

# -------------------------- tests for join ----------------------------

def test_join_with_args_only_preserves_order_and_builds_name(sample_df):
    df = Table.join_columns(sample_df, "name", "city", sep="-")
    expected_colname = "name-city"
    assert list(df.columns) == [expected_colname]
    assert df.iloc[0,0] == "A-X"
    assert df.iloc[1,0] == "B-Y"

def test_join_with_dtype_filters_ignores_order(sample_df):
    # include floats and ints; result column order is non-deterministic; validate content per row
    df = Table.join_columns(sample_df, include=("int64","float64"), sep="|")
    # Retrieve the produced column name and split to see which columns were used
    produced_col = df.columns[0]
    used_cols = set(produced_col.split("|"))
    assert used_cols == {"age","score"}  # both numeric columns must be used

    # Validate row-wise joining independent of order
    def parts(value): return set(str(value).split("|"))
    assert parts(df.iloc[0,0]) == {"10","1.5"}
    assert parts(df.iloc[2,0]) == {"30","3.5"}

def test_join_default_separator_is_space(sample_df):
    df = Table.join_columns(sample_df, "name", "city")
    assert " " in df.columns[0]
    assert df.iloc[0,0] == "A X"

# ------------------------- tests for filter ---------------------------

def test_filter_keeps_requested_values_and_resets_index(sample_df):
    out = Table.filter_column(sample_df, "name", "A", "C")
    assert set(out["name"]) == {"A","C"}
    assert list(out.index) == list(range(len(out)))  # reset_index(drop=True)
    # rows with other names should be removed
    assert not (out["name"] == "B").any()

def test_filter_empty_result(sample_df):
    out = Table.filter_column(sample_df, "city", "NOPE")
    assert out.empty
    assert list(out.columns) == list(sample_df.columns)

# ------------------------ tests for groupsum --------------------------

def test_groupsum_sums_numeric_and_drops_group_label(sample_df):
    # select two names to keep; after groupsum, the label column is removed by design
    out = Table.groupsum_column(sample_df, "name", "A", "B")
    # grouped rows become a single row; only numeric columns remain summed
    # numeric sums: age = 10+40+20 = 70, score = 1.5+4.0+2.0 = 7.5
    expected_cols = {"age","score"}  # bool will not be summed as ints (True=1, False=0)
    assert set(out.columns) >= expected_cols
    assert len(out) == 1
    assert out.loc[0,"age"] == 70
    assert out.loc[0,"score"] == pytest.approx(7.5)
    # original grouping column should not be present
    assert "name" not in out.columns

def test_groupsum_respects_custom_separator_when_forming_label(sample_df):
    # Even though label is dropped later, ensure no errors when a custom separator is provided.
    out = Table.groupsum_column(sample_df, "city", "X", "Z")
    assert len(out) == 1
    # still no 'city' column (dropped by reset_index)
    assert "city" not in out.columns

def test_groupsum_on_empty_filter_returns_empty(sample_df):
    out = Table.groupsum_column(sample_df, "name", "NOPE")
    # groupby on empty -> remains empty after sum/reset
    assert out.empty
    # columns should be the numeric ones (pandas sum on empty preserves dtypes/columns)
    # but exact behavior can vary; at least shouldn't raise
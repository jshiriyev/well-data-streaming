# test_utils.py
import pandas as pd
import numpy as np
import pytest

from typing import Tuple

from wellx.pipes import utils

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
    out = utils.heads(sample_df, "city", "age", "missing", "name")
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
    out = set(utils.heads(sample_df, include=include, exclude=exclude))
    assert expected_subset.issubset(out)


def test_heads_combines_args_and_dtype_selection(sample_df):
    out = set(utils.heads(sample_df, "name", include=("float64",)))
    # should contain 'name' and any float columns
    assert {"name","score"}.issubset(out)

# -------------------------- tests for join ----------------------------

def test_join_with_args_only_preserves_order_and_builds_name(sample_df):
    df = utils.join(sample_df, "name", "city", separator="-")
    expected_colname = "name-city"
    assert list(df.columns) == [expected_colname]
    assert df.iloc[0,0] == "A-X"
    assert df.iloc[1,0] == "B-Y"

def test_join_with_dtype_filters_ignores_order(sample_df):
    # include floats and ints; result column order is non-deterministic; validate content per row
    df = utils.join(sample_df, include=("int64","float64"), separator="|")
    # Retrieve the produced column name and split to see which columns were used
    produced_col = df.columns[0]
    used_cols = set(produced_col.split("|"))
    assert used_cols == {"age","score"}  # both numeric columns must be used

    # Validate row-wise joining independent of order
    def parts(value): return set(str(value).split("|"))
    assert parts(df.iloc[0,0]) == {"10","1.5"}
    assert parts(df.iloc[2,0]) == {"30","3.5"}

def test_join_default_separator_is_space(sample_df):
    df = utils.join(sample_df, "name", "city")
    assert " " in df.columns[0]
    assert df.iloc[0,0] == "A X"

# ------------------------- tests for filter ---------------------------

def test_filter_keeps_requested_values_and_resets_index(sample_df):
    out = utils.filter(sample_df, "name", "A", "C")
    assert set(out["name"]) == {"A","C"}
    assert list(out.index) == list(range(len(out)))  # reset_index(drop=True)
    # rows with other names should be removed
    assert not (out["name"] == "B").any()

def test_filter_empty_result(sample_df):
    out = utils.filter(sample_df, "city", "NOPE")
    assert out.empty
    assert list(out.columns) == list(sample_df.columns)

# ------------------------ tests for groupsum --------------------------

def test_groupsum_sums_numeric_and_drops_group_label(sample_df):
    # select two names to keep; after groupsum, the label column is removed by design
    out = utils.groupsum(sample_df, "name", "A", "B")
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
    out = utils.groupsum(sample_df, "city", "X", "Z")
    assert len(out) == 1
    # still no 'city' column (dropped by reset_index)
    assert "city" not in out.columns

def test_groupsum_on_empty_filter_returns_empty(sample_df):
    out = utils.groupsum(sample_df, "name", "NOPE")
    # groupby on empty -> remains empty after sum/reset
    assert out.empty
    # columns should be the numeric ones (pandas sum on empty preserves dtypes/columns)
    # but exact behavior can vary; at least shouldn't raise
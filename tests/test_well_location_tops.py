# test_tops.py
# Run: pytest -q
import numpy as np
import pytest

from wellx.items import Tops

def arr(*xs):
    return np.asarray(xs, dtype=float)


# ---------- Construction & schema ----------
def test_fields_schema():
    assert Tops.fields() == ["formation", "depth", "facecolor"]

def test_basic_construction_orders_by_depth_and_keeps_colors():
    tops = Tops(
        formation=["B", "A", "C"],
        depth=[2000, 1000, 2500],
        facecolor={"A": "red", "C": "#00FF00"}
    )
    assert tops.formations == ["A", "B", "C"]
    assert np.allclose(tops.depths, arr(1000, 2000, 2500))
    # color map preserves known keys; missing gets None
    cmap = tops.facecolor_map()
    assert cmap["A"] == "red"
    assert cmap["B"] is None
    assert cmap["C"] == "#00FF00"

def test_len_contains_index_getitem():
    tops = Tops(["Shale", "Sandstone"], [1000, 1500])
    assert len(tops) == 2
    assert "Shale" in tops and "Chalk" not in tops
    assert tops.index("Sandstone") == 1
    assert tops["Shale"] == 1000.0  # __getitem__ delegates to get_top


# ---------- Validation errors ----------
def test_length_mismatch_raises():
    with pytest.raises(ValueError):
        Tops(["A", "B"], [1000])

def test_non_1d_depth_raises():
    with pytest.raises(ValueError):
        Tops(["A", "B"], np.array([[1000, 1500]]))  # 2D

def test_non_finite_or_negative_raises():
    with pytest.raises(ValueError):
        Tops(["A"], [np.nan])
    with pytest.raises(ValueError):
        Tops(["A"], [np.inf])
    with pytest.raises(ValueError):
        Tops(["A"], [-1.0])  # negative MD not allowed

def test_duplicate_names_raises():
    with pytest.raises(ValueError):
        Tops(["A", "A"], [1000, 1500])


# ---------- Lookups & intervals ----------
def test_get_top_and_get_limit_and_intervals():
    tops = Tops(["A", "B", "C"], [1000, 1500, 2000])
    assert tops.get_top("B") == 1500.0
    assert tops.get_limit("A") == (1000.0, 1500.0)
    assert tops.get_limit("C") == (2000.0, None)
    assert tops.intervals() == [
        ("A", 1000.0, 1500.0),
        ("B", 1500.0, 2000.0),
        ("C", 2000.0, None),
    ]

def test_find_at_md_edge_convention():
    tops = Tops(["A", "B", "C"], [1000, 1500, 2000])
    # [top, bottom): inclusive at top, exclusive at bottom
    assert tops.find_at_md(999.9) is None
    assert tops.find_at_md(1000.0) == "A"
    assert tops.find_at_md(1499.999) == "A"
    assert tops.find_at_md(1500.0) == "B"       # exclusive at A's bottom
    assert tops.find_at_md(1999.999) == "B"
    assert tops.find_at_md(2000.0) == "C"
    assert tops.find_at_md(9999.0) == "C"      # deepest is open-ended

def test_find_at_md_with_single_formation():
    tops = Tops(["Only"], [1234.0])
    assert tops.find_at_md(0.0) is None
    assert tops.find_at_md(1234.0) == "Only"
    assert tops.find_at_md(9999.0) == "Only"


# ---------- Mutation: add / remove / rename ----------
def test_add_inserts_in_order_and_sets_color():
    tops = Tops(["A", "C"], [1000, 2000], facecolor={"A": "red"})
    tops.add("B", 1500, facecolor="blue")
    assert tops.formations == ["A", "B", "C"]
    assert np.allclose(tops.depths, arr(1000, 1500, 2000))
    assert tops.get_facecolor("B") == "blue"

def test_add_existing_raises_and_invalid_depth_raises():
    tops = Tops(["A"], [1000])
    with pytest.raises(ValueError):
        tops.add("A", 1200)
    with pytest.raises(ValueError):
        tops.add("B", -5)
    with pytest.raises(ValueError):
        tops.add("B", float("nan"))

def test_remove_and_rename_preserve_depths_and_colors():
    tops = Tops(["A", "B", "C"], [1000, 1500, 2000], facecolor={"B": "gold"})
    tops.rename("B", "Sand")
    assert "B" not in tops and "Sand" in tops
    assert tops.get_facecolor("Sand") == "gold"
    assert tops.get_top("Sand") == 1500.0
    tops.remove("Sand")
    assert "Sand" not in tops
    assert np.allclose(tops.depths, arr(1000, 2000))

def test_rename_to_existing_raises():
    tops = Tops(["A", "B"], [1000, 1500])
    with pytest.raises(ValueError):
        tops.rename("A", "B")


# ---------- Facecolors ----------
def test_merge_facecolors_overrides_known_and_ignores_unknown():
    tops = Tops(["A", "B"], [1000, 1500], facecolor={"A": "red"})
    tops.merge_facecolors({"A": "darkred", "Unknown": "green"})
    cmap = tops.facecolor_map()
    assert cmap["A"] == "darkred"
    assert cmap["B"] is None   # unchanged / still None


# ---------- Convenience I/O ----------
def test_from_mapping_and_to_mapping_roundtrip_ordered():
    mapping = {"B": 2000.0, "A": 1000.0, "C": 2500.0}
    tops = Tops.from_mapping(mapping, facecolor={"A": "red"})
    # Ensure sorted by depth and mapping comes back ordered shallow->deep
    assert tops.formations == ["A", "B", "C"]
    assert tops.to_mapping() == {"A": 1000.0, "B": 2000.0, "C": 2500.0}


# ---------- Error messages / missing formation ----------
def test_index_and_get_top_missing_raises():
    tops = Tops(["A"], [1000])
    with pytest.raises(ValueError):
        tops.index("Nope")
    with pytest.raises(ValueError):
        tops.get_top("Nope")

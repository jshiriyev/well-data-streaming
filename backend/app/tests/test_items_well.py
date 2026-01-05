# test_well.py
# Run: pytest -q
import pytest
import numpy as np

# ⬇️ Adjust this import to match your package structure
# e.g., from wellx.core.well import Well
from wellx import Well


# ---------- Minimal stubs (only what's needed by Well) ----------
class NameStub:
    def __init__(self, name: str):
        self.name = name

class SurveyStub:
    def __init__(self, MD, TVD=None):
        self.MD = np.asarray(MD, dtype=float)
        self.TVD = None if TVD is None else np.asarray(TVD, dtype=float)

class TopsStub:
    def __init__(self, formations, depths):
        self.formations = list(formations)
        self._depths = np.asarray(depths, dtype=float)

    @property
    def depths(self):
        # Well.validate reads depths iterably
        return self._depths

class StatusCodeStub:
    def __init__(self, value: str):
        self.value = value  # mimics real Enum.value

class StatusStub:
    def __init__(self, code_value: str, color_hex="#123456", d=None):
        self.code = StatusCodeStub(code_value)
        self._color = color_hex
        self._d = d or {"code": code_value, "started_at": "2025-01-01T00:00:00+00:00", "ended_at": None}

    def color(self, palette=None):
        return self._color

    def to_dict(self):
        return dict(self._d)

class PerfsStub:
    def __init__(self, intervals=None):
        self.intervals = intervals or []


# ---------- Helpers ----------
def make_well_basic(name="GUN-38"):
    return Well(name=NameStub(name))


# ---------- Construction & identity ----------
def test_construct_minimal_and_name_text_exposes_raw():
    w = make_well_basic("FIELD-01")
    assert w.name_text == "FIELD-01"
    # ensure immutability style: with_* returns a new instance
    w2 = w.with_name("FIELD-02")
    assert w2 is not w and w2.name_text == "FIELD-02" and w.name_text == "FIELD-01"


# ---------- Status helpers ----------
def test_current_status_code_and_color():
    w = make_well_basic()
    assert w.current_status_code() is None
    s = StatusStub("drilling", color_hex="#7c3aed")
    w2 = w.with_status(s)
    assert w2.current_status_code() == "drilling"
    assert w2.status_color() == "#7c3aed"


# ---------- Attach survey / tops / perfs and summarize ----------
def test_with_survey_tops_perfs_and_summary_counts():
    MD = np.array([0, 500, 1000], dtype=float)
    TVD = np.array([0, 450, 900], dtype=float)
    survey = SurveyStub(MD=MD, TVD=TVD)

    tops = TopsStub(formations=["A", "B"], depths=[200.0, 800.0])
    perfs = PerfsStub(intervals=[(1500, 1600), (2000, 2100)])  # not used deeply

    w = make_well_basic().with_survey(survey).with_tops(tops).with_perfs(perfs)
    sm = w.summary()

    assert sm["name"] == "GUN-38"
    assert sm["md_end"] == pytest.approx(1000.0)
    assert sm["tvd_end"] == pytest.approx(900.0)
    assert sm["tops"] == 2
    assert sm["perfs"] == 2
    assert sm["log_files"] == 0


# ---------- Units metadata & LAS handling ----------
def test_with_units_merges_and_add_las_dedup_preserves_order():
    w = make_well_basic().with_units({"MD": "m"}).with_units({"TVD": "m", "oil": "bbl/d"})
    assert w.units == {"MD": "m", "TVD": "m", "oil": "bbl/d"}

    w2 = w.add_log("a.las", "b.las", "a.las", "c.las")
    assert w2.logs == ("a.las", "b.las", "c.las")
    # original unchanged
    assert w.logs == ()

# ---------- Validation ----------
def test_validate_passes_when_tops_within_survey_range():
    survey = SurveyStub(MD=[0, 1000], TVD=[0, 900])
    tops = TopsStub(["A"], [500.0])
    w = make_well_basic().with_survey(survey).with_tops(tops)
    w.validate()  # should not raise

def test_validate_raises_when_top_outside_survey_range():
    survey = SurveyStub(MD=[0, 1000], TVD=[0, 900])
    tops = TopsStub(["A"], [1200.0])  # outside
    w = make_well_basic().with_survey(survey).with_tops(tops)
    with pytest.raises(ValueError):
        w.validate()


# ---------- to_dict / from_dict ----------
def test_to_dict_shallow_includes_light_markers_and_status_dict_when_available():
    s = StatusStub("production", color_hex="#166534", d={"code": "production", "started_at": "2025-01-01T00:00:00+00:00", "ended_at": None})
    survey = SurveyStub(MD=[0, 10], TVD=[0, 9])

    w = make_well_basic().with_status(s).with_survey(survey).add_log("x.las")
    out = w.to_dict(deep=False)

    # name and units present
    assert out["name"] == "GUN-38"
    assert isinstance(out["units"], dict)

    # status uses to_dict() if available
    assert isinstance(out["status"], dict) and out["status"]["code"] == "production"

    # shallow mode uses light markers, not deep nested dicts
    assert out["survey"] == "survey"   # marker
    assert out["tops"] is None
    assert out["perfs"] is None
    assert out["logs"] == ["x.las"]

def test_from_dict_minimal_builds_well_with_name_and_las_only():
    data = {"name": "W-001", "logs": ["a.las", "b.las"], "plt": "PLT-01"}
    w = Well.from_dict(data)
    assert w.name_text == "W-001"
    assert w.logs == ("a.las", "b.las")
    # no status/survey/tops attached
    assert w.current_status_code() is None
    assert w.survey is None and w.tops is None
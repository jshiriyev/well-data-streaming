# test_survey.py
# Run: pytest -q
import numpy as np
import pytest

# Adjust this import to where your class lives
from wellx.items import Survey


# ---------- Utilities ----------
def arr(*xs):
    return np.asarray(xs, dtype=float)


# ---------- Fields / construction ----------
def test_fields_have_expected_names():
    f = Survey.fields()
    for name in ["MD", "TVD", "DX", "DY", "INC", "AZI", "xhead", "yhead", "datum"]:
        assert name in f

def test_from_md_tvd_basic_and_view_section():
    md  = arr(0, 10, 20, 30)
    tvd = arr(0,  9, 19, 28)
    s = Survey.from_md_tvd(md, tvd)
    md2, tvd2 = s.view_section()
    assert np.allclose(md2, md)
    assert np.allclose(tvd2, tvd)

def test_constructor_enforces_md_strictly_increasing():
    with pytest.raises(ValueError):
        Survey.from_md_tvd(arr(0, 10, 10), arr(0, 9, 18))

def test_shape_mismatch_raises():
    with pytest.raises(ValueError):
        Survey(MD=arr(0, 10, 20), TVD=arr(0, 9))  # lengths differ


# ---------- Interpolation ----------
def test_md2tvd_and_tvd2md_roundtrip_within_range():
    md  = arr(0, 10, 20, 30)
    tvd = arr(0,  8, 18, 27)
    s = Survey.from_md_tvd(md, tvd)

    q_md = arr(5, 15, 25)
    got_tvd = s.md2tvd(q_md)
    # Inverse requires TVD strictly increasing (it is)
    back_md = s.tvd2md(got_tvd)
    assert np.allclose(back_md, q_md)

def test_md2tvd_raises_out_of_range():
    s = Survey.from_md_tvd(arr(0, 10, 20), arr(0, 9, 18))
    with pytest.raises(ValueError):
        s.md2tvd(arr(-1, 5))  # -1 is below range
    with pytest.raises(ValueError):
        s.md2tvd(arr(5, 25))  # 25 is above range

def test_tvd2md_requires_increasing_tvd():
    # TVD not strictly increasing -> tvd2md must raise
    s = Survey.from_md_tvd(arr(0, 10, 20), arr(0, 0, 5))  # not strictly increasing
    with pytest.raises(ValueError):
        s.tvd2md(arr(1, 3))


# ---------- Geometry helpers ----------
def test_inc2tvd_vertical_equals_md():
    md = arr(0, 10, 20, 30)
    inc = arr(0, 0, 0, 0)  # vertical
    tvd = Survey.inc2tvd(inc, md)
    assert np.allclose(tvd, md)

def test_off2tvd_no_lateral_equals_md_increment():
    md  = arr(0, 10, 20, 30)
    dx  = arr(0, 0, 0, 0)
    dy  = arr(0, 0, 0, 0)
    tvd = Survey.off2tvd(md, dx, dy)
    assert np.allclose(tvd, md)

def test_off2tvd_handles_large_lateral_without_crash():
    # Construct intervals where lateral is close to MD (valid geometry)
    md = arr(0, 10, 20)
    dx = arr(0,  6, 12)
    dy = arr(0,  6, 12)
    tvd = Survey.off2tvd(md, dx, dy)
    # dTVD = sqrt(dMD^2 - dX^2 - dY^2) -> here sqrt(100 - 36 - 36) = sqrt(28)
    assert np.isfinite(tvd).all()
    assert tvd[0] == 0.0
    assert tvd[-1] > 0.0


# ---------- Minimum curvature & constructors ----------
def test_minimum_curvature_vertical_path():
    md  = arr(0, 10, 20, 30)
    inc = arr(0, 0, 0, 0)
    azi = arr(0, 0, 0, 0)
    dx, dy, tvd = Survey.minimum_curvature(md, inc, azi, xhead=100.0, yhead=200.0, datum=5.0)
    assert np.allclose(dx, 100.0)  # no east movement
    assert np.allclose(dy, 200.0)  # no north movement
    # TVD grows by ~dMD each step
    assert np.allclose(tvd, arr(5.0, 15.0, 25.0, 35.0))

def test_from_md_inc_azi_constructor_and_views():
    md  = arr(0, 10, 20)
    inc = arr(0, 30, 30)
    azi = arr(0, 90, 90)  # turning east
    s = Survey.from_md_inc_azi(md, inc, azi, xhead=0.0, yhead=0.0, datum=0.0)
    # Has DX/DY/TVD available for plan and section
    X, Y = s.view_plan()
    M, Z = s.view_section()
    assert len(X) == len(Y) == len(M) == len(Z) == 3

def test_view_plan_requires_dx_dy():
    s = Survey.from_md_tvd(arr(0, 10, 20), arr(0, 9, 18))
    with pytest.raises(ValueError):
        s.view_plan()


# ---------- Downsampling ----------
def test_downsample_reduces_points_and_preserves_endpoints():
    md  = np.linspace(0.0, 100.0, 101)
    tvd = md.copy()
    s = Survey.from_md_tvd(md, tvd)
    downs = s.downsample(max_points=5)
    # downs returns tuple skipping None -> here (MD, TVD)
    md_d, tvd_d = downs
    assert md_d.size == 5 and tvd_d.size == 5
    assert md_d[0] == md[0] and md_d[-1] == md[-1]
    assert tvd_d[0] == tvd[0] and tvd_d[-1] == tvd[-1]

def test_downsample_invalid_max_points_raises():
    s = Survey.from_md_tvd(arr(0, 10), arr(0, 9))
    with pytest.raises(ValueError):
        s.downsample(1)


# ---------- Inverse planning ----------
def test_solve_straight_to_target_vertical_segment():
    inc, azi = Survey.solve_straight_to_target(
        x_target=0.0, y_target=0.0, tvd_target=100.0,
        x0=0.0, y0=0.0, tvd0=0.0,
        md_start=0.0, md_end=100.0
    )
    # Straight vertical down: ~0 deg inclination, azimuth arbitrary (0 expected here)
    assert abs(inc - 0.0) < 1e-6
    assert abs(azi - 0.0) < 1e-6

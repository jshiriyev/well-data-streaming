import numpy as np
from shapely.geometry import LineString, MultiLineString
from scipy.interpolate import splprep, splev

def bspline_smooth_line(line, s=10.0, k=3, per=False, n_samples=None):
    xy = np.asarray(line.coords)
    if len(xy) < k+1:
        return line  # too short to fit
    # Parameterize by cumulative arclength for stability
    seg = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    t = np.insert(np.cumsum(seg), 0, 0.0)
    if t[-1] == 0:
        return line
    u = t / t[-1]
    x,y = xy[:,0], xy[:,1]
    tck, _ = splprep([x, y], u=u, s=s, k=min(k, len(xy)-1), per=per)
    if n_samples is None:
        n_samples = max(100, len(xy))  # enough samples for smooth look
    unew = np.linspace(0, 1, n_samples)
    x_new, y_new = splev(unew, tck)
    # Force endpoints exactly if per=False
    x_new[0], y_new[0] = x[0], y[0]
    x_new[-1], y_new[-1] = x[-1], y[-1]
    return LineString(np.column_stack((x_new, y_new)))

def bspline_smooth(geom, **kwargs):
    if geom.geom_type == "LineString":
        return bspline_smooth_line(geom, **kwargs)
    return MultiLineString([bspline_smooth_line(g, **kwargs) for g in geom.geoms])
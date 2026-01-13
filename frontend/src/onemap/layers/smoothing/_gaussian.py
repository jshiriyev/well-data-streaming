import numpy as np
from shapely.geometry import LineString, MultiLineString
from scipy.ndimage import gaussian_filter1d

def gaussian_smooth_line(line, sigma_pts=2.0):
    xy = np.asarray(line.coords)
    if len(xy) < 5:
        return line
    x = gaussian_filter1d(xy[:,0], sigma=sigma_pts, mode='nearest')
    y = gaussian_filter1d(xy[:,1], sigma=sigma_pts, mode='nearest')
    x[0], y[0] = xy[0]
    x[-1], y[-1] = xy[-1]
    return LineString(np.column_stack((x, y)))

def gaussian_smooth(geom, sigma_pts=2.0):
    if geom.geom_type == "LineString":
        return gaussian_smooth_line(geom, sigma_pts)
    return MultiLineString([gaussian_smooth_line(g, sigma_pts) for g in geom.geoms])

import numpy as np
from shapely.geometry import LineString, MultiLineString
from scipy.signal import savgol_filter

def savgol_smooth_line(line, window_length=9, polyorder=2):
    xy = np.asarray(line.coords)
    if len(xy) < window_length:
        return line
    x = savgol_filter(xy[:,0], window_length=window_length, polyorder=polyorder, mode='interp')
    y = savgol_filter(xy[:,1], window_length=window_length, polyorder=polyorder, mode='interp')
    # keep endpoints exactly
    x[0], y[0] = xy[0]
    x[-1], y[-1] = xy[-1]
    return LineString(np.column_stack((x, y)))

def savgol_smooth(geom, window_length=9, polyorder=2):
    if geom.geom_type == "LineString":
        return savgol_smooth_line(geom, window_length, polyorder)
    return MultiLineString([savgol_smooth_line(g, window_length, polyorder) for g in geom.geoms])

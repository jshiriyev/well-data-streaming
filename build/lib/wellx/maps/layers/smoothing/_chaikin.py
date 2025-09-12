import numpy as np
from shapely.geometry import LineString, MultiLineString

def chaikin_1pass(coords, weight=0.25, keep_ends=True):
    new = []
    n = len(coords)
    if keep_ends:
        new.append(coords[0])
    for i in range(n-1):
        p = np.array(coords[i]); q = np.array(coords[i+1])
        Q = (1 - weight) * p + weight * q
        R = weight * p + (1 - weight) * q
        new.extend([tuple(Q), tuple(R)])
    if keep_ends:
        new.append(coords[-1])
    return new

def chaikin_smooth_line(line, iterations=2, weight=0.25):
    coords = list(line.coords)
    for _ in range(iterations):
        coords = chaikin_1pass(coords, weight=weight, keep_ends=True)
    return LineString(coords)

def chaikin_smooth(geom, iterations=2, weight=0.25):
    if geom.geom_type == "LineString":
        return chaikin_smooth_line(geom, iterations, weight)
    return MultiLineString([chaikin_smooth_line(g, iterations, weight) for g in geom.geoms])
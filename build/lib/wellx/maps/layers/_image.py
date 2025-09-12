from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple, Union

import folium
from pyproj import CRS, Transformer

LatLonBounds = Sequence[Sequence[float]]  # [[lat_min, lon_min], [lat_max, lon_max]]
Float2 = Tuple[float, float]

def image_overlay(
    path: Union[str, Path],
    name: Optional[str] = None,
    *,
    # Option A: give projected XY ranges and let the function transform -> WGS84
    x: Optional[Float2] = None,
    y: Optional[Float2] = None,
    crs_from: Union[str, int, CRS] = "EPSG:32639",
    crs_to: Union[str, int, CRS] = "EPSG:4326",
    # Option B: provide lat/lon bounds directly (wins over x/y if given)
    latlon_bounds: Optional[LatLonBounds] = None,
    # Where to add (optional). If None: return unattached overlay.
    group: Optional[Union[folium.Map, folium.FeatureGroup]] = None,
    **kwargs,
) -> folium.raster_layers.ImageOverlay:
    """
    Create a Folium ImageOverlay with flexible bounds input and CRS handling.

    You can either:
      1) pass projected coordinate ranges `x=(xmin, xmax)`, `y=(ymin, ymax)` and let
         the function transform them into geographic bounds; or
      2) pass `latlon_bounds=[[lat_min, lon_min], [lat_max, lon_max]]` directly.

    If both are provided, `latlon_bounds` takes precedence.

    Parameters
    ----------
    path : str | pathlib.Path
        Path or URL to the raster image (e.g., PNG). It can also be a NumPy array or
        PIL image if Folium’s `ImageOverlay` supports it in your version.
    name : str, optional
        Layer name used by Folium’s layer control.
    x, y : (float, float), optional
        Projected coordinate ranges of the image footprint. Order need not be sorted;
        the function will handle reversed ranges. Only used when `latlon_bounds` is
        not provided.
    crs_from : str | int | pyproj.CRS, default "EPSG:32639"
        The CRS of the provided `x/y` coordinates (e.g., a UTM EPSG). Ignored if
        `latlon_bounds` is given.
    crs_to : str | int | pyproj.CRS, default "EPSG:4326"
        The target CRS for the overlay bounds. Folium/Leaflet expect WGS84 (EPSG:4326)
        latitude/longitude. Change this only if you know your Leaflet map uses a
        custom CRS (rare).
    latlon_bounds : [[lat_min, lon_min], [lat_max, lon_max]], optional
        Geographic bounds. If provided, this is used directly and no transformation
        occurs.
    group : folium.Map | folium.FeatureGroup, optional
        A map or group to immediately attach the overlay to. If None, the overlay
        is returned but not added.
    **kwargs :
        Extra keyword arguments forwarded to `folium.raster_layers.ImageOverlay`,
        such as `opacity`, `zindex`, `interactive`, `cross_origin`, `alt`,
        `bounds`-independent styling flags, and `show`.

    Returns
    -------
    folium.raster_layers.ImageOverlay
        The created ImageOverlay (already added to `group` if provided).

    Raises
    ------
    ValueError
        If neither `latlon_bounds` nor (`x` and `y`) are provided, or if bounds
        cannot be computed.

    Examples
    --------
    Basic usage with projected coordinates (UTM 39N -> WGS84):
    >>> overlay = image_overlay(
    ...     "static/geology.png",
    ...     name="Geology",
    ...     x=(440000, 460000),
    ...     y=(4470000, 4490000),
    ...     opacity=0.6
    ... )

    Direct lat/lon bounds:
    >>> overlay = image_overlay(
    ...     "https://example.com/overlay.png",
    ...     latlon_bounds=[[40.35, 49.70], [40.55, 49.95]],
    ...     name="Overlay",
    ...     zindex=500
    ... )

    Immediately add to a map:
    >>> m = folium.Map(location=[40.45, 49.85], zoom_start=11)
    >>> image_overlay("overlay.png",
    ...               latlon_bounds=[[40.35, 49.70], [40.55, 49.95]],
    ...               group=m, opacity=0.5)
    >>> folium.LayerControl().add_to(m)
    >>> m.save("map.html")
    """
    # 1) Resolve / normalize bounds
    if latlon_bounds is not None:
        bounds = _validate_latlon_bounds(latlon_bounds)
    else:
        if x is None or y is None:
            raise ValueError(
                "Provide either `latlon_bounds` or both projected ranges `x=(xmin, xmax)` and `y=(ymin, ymax)`."
            )
        bounds = _projected_ranges_to_latlon_bounds(x, y, crs_from=crs_from, crs_to=crs_to)

    # 2) Build the ImageOverlay
    layer = folium.raster_layers.ImageOverlay(
        name=name,
        image=str(path),
        bounds=bounds,
        **kwargs,
    )

    # 3) Optionally attach to map/group
    if group is not None:
        layer.add_to(group)

    return layer


# --------------------------
# Helpers
# --------------------------

def _validate_latlon_bounds(bounds: LatLonBounds) -> LatLonBounds:
    if (
        not isinstance(bounds, (list, tuple))
        or len(bounds) != 2
        or not isinstance(bounds[0], (list, tuple))
        or not isinstance(bounds[1], (list, tuple))
        or len(bounds[0]) != 2
        or len(bounds[1]) != 2
    ):
        raise ValueError("`latlon_bounds` must be [[lat_min, lon_min], [lat_max, lon_max]].")

    (lat_min, lon_min), (lat_max, lon_max) = bounds

    # Normalize in case user gave reversed order
    lat1, lat2 = sorted((float(lat_min), float(lat_max)))
    lon1, lon2 = sorted((float(lon_min), float(lon_max)))

    return [[lat1, lon1], [lat2, lon2]]


def _projected_ranges_to_latlon_bounds(
    x: Float2,
    y: Float2,
    *,
    crs_from: Union[str, int, CRS],
    crs_to: Union[str, int, CRS],
) -> LatLonBounds:
    # Ensure numeric & sorted
    xmin, xmax = sorted((float(x[0]), float(x[1])))
    ymin, ymax = sorted((float(y[0]), float(y[1])))

    crs_from = CRS.from_user_input(crs_from)
    crs_to = CRS.from_user_input(crs_to)

    if crs_from == crs_to:
        # Already in target CRS; assume x->lon and y->lat
        lon_min, lon_max = xmin, xmax
        lat_min, lat_max = ymin, ymax
    else:
        # Use always_xy=True to interpret as (x, y) regardless of axis order
        tr = Transformer.from_crs(crs_from, crs_to, always_xy=True)

        # Transform both corners
        lon_min, lat_min = tr.transform(xmin, ymin)
        lon_max, lat_max = tr.transform(xmax, ymax)

        # Normalize in case the transformation flips orientation
        lon_min, lon_max = sorted((lon_min, lon_max))
        lat_min, lat_max = sorted((lat_min, lat_max))

    return [[lat_min, lon_min], [lat_max, lon_max]]

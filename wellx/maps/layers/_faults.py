from __future__ import annotations

from typing import Optional, Sequence, Union, Callable, Dict, Any

import folium
import geopandas as gpd
from shapely.geometry.base import BaseGeometry

StyleDict = Dict[str, Any]
StyleFunc = Callable[[dict], StyleDict]  # f(feature)->style

def faults(
    gdf_or_geojson: Union[gpd.GeoDataFrame, dict, str],
    *,
    name: str = "Faults",
    group: Optional[Union[folium.Map, folium.FeatureGroup]] = None,
    # Pane / LayerControl behavior
    pane: str = "overlayPane",
    control: bool = True,
    # Styling (display)
    style: Optional[StyleDict] = None,
    style_function: Optional[StyleFunc] = None,
    highlight_function: Optional[StyleFunc] = None,
    # Tooltip / Popup (either fields+aliases or pass objects)
    tooltip_fields: Optional[Sequence[str]] = None,
    tooltip_aliases: Optional[Sequence[str]] = None,
    tooltip: Optional[folium.Tooltip] = None,
    popup_fields: Optional[Sequence[str]] = None,
    popup_aliases: Optional[Sequence[str]] = None,
    popup: Optional[folium.Popup] = None,
    # CRS handling (for GeoDataFrame only)
    reproject_to_wgs84: bool = True,
    # Optional geometry simplification (server-side before serializing)
    simplify_tolerance: Optional[float] = None,
    simplify_preserve_topology: bool = True,
    # Pass-through extras to folium.GeoJson (e.g., show=False, smooth_factor=0)
    **geojson_kwargs,
) -> folium.GeoJson:
    """
    Build a Folium GeoJson layer for fault polylines with flexible styling and UX.

    Parameters
    ----------
    gdf_or_geojson : GeoDataFrame | dict | str
        - GeoDataFrame of LineString/MultiLineString faults, or
        - GeoJSON mapping (Python dict), or
        - GeoJSON text (str).
        If a GeoDataFrame is provided and `reproject_to_wgs84=True` (default), it
        is reprojected to EPSG:4326 for Leaflet.
    name : str, default "Faults"
        Layer name shown in LayerControl (if `control=True`).
    group : folium.Map | folium.FeatureGroup, optional
        If provided, the layer is added to this map/group; otherwise it is returned unattached.
    pane : str, default "overlayPane"
        Leaflet pane for z-ordering relative to other layers.
    control : bool, default True
        Whether this layer appears in `folium.LayerControl`.
    style : dict, optional
        Constant style for the faults (e.g., {"color":"black","weight":3,"opacity":0.3}).
        Ignored if `style_function` is provided.
    style_function : Callable[[feature], dict], optional
        Dynamic per-feature style. If provided, overrides `style`.
    highlight_function : Callable[[feature], dict], optional
        Hover style; e.g., `lambda f: {"weight": 5, "opacity": 0.8}`.
    tooltip_fields, tooltip_aliases : Sequence[str], optional
        If provided and `tooltip` is None, builds a `folium.GeoJsonTooltip`.
    tooltip : folium.Tooltip, optional
        Custom tooltip object (wins over `tooltip_fields/aliases`).
    popup_fields, popup_aliases : Sequence[str], optional
        If provided and `popup` is None, builds a `folium.GeoJsonPopup`.
    popup : folium.Popup, optional
        Custom popup object (wins over `popup_fields/aliases`).
    reproject_to_wgs84 : bool, default True
        Only applies when input is a GeoDataFrame. If its CRS is set and not
        EPSG:4326, reproject to WGS84 so Leaflet renders correctly.
    simplify_tolerance : float, optional
        If given (units of layer CRS / degrees if already 4326), geometries are
        simplified on the server prior to serialization to reduce payload size.
    simplify_preserve_topology : bool, default True
        Preserve topology when simplifying (recommended for lines).
    **geojson_kwargs :
        Additional keyword args forwarded to `folium.GeoJson`, e.g.:
        `show=False`, `smooth_factor=0`, `embed=False`, `zoom_on_click=False`, etc.

    Returns
    -------
    folium.GeoJson
        The constructed GeoJson layer (already added to `group` if provided).

    Examples
    --------
    >>> layer = faults(
    ...     faults_gdf,
    ...     name="Field Faults",
    ...     style={"color":"#333","weight":2,"opacity":0.6},
    ...     tooltip_fields=["fault"], tooltip_aliases=["Fault:"],
    ...     group=m, show=True, smooth_factor=0.0
    ... )
    >>> folium.LayerControl().add_to(m)
    """
    # --- Build data payload (gdf -> GeoJSON mapping/text) ---
    if isinstance(gdf_or_geojson, gpd.GeoDataFrame):
        gdf = gdf_or_geojson

        # optional simplification before reprojection (cheaper in native CRS)
        if simplify_tolerance is not None and not gdf.empty:
            gdf = gdf.copy()
            gdf["geometry"] = gdf.geometry.simplify(simplify_tolerance, preserve_topology=simplify_preserve_topology)

        # reproject if needed for Leaflet
        if reproject_to_wgs84 and gdf.crs is not None and str(gdf.crs).lower() not in {"epsg:4326", "epsg:4326:84", "wgs84"}:
            gdf = gdf.to_crs(epsg=4326)

        data = gdf.__geo_interface__  # faster than to_json for Folium
    else:
        # dict or str (GeoJSON mapping or text) — pass through
        data = gdf_or_geojson

    # --- Tooltip / Popup wiring ---
    tooltip_obj = tooltip
    if tooltip_obj is None and tooltip_fields:
        tooltip_obj = folium.GeoJsonTooltip(fields=list(tooltip_fields), aliases=list(tooltip_aliases or []))

    popup_obj = popup
    if popup_obj is None and popup_fields:
        popup_obj = folium.GeoJsonPopup(fields=list(popup_fields), aliases=list(popup_aliases or []))

    # --- Default style if none provided ---
    if style_function is None and style is None:
        style = {"color": "black", "weight": 3, "opacity": 0.3}

    # --- Compose layer ---
    layer = folium.GeoJson(
        data=data,
        name=name,
        pane=pane,
        control=control,
        style_function=(style_function or (lambda f, _s=style: _s)),
        highlight_function=highlight_function,
        tooltip=tooltip_obj,
        popup=popup_obj,
        **geojson_kwargs,
    )

    if group is not None:
        layer.add_to(group)

    return layer

from __future__ import annotations

import html
import math

from typing import Any, Dict, List, Optional, Union, Callable

from branca.element import Element
import folium
import pandas as pd
from pyproj import Transformer

# Reuse transformers (fast & thread-safe)
_TO_WEB = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
_FROM_WEB = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

def platform(
	lat: float,
	lon: float,
	width_m: float = 120,
	height_m: float = 80,
	angle_deg: float = 0,
	color: str = "#111",
	weight: float = 2,
	fill: bool = True,
	fill_color: str = "#22c55e",
	fill_opacity: float = 0.85,
	close: bool = True,
	**polygon_kwargs
	) -> folium.Polygon:
	"""
	Create a rotated rectangular *vector* marker (a Folium Polygon) centered at (lat, lon),
	with size specified in **meters** and rotation in degrees. Because this is a geographic
	path (not a pixel icon), it scales with zoom—like `folium.Circle` (meters).

	Parameters
	----------
	lat, lon : float
		Center latitude and longitude in WGS84 (EPSG:4326).
	width_m, height_m : float, default (40, 18)
		Rectangle size in meters.
	angle_deg : float, default 45
		Rotation angle in degrees (clockwise, visual).
	color : str, default "#111"
		Stroke color.
	weight : float, default 2
		Stroke width in pixels.
	fill : bool, default True
		Whether to fill the rectangle.
	fill_color : str, default "#22c55e"
		Fill color.
	fill_opacity : float, default 0.85
		Fill opacity (0..1).
	close : bool, default True
		If True, repeats the first vertex at the end of the coordinates list.
		Leaflet will close polygons automatically, but closing explicitly can be
		useful for some tooling.
	**polygon_kwargs :
		Additional keyword args passed to `folium.Polygon`, e.g.:
		`dash_array`, `line_cap`, `line_join`, `smooth_factor`, etc.

	Returns
	-------
	folium.Polygon
		Polygon ready to be `.add_to(map_or_group)`.

	Example
	-------
	>>> m = folium.Map([40.41, 49.87], zoom_start=14)
	>>> fg = folium.FeatureGroup(name="Platforms").add_to(m)
	>>> platform(40.415, 49.86, width_m=60, height_m=25, angle_deg=30).add_to(fg)
	>>> folium.LayerControl().add_to(m)
	>>> m.save("platform.html")

	"""
	# --- validate inputs ---
	if not (isinstance(lat, (int, float)) and isinstance(lon, (int, float))):
		raise TypeError("lat and lon must be numbers.")
	if not (math.isfinite(lat) and math.isfinite(lon)):
		raise ValueError("lat and lon must be finite numbers.")
	if not (-90 <= lat <= 90 and -180 <= lon <= 180):
		raise ValueError("lat/lon out of range (WGS84).")
	if width_m <= 0 or height_m <= 0:
		raise ValueError("width_m and height_m must be positive.")

	# center in meters (Web Mercator)
	x0, y0 = _TO_WEB.transform(lon, lat)

	# unrotated rectangle (meters) about origin
	w2, h2 = width_m / 2.0, height_m / 2.0
	rect = [(-w2, -h2), (w2, -h2), (w2, h2), (-w2, h2)]

	# rotate and project back to lat/lon
	a = math.radians(angle_deg)
	ca, sa = math.cos(a), math.sin(a)
	coords = []
	for dx, dy in rect:
		rx, ry = dx * ca - dy * sa, dx * sa + dy * ca
		lon_i, lat_i = _FROM_WEB.transform(x0 + rx, y0 + ry)
		coords.append([lat_i, lon_i])

	if close:
		coords.append(coords[0])

	layer = folium.Polygon(
		locations=coords,
		color=color,
		weight=weight,
		fill=fill,
		fill_color=fill_color,
		fill_opacity=fill_opacity,
		**polygon_kwargs
	)

	return layer

def _attach_css_once(target: Union[folium.Map, folium.FeatureGroup], css_text: str, key: str) -> None:
    """Attach a <style>…</style> to the figure exactly once."""
    if target is None:
        return
    fig = target.get_root()
    if not hasattr(fig, "_custom_css_registry"):
        fig._custom_css_registry = set()
    if key in fig._custom_css_registry:
        return
    el = Element(f"<style>\n{css_text}\n</style>")
    if hasattr(fig, "header"):
        fig.header.add_child(el, name=key)
    else:
        fig.html.add_child(el, name=key)
    fig._custom_css_registry.add(key)

def platforms(
    frame: pd.DataFrame,
    *,
    # Geometry behavior
    use_fixed_dimensions: bool = False,
    fixed_width_m: float = 120.0,
    fixed_height_m: float = 80.0,
    default_angle_deg: float = 0.0,
    # Styling / display
    polygon_pane: str = "overlayPane",
    color: str = "#111",
    weight: float = 2.0,
    fill: bool = True,
    fill_color: str = "white",
    fill_opacity: float = 0.0,
    polygon_kwargs: Optional[Dict[str, Any]] = None,  # extra folium.Polygon kwargs applied to all rows
    style_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,  # per-row polygon kwargs
    # Popup / Tooltip
    popup_builder: Optional[Callable[[Dict[str, Any]], str]] = None,  # custom HTML builder; must return str
    include_tooltip: bool = True,
    tooltip_builder: Optional[Callable[[Dict[str, Any]], Union[str, folium.Tooltip]]] = None,
    tooltip_field: str = "name",  # used if tooltip_builder is None
    # Where to add
    group: Optional[Union[folium.Map, folium.FeatureGroup]] = None,
    # CSS injection
    add_css: bool = True,
    css_text: Optional[str] = None,
) -> List[folium.Polygon]:
    """
    Create rotated rectangular platform polygons from a pandas DataFrame.

    Expected columns in `frame` (all optional except `lat`/`lon`):
        - name : str
        - length : float   (platform length in meters)
        - width : float    (platform width in meters)
        - year : int|str   (commencement year)
        - lat : float      (WGS84)
        - lon : float      (WGS84)
        - angle : float    (degrees, clockwise visual)
        - sea_depth : float
        - comment : str

    Key features
    ------------
    - If `use_fixed_dimensions=True`, every platform uses `fixed_width_m × fixed_height_m`
      regardless of row `length`/`width` values.
    - Otherwise, per-row `length`/`width` are used when present; missing values fall back to the
      standard values (120 × 80 by default).
    - Popups are HTML-escaped; any missing/NaN becomes an empty string `""`.
    - You can customize polygon kwargs per-row via `style_fn(row_dict)->dict`.
    - Returns the list of created `folium.Polygon` objects; attaches them to `group` if provided.
    - Optional tooltip from `tooltip_field` or a custom `tooltip_builder`.
    - If `group` is provided and `add_css=True`, injects once:
          .leaflet-container .leaflet-interactive:focus { outline: none; }
      This prevents a focus ring from appearing on clicked SVG paths.

    Parameters
    ----------
    use_fixed_dimensions : bool, default False
        If True, ignore row `length`/`width` entirely and use `fixed_width_m` × `fixed_height_m`.
    fixed_width_m, fixed_height_m : float
        Standard platform dimensions (meters).
    default_angle_deg : float, default 0
        Fallback angle if a row has no `angle`.
    polygon_pane, color, weight, fill, fill_color, fill_opacity :
        Base Leaflet styling for polygons (can be overridden per-row by `style_fn`).
    polygon_kwargs : dict, optional
        Extra kwargs forwarded to `folium.Polygon` for all rows (e.g., dash_array, line_join, smooth_factor).
    style_fn : Callable[[row_dict], dict], optional
        Per-row override/additional kwargs for `folium.Polygon`. Receives a sanitized dict with keys:
        name, length, width, year, lat, lon, angle, sea_depth, comment.
    popup_builder : Callable[[row_dict], str], optional
        Custom popup HTML builder (must return a string). If None, a safe default is used.
    include_tooltip : bool, default True
        If True and `tooltip_builder` is None, uses `tooltip_field` (if present) for a simple tooltip.
    tooltip_builder : Callable[[row_dict], str|folium.Tooltip], optional
        Provide a custom tooltip (string or `folium.Tooltip`).
    tooltip_field : str, default "name"
        Field to display in the simple tooltip if `tooltip_builder` is None.
    group : folium.Map | folium.FeatureGroup, optional
        If provided, polygons are added to this map/group.
    add_css : bool, default True
        Whether to inject the CSS rule to remove focus outlines on SVG paths.
    css_text : str, optional
        Custom CSS to inject instead of the default.

    Returns
    -------
    List[folium.Polygon]
        The created polygons (already added to `group` if provided).

    Notes
    -----
    - Requires a `platform(lat, lon, width_m, height_m, angle_deg, **kwargs) -> folium.Polygon`
      function available in scope (your single-platform builder).

    """
    polygon_kwargs = dict(polygon_kwargs or {})

    def _is_nan(v: Any) -> bool:
        return v is None or (isinstance(v, float) and math.isnan(v))

    def _safe_text(v: Any) -> str:
        return "" if _is_nan(v) else html.escape(str(v), quote=True)

    def _num_or_default(v: Any, default_val: float) -> float:
        if _is_nan(v):
            return default_val
        try:
            return float(v)
        except Exception:
            return default_val

    def _popup_default(rd: Dict[str, Any]) -> str:
        # Assemble a compact table; include only fields with non-empty values
        rows = []
        def add_row(label: str, key: str, suffix: str = ""):
            txt = _safe_text(rd.get(key))
            if txt == "":
                return
            if suffix:
                txt = f"{txt}{html.escape(suffix)}"
            rows.append(
                f"<tr><th style='text-align:left;padding-right:6px'>{html.escape(label)}:</th>"
                f"<td>{txt}</td></tr>"
            )

        add_row("Platform", "name")
        # Size: show if at least one side is present
        L = _safe_text(rd.get("length"))
        W = _safe_text(rd.get("width"))
        if L or W:
            rows.append(
                "<tr><th style='text-align:left;padding-right:6px'>Size:</th>"
                f"<td>{L} × {W}</td></tr>"
            )
        add_row("Commencement Year", "year")
        add_row("Sea Depth", "sea_depth", suffix="")  # no unit appended here by default
        add_row("Comments", "comment")

        if not rows:
            return ""
        return "<div><table style='font-size:12px;line-height:1.35'>" + "".join(rows) + "</table></div>"

    # Inject CSS once if requested and we have a target group/map
    if add_css and group is not None:
        default_css = """
/* Remove focus ring on clicked SVG paths */
.leaflet-container .leaflet-interactive:focus { outline: none; }
""".strip()
        _attach_css_once(group, (css_text or default_css), key="platforms-focus-css")

    polys: List[folium.Polygon] = []

    # Use iterrows for robust label-based access
    for _, row in frame.iterrows():
        lat = row.get("lat")
        lon = row.get("lon")
        if _is_nan(lat) or _is_nan(lon):
            continue  # skip invalid rows

        # Determine dimensions
        if use_fixed_dimensions:
            width_m = fixed_width_m
            height_m = fixed_height_m
            # For popup display, reflect the standard dimensions even if row had values
            disp_length = fixed_width_m
            disp_width = fixed_height_m
        else:
            width_m = _num_or_default(row.get("length"), fixed_width_m)
            height_m = _num_or_default(row.get("width"), fixed_height_m)
            disp_length = row.get("length")
            disp_width = row.get("width")

        angle_deg = _num_or_default(row.get("angle"), default_angle_deg)

        # Sanitize values for popup/tooltip and style_fn
        row_dict: Dict[str, Any] = {
            "name": row.get("name", ""),
            "length": disp_length,     # for display in popup
            "width": disp_width,       # for display in popup
            "year": row.get("year", ""),
            "lat": lat,
            "lon": lon,
            "angle": angle_deg,
            "sea_depth": row.get("sea_depth", ""),
            "comment": row.get("comment", ""),
        }

        # Base kwargs for this polygon
        per_row_kwargs: Dict[str, Any] = {
            "pane": polygon_pane,
            "color": color,
            "weight": weight,
            "fill": fill,
            "fill_color": fill_color,
            "fill_opacity": fill_opacity,
        }
        per_row_kwargs.update(polygon_kwargs)

        # Per-row style overrides
        if style_fn is not None:
            try:
                overrides = style_fn(row_dict) or {}
                per_row_kwargs.update(overrides)
            except Exception:
                pass  # ignore style_fn failures for this row

        # Build polygon via your single-platform helper
        poly = platform(
            float(lat), float(lon),
            width_m=width_m, height_m=height_m, angle_deg=angle_deg,
            **per_row_kwargs
        )

        # Popup (safe)
        try:
            popup_html = popup_builder(row_dict) if popup_builder else _popup_default(row_dict)
        except Exception:
            popup_html = ""  # fail-safe

        if popup_html:
            poly.add_child(folium.Popup(popup_html, max_width=360))

        # Tooltip
        if tooltip_builder is not None:
            try:
                tt = tooltip_builder(row_dict)
                if isinstance(tt, folium.Tooltip):
                    poly.add_child(tt)
                elif isinstance(tt, str) and tt:
                    poly.add_child(folium.Tooltip(tt))
            except Exception:
                pass
        elif include_tooltip:
            tip_text = _safe_text(row_dict.get(tooltip_field))
            if tip_text:
                poly.add_child(folium.Tooltip(tip_text))

        if group is not None:
            poly.add_to(group)

        polys.append(poly)

    return polys
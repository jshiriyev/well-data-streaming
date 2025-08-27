import math
from typing import Optional, List, Tuple

import folium

from folium.features import DivIcon

import pandas as pd

from pyproj import Transformer

# Reuse transformers (fast & thread-safe)
_TO_WEB = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
_FROM_WEB = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

def platform(
	lat: float,
	lon: float,
	width_m: float = 40,
	height_m: float = 18,
	angle_deg: float = 45,
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

	poly = folium.Polygon(
		locations=coords,
		color=color,
		weight=weight,
		fill=fill,
		fill_color=fill_color,
		fill_opacity=fill_opacity,
		**polygon_kwargs
	)

	return poly

def wells(
	frame:pd.DataFrame,
	*,
	label_layer:Optional[folium.FeatureGroup]=None,
	head_layer:Optional[folium.FeatureGroup]=None,
	popup_formatter: Optional[str]=None
	)-> Tuple[List[folium.CircleMarker], List[folium.Marker]]:
	"""
	Add well heads (CircleMarker) and optional text labels (DivIcon) for each row.

	This function:
	  - Reads lat/lon and style columns from `frame`.
	  - Creates a CircleMarker per well and (optionally) a text label Marker.
	  - Adds heads to `head_layer` and labels to `label_layer` (if provided).

	Parameters
	----------
	frame : pd.DataFrame
		Table containing at least latitude/longitude columns.
	head_layer : folium.FeatureGroup, optional
		Group to receive CircleMarkers (e.g., your “Wells” group).
	label_layer : folium.FeatureGroup, optional
		Group to receive text labels (can be a FeatureGroupSubGroup of `head_layer`).
	popup_formatter : Callable[[pd.Series], str], optional
        Builds popup HTML from the row; default shows “Name<br/>(lat, lon)”.

	"""
	heads: List[folium.CircleMarker] = []
	labels: List[folium.Marker] = []

	def _fmt_popup(r:pd.Series):

		if popup_formatter is not None:
			return popup_formatter(r)

		name = r.well if isinstance(r.well, str) else "Well"
		
		return f"{name}<br/>({r.lat:.6f}, {r.lon:.6f})"

	for r in frame.itertuples(index=False):

		head = folium.CircleMarker(
			location=[r.lat, r.lon],
			radius=5,
			weight=0,
			color=r.color,
			fill=True,
			fill_opacity=r.fill_opacity
		).add_child(folium.Popup(_fmt_popup(r),max_width=250))

		if head_layer is not None: head.add_to(head_layer)

		heads.append(head)

		# add a text label
		label = folium.Marker(
			[r.lat, r.lon],
			title=r.well,
			icon=DivIcon(
				icon_size=(1,1),	  # minimal; we position via CSS
				icon_anchor=(0,0),
				html=f"""
				<div class="well-label-div">{(r.well or "")}</div>
				"""
			)
		)

		if label_layer is not None: label.add_to(label_layer)

		labels.append(label)

	return heads, labels
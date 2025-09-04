from typing import Optional, List, Tuple

import folium

from folium.features import DivIcon

import pandas as pd

def wells(
	frame:pd.DataFrame,
	*,
	label_group:Optional[folium.FeatureGroup]=None,
	point_group:Optional[folium.FeatureGroup]=None,
	label_pane:Optional[str]="overlayPane",
	point_pane:Optional[str]="overlayPane",
	popup_formatter: Optional[str]=None
	)-> Tuple[List[folium.CircleMarker], List[folium.Marker]]:
	"""
	Add well points (CircleMarker) and optional text labels (DivIcon) for each row.

	This function:
	  - Reads lat/lon and style columns from `frame`.
	  - Creates a CircleMarker per well and (optionally) a text label Marker.
	  - Adds points to `point_group` and labels to `label_group` (if provided).

	Parameters
	----------
	frame : pd.DataFrame
		Table containing at least latitude/longitude columns.
	point_group : folium.FeatureGroup, optional
		Group to receive CircleMarkers (e.g., your “Wells” group).
	label_group : folium.FeatureGroup, optional
		Group to receive text labels (can be a FeatureGroupSubGroup of `point_group`).
	popup_formatter : Callable[[pd.Series], str], optional
        Builds popup HTML from the row; default shows “Name<br/>(lat, lon)”.

	"""
	points: List[folium.CircleMarker] = []
	labels: List[folium.Marker] = []

	def _fmt_popup(r:pd.Series):

		if popup_formatter is not None:
			return popup_formatter(r)

		name = r.well if isinstance(r.well, str) else "Well"
		
		return f"{name}<br/>({r.lat:.6f}, {r.lon:.6f})"

	for r in frame.itertuples(index=False):

		point = folium.CircleMarker(
			location=[r.lat, r.lon],
			radius=5,
			weight=0,
			color=r.color,
			pane=point_pane,
			fill=True,
			fill_opacity=r.fill_opacity
		).add_child(folium.Popup(_fmt_popup(r),max_width=250))

		if point_group is not None: point.add_to(point_group)

		points.append(point)

		# add a text label
		label = folium.Marker(
			[r.lat, r.lon],
			title=r.well,
			pane=label_pane,
			icon=DivIcon(
				icon_size=(1,1),	  # minimal; we position via CSS
				icon_anchor=(0,0),
				html=f"""
				<div class="well-label-div">{(r.well or "")}</div>
				"""
			)
		)

		if label_group is not None: label.add_to(label_group)

		labels.append(label)

	return points, labels

def well_search(
	frame:pd.DataFrame,
	*,
	layer:Optional[folium.FeatureGroup]=None,
	pane="overlayPane",
	icon_class_name="leaflet-div-icon",
	**kwargs
	)-> Tuple[List[folium.CircleMarker], List[folium.Marker]]:
	"""
	Parameters
	----------
	frame : pd.DataFrame
		Table containing at least latitude/longitude columns.
	layer : folium.FeatureGroup, optional
		Group to receive Markers (e.g., your “Wells” group).

	"""
	labels: List[folium.Marker] = []

	for r in frame.itertuples(index=False):

		label = folium.Marker(
			[r.lat, r.lon],
			pane=pane,
			title=r.well,
			icon=DivIcon(
				icon_size=(1,1),	  # minimal; we position via CSS
				icon_anchor=(0,0),
				html="",
				class_name=icon_class_name,
			),
			**kwargs
		)

		if layer is not None: label.add_to(layer)

		labels.append(label)

	return labels
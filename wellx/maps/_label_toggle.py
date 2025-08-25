from branca.element import MacroElement
from jinja2 import Template

class ToggleLabelsOnZoom(MacroElement):
	"""
	Conditionally show or hide a label layer in a Folium/Leaflet map based on zoom level.

	This class injects a JavaScript snippet that listens for `zoomend` events 
	and toggles the visibility of a given layer (typically labels, annotations, 
	or text markers). The layer is only displayed when the zoom level is greater 
	than or equal to a specified threshold.

	Parameters
	----------
	layer : folium.Layer or folium.FeatureGroup
		The layer containing labels or markers to toggle on zoom.
	min_zoom : int, optional (default=16)
		The minimum zoom level at which the labels should become visible.
		Below this zoom, the labels are hidden.

	Example
	-------
	>>> import folium
	>>> from wellx.maps import ToggleLabelsOnZoom
	>>>
	>>> m = folium.Map(location=[40, -74], zoom_start=12)
	>>> labels = folium.FeatureGroup(name="Labels").add_to(m)
	>>> folium.Marker([40, -74], tooltip="Hello").add_to(labels)
	>>>
	>>> # Labels only appear at zoom >= 15
	>>> m.get_root().add_child(ToggleLabelsOnZoom(labels, min_zoom=15))
	>>> m.save("map_with_toggle_labels.html")

	Notes
	-----
	- Useful for decluttering maps: hide labels at low zoom levels where they 
	  would overlap heavily, and only show them when the map is zoomed in enough.
	- Works with any Folium layer, but is especially designed for text/label layers.
	- The logic runs once on initialization (to set the initial state) and again 
	  whenever the zoom level changes.

	"""
	_template = Template("""
	{% macro script(this, kwargs) %}
	(function(){
	  var map = {{ this._parent.get_name() }};
	  var labels = {{ this.layer_name }};
	  function onZoom() {
		var z = map.getZoom();
		if (z >= {{ this.min_zoom }}) {
		  if (!map.hasLayer(labels)) map.addLayer(labels);
		} else {
		  if (map.hasLayer(labels)) map.removeLayer(labels);
		}
	  }
	  map.on('zoomend', onZoom);
	  onZoom();
	})();
	{% endmacro %}
	""")

	def __init__(self, layer, min_zoom=16):
		"""
		Initialize the ToggleLabelsOnZoom macro.

		Parameters
		----------
		layer : folium.Layer or folium.FeatureGroup
			The label/marker layer to toggle.
		min_zoom : int, optional (default=16)
			Minimum zoom level at which the layer should be visible.
			
		"""
		super().__init__()

		self.layer_name = layer.get_name()
		self.min_zoom = min_zoom

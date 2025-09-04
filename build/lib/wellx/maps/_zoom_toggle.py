from branca.element import MacroElement
from jinja2 import Template

class ZoomToggle(MacroElement):
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
	parent_layer : folium.Layer or folium.FeatureGroup, optional
    The *visible* parent group (e.g., wells/markers). If provided, labels show
    only when this parent is visible in LayerControl.
	min_zoom : int, optional (default=16)
		The minimum zoom level at which the labels should become visible.
		Below this zoom, the labels are hidden.

	Example
	-------
	>>> import folium
	>>> from wellx.maps import ZoomToggle
	>>>
	>>> m = folium.Map(location=[40, -74], zoom_start=12)
	>>> labels = folium.FeatureGroup(name="Labels").add_to(m)
	>>> folium.Marker([40, -74], tooltip="Hello").add_to(labels)
	>>>
	>>> # Labels only appear at zoom >= 15
	>>> m.get_root().add_child(ZoomToggle(labels, min_zoom=15))
	>>> m.save("map_with_toggle_labels.html")

	Notes
	-----
	- Useful for decluttering maps: hide labels at low zoom levels where they 
	  would overlap heavily, and only show them when the map is zoomed in enough.
	- Works with any Folium layer, but is especially designed for text/label layers.
	- The logic runs once on initialization (to set the initial state) and again 
	  whenever the zoom level changes.
	- For best UX, add `parent_layer` to LayerControl, and keep `layer` (labels)
      out of LayerControl (control=False) so users don’t have to toggle two things.
    - Works with FeatureGroup or Layer instances.

	"""
	_template = Template("""
    {% macro script(this, kwargs) %}
    (function(){
      var map = {{ this._parent.get_name() }};
      var labels = {{ this.layer_name }};
      var parent = {{ this.parent_layer_name if this.parent_layer_name else 'null' }};
      var MINZ = {{ this.min_zoom }};

      function refresh() {
        var zoomOK = map.getZoom() >= MINZ;
        var parentOK = true;
        if (parent !== null) {
          parentOK = map.hasLayer(parent);
        }
        var shouldShow = zoomOK && parentOK;

        if (shouldShow) {
          if (!map.hasLayer(labels)) map.addLayer(labels);
        } else {
          if (map.hasLayer(labels)) map.removeLayer(labels);
        }
      }

      // Recompute on zoom or when overlays are toggled in LayerControl
      map.on('zoomend', refresh);
      map.on('overlayadd', refresh);
      map.on('overlayremove', refresh);

      // Initial state
      refresh();
    })();
    {% endmacro %}
    """)

	def __init__(self, layer, parent_layer=None, min_zoom=16):
		"""
		Initialize the ZoomToggle macro.

		Parameters
		----------
		layer : folium.Layer or folium.FeatureGroup
			The label/marker layer to toggle.
		min_zoom : int, optional (default=16)
			Minimum zoom level at which the layer should be visible.
			
		"""
		super().__init__()

		self.layer_name = layer.get_name()
		self.parent_layer_name = parent_layer.get_name() if parent_layer is not None else None
		self.min_zoom = min_zoom

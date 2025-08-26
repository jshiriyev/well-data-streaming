from branca.element import MacroElement
from jinja2 import Template

class ReCenter(MacroElement):
	"""
	A custom Folium/Leaflet control to re-center the map to a predefined latitude,
	longitude, and zoom level.

	This class creates a button (⟳) on the map, which when clicked, resets
	the map view back to the specified coordinates and zoom. It is useful when
	users navigate away from the initial focus and need a quick way to return.

	Parameters
	----------
	lat : float
		Latitude to re-center the map on.
	lon : float
		Longitude to re-center the map on.
	zoom : int
		Zoom level to reset the map to.
	position : str, optional (default='bottomleft')
		Position of the control on the map. Options include:
		'topleft', 'topright', 'bottomleft', 'bottomright'.

	Examples
	--------
	>>> import folium
	>>> m = folium.Map(location=[40.4093, 49.8671], zoom_start=10)
	>>> m.add_child(ReCenter(lat=40.4093, lon=49.8671, zoom=10))
	>>> m.save("map_with_recenter.html")
	
	"""
	# Jinja2 template for rendering the Leaflet control
	_template = Template("""
		{% macro script(this, kwargs) %}
		var map = {{ this._parent.get_name() }};
		var Reset{{ this.get_name() }} = L.Control.extend({
			onAdd: function(map) {
				// Create a container for the button
				var container = L.DomUtil.create('div', 'leaflet-bar');

				// Create the button element
				var btn = L.DomUtil.create('a', '', container);
				btn.innerHTML = '&#8635;';  // Unicode ⟳
				btn.title = 'Re-center';
				btn.href = '#';
				
				// Style the button
				btn.style.textAlign = 'center';
				btn.style.lineHeight = '26px';
				btn.style.width = '26px';
				btn.style.height = '26px';

				// Add click event: reset view
				L.DomEvent.on(btn, 'click', function(e) {
					L.DomEvent.stop(e);
					map.setView([{{ this.lat }}, {{ this.lon }}], {{ this.zoom }});
				});

				return container;
			}
		});
		map.addControl(new Reset{{ this.get_name() }}({ position: '{{ this.position }}' }));
		{% endmacro %}
	""")

	def __init__(self, lat: float, lon: float, zoom: int, position: str = 'bottomleft'):
		"""
		Initialize the re-center control.
		"""
		super().__init__()
		self._name = "ReCenter"
		self.lat = float(lat)
		self.lon = float(lon)
		self.zoom = int(zoom)
		self.position = position
from branca.element import MacroElement
from jinja2 import Template

class Recenter(MacroElement):
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
	>>> m.add_child(Recenter(lat=40.4093, lon=49.8671, zoom=10))
	>>> m.save("map_with_recenter.html")
	
	"""
	# Jinja2 template for rendering the Leaflet control
	_template = Template("""
		{% macro script(this, kwargs) %}
		var map = {{ this._parent.get_name() }};
		var Reset{{ this.get_name() }} = L.Control.extend({
			onAdd: function(map) {
				// Create a container for the button
				var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');

				// Create the button element
				var btn = L.DomUtil.create('a', '', container);
				btn.innerHTML = '&#8635;';  // Unicode ⟳
				btn.title = 'Re-center';
				btn.href = '#';
				
				// Style the button
				btn.style.width = '30px';
                btn.style.height = '30px';
                btn.style.lineHeight = '30px';
                btn.style.textAlign = 'center';
                btn.style.fontSize = '16px';
                btn.style.textDecoration = 'none';
                btn.style.backgroundColor = 'white';
                btn.style.color = 'black';
                btn.style.display = 'block';
                btn.style.borderBottom = '1px solid #ccc';

                // Hover effect (same as Leaflet search button)
                btn.onmouseover = function() {
                    this.style.backgroundColor = '#f4f4f4';
                };
                btn.onmouseout = function() {
                    this.style.backgroundColor = 'white';
                };

				// Reset view on click
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
		self._name = "Recenter"
		self.lat = float(lat)
		self.lon = float(lon)
		self.zoom = int(zoom)
		self.position = position
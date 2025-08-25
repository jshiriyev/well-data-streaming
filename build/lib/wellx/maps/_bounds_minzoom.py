from branca.element import MacroElement
from jinja2 import Template

class SetBoundsAndMinZoom(MacroElement):
	"""
	A Folium/Leaflet helper to restrict map interactions to a given bounding box.

	This class injects a small JavaScript snippet into a Folium map that:
	  1. Fits the map view to the provided bounds.
	  2. Locks panning so the user cannot move outside those bounds.
	  3. Prevents zooming out beyond the fitted zoom level (while still allowing zooming in).

	Parameters
	----------
	bounds : tuple
		A tuple of two coordinate pairs defining the bounding box:
		((south, west), (north, east))

		Example:
		>>> bounds = ((40.0, -75.0), (42.0, -73.0))
		>>> m.get_root().add_child(SetBoundsAndMinZoom(bounds))

	Notes
	-----
	- This is especially useful when working with static images or limited regions
	  where you don’t want users to zoom or pan into blank space.
	- The bounding box is applied with `map.setMaxBounds()` and `map.setMinZoom()`
	  (after the initial fit).

	"""
	_template = Template(
		"""
		{% macro script(this, kwargs) %}
		(function() {
			var map = {{ this._parent.get_name() }};
			var b = L.latLngBounds(
				[ [{{ this.south }}, {{ this.west }}], [{{ this.north }}, {{ this.east }}] ]
			);

			// Fit to bounds
			map.fitBounds(b, {padding:[0,0]});

			// Restrict panning to the bounds
			map.setMaxBounds(b);
			map.options.maxBounds = b;
			map.options.maxBoundsViscosity = 1.0;

			// After fit, lock the minimum zoom to current zoom so users can't zoom out to blank space
			var z = map.getZoom();
			map.setMinZoom(z);
		})();
		{% endmacro %}
		"""
	)

	def __init__(self, bounds:tuple):
		"""
		Initialize the SetBoundsAndMinZoom macro.

		Parameters
		----------
		bounds : tuple
			((south, west), (north, east)) geographic bounds.

		"""
		super().__init__()

		self._name = "SetBoundsAndMinZoom"

		(self.south, self.west), (self.north, self.east) = bounds
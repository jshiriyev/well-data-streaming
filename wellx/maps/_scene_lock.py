from branca.element import MacroElement
from jinja2 import Template

class SceneLock(MacroElement):
	"""
	Fit the map to bounds, lock panning to those bounds, and (optionally) prevent
	zooming out beyond the fitted zoom while still allowing zoom-in.

	This class injects a small JavaScript snippet into a Folium map that:
	  1. Fits the map view to the provided bounds.
	  2. Locks panning so the user cannot move outside those bounds.
	  3. Prevents zooming out beyond the fitted zoom level (while still allowing zooming in).

	Parameters
	----------
	bounds : [[min_lat, min_lng], [max_lat, max_lng]]
		Geographic bounds of your content.
	pad : float
		Fractional padding applied to max bounds (0.02 = 2% on each side).
	fit : bool
		If True, call map.fitBounds(...) inside the control.
	fit_padding : (int, int)
		Pixel padding used by fitBounds (x, y).
	fit_max_zoom : int | None
		Optional maxZoom cap during fitBounds.
	animate : bool
		Animate the fitBounds transition.
	no_wrap : bool
		If True, set noWrap=True on tile layers and disable world wrapping.
	viscosity : float
		Leaflet maxBoundsViscosity (0..1). 1 = “sticky” edges.
	lock_min_zoom : bool
		Lock minZoom to the fitted zoom so you can't zoom out past it

	Example:
	>>> bounds = ((40.0, -75.0), (42.0, -73.0))
	>>> SceneLock(bounds,
		pad=0.02,
		fit=True,
		fit_padding=(24,24),
		fit_max_zoom=None,   # or a number if you want to cap the fit zoom-in
		animate=False,
		no_wrap=True,
		viscosity=1.0,	   # make panning strictly confined
		lock_min_zoom=True).add_to(m)

	Notes
	-----
	- This is especially useful when working with static images or limited regions
	  where you don’t want users to zoom or pan into blank space.
	- The bounding box is applied with `map.setMaxBounds()` and `map.setMinZoom()`
	  (after the initial fit).

	"""
	_template = Template("""
	{% macro script(this, kwargs) -%}
	(function(){
	  var map = {{ this._parent.get_name() }};

	  var sw = L.latLng({{ this.sw[0] }}, {{ this.sw[1] }});
	  var ne = L.latLng({{ this.ne[0] }}, {{ this.ne[1] }});
	  var bounds = L.latLngBounds(sw, ne);

	  // Lock panning to padded bounds
	  var paddedMax = bounds.pad({{ this.pad }});
	  map.setMaxBounds(paddedMax);
	  map.options.maxBoundsViscosity = {{ this.viscosity }};

	  {% if this.no_wrap %}
	  map.eachLayer(function(layer){ if (layer instanceof L.TileLayer) layer.options.noWrap = true; });
	  map.on('layeradd', function(e){ if (e.layer instanceof L.TileLayer) e.layer.options.noWrap = true; });
	  {% endif %}

	  function doFit(){
		{% if this.fit %}
		var opts = {
		  padding: L.point({{ this.fit_padding[0] }}, {{ this.fit_padding[1] }}),
		  {% if this.fit_max_zoom is not none %}maxZoom: {{ this.fit_max_zoom }},{% endif %}
		  animate: {{ 'true' if this.animate else 'false' }}
		};
		map.fitBounds(bounds, opts);

		{% if this.lock_min_zoom %}
		var lock = function(){ map.setMinZoom(map.getZoom()); };
		if (opts.animate) { map.once('zoomend', lock); } else { lock(); }
		{% endif %}
		{% endif %}
	  }

	  // Defer until map is fully ready (prevents tiny container -> tiny zoom)
	  if (map._loaded) {
		requestAnimationFrame(doFit);
	  } else {
		map.once('load', doFit);
	  }

	  // Safety: after the first real resize (layout settling), ensure we aren't under-zoomed
	  map.once('resize', function(){
		var target = map.getBoundsZoom(bounds, true, L.point({{ this.fit_padding[0] }}, {{ this.fit_padding[1] }}));
		if (map.getZoom() < target) {
		  map.setView(bounds.getCenter(), target, {animate:false});
		  {% if this.lock_min_zoom %} map.setMinZoom(target); {% endif %}
		}
	  });
	})();
	{%- endmacro %}
	""")

	def __init__(
		self,
		bounds,
		*,
		pad: float = 0.02,		  # fractional padding for max bounds
		fit: bool = True,		   # perform fitBounds
		fit_padding: tuple[int,int] = (20, 20),
		fit_max_zoom: int | None = None,
		animate: bool = False,
		no_wrap: bool = True,	   # disable world wrapping on tiles
		viscosity: float = 0.8,	 # 1.0 = hard lock; <1 = "sticky" bounce
		lock_min_zoom: bool = True  # prevent zooming out past fitted level
	):
		super().__init__()
		self.sw, self.ne = bounds[0], bounds[1]
		self.pad = float(pad)
		self.fit = bool(fit)
		self.fit_padding = tuple(fit_padding)
		self.fit_max_zoom = fit_max_zoom
		self.animate = bool(animate)
		self.no_wrap = bool(no_wrap)
		self.viscosity = float(viscosity)
		self.lock_min_zoom = bool(lock_min_zoom)
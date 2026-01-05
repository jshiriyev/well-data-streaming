from pathlib import Path
from typing import Dict, Optional, Union

from branca.element import MacroElement, Element
from jinja2 import Template

class Recenter(MacroElement):
	"""
	A custom Folium/Leaflet control to re-center the map to a predefined latitude,
	longitude, and zoom level. It is useful when users navigate away from the
	initial focus and need a quick way to return.

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
	TEMPLATES: Dict[str, Dict[str, Union[Template, str, None]]] = {
		"classic": {
			"script" : Template("""
			{% macro script(this, kwargs) %}
			var map = {{ this._parent.get_name() }};
			var Reset{{ this.get_name() }} = L.Control.extend({
				onAdd: function(map) {
					// Create a container for the button
					var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');

					// Create the button element
					var btn = L.DomUtil.create('a', '', container);
					btn.innerHTML = '&#8635;';	// Unicode ⟳
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

					btn.setAttribute('role','button');
					btn.setAttribute('aria-label','Re-center map');
					btn.setAttribute('tabindex','0');

					L.DomEvent.disableClickPropagation(container);
					L.DomEvent.disableScrollPropagation(container);

					L.DomEvent.on(btn, 'click', function(e){
						L.DomEvent.stop(e);
						map.setView([{{ this.lat }}, {{ this.lon }}], {{ this.zoom }});
					});

					L.DomEvent.on(btn, 'keydown', function(e){
					  if (e.key === 'Enter' || e.key === ' ') {
						L.DomEvent.stop(e);
						map.setView([{{ this.lat }}, {{ this.lon }}], {{ this.zoom }});
					  }
					});

					return container;
				}
			});
			map.addControl(new Reset{{ this.get_name() }}({ position: '{{ this.position }}' }));
			{% endmacro %}
			"""),
			"style" : ""
		},
		"modern": {
			"script" : Template("""
			{% macro script(this, kwargs) %}
			(function(){
				var map = {{ this._parent.get_name() }};

				var RecenterCtl{{ this.get_name() }} = L.Control.extend({
				options: { position: '{{ this.position }}' },
				onAdd: function(map) {
					var container = L.DomUtil.create('div', 'leaflet-control leaflet-control-recenter');

					// button element
					var btn = L.DomUtil.create('a', 'recenter-btn', container);
					btn.href = '#';
					btn.title = 'Re-center';
					btn.setAttribute('role','button');
					btn.setAttribute('aria-label','Re-center map');

					// crisp “target” SVG icon (white strokes)
					btn.innerHTML = `
					<svg viewBox="0 0 24 24" aria-hidden="true">
						<circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="2"/>
						<path d="M12 4v3 M12 17v3 M4 12h3 M17 12h3" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/>
					</svg>
					`;

					// prevent map interactions when clicking/scrolling on the control
					L.DomEvent.disableClickPropagation(container);
					L.DomEvent.disableScrollPropagation(container);

					// click -> reset view
					L.DomEvent.on(btn, 'click', function(e){
						L.DomEvent.stop(e);
						map.setView([{{ this.lat }}, {{ this.lon }}], {{ this.zoom }});
					});

					// keyboard (Enter/Space)
					L.DomEvent.on(btn, 'keydown', function(e){
					if (e.key === 'Enter' || e.key === ' ') {
						L.DomEvent.stop(e);
						map.setView([{{ this.lat }}, {{ this.lon }}], {{ this.zoom }});
					}
					});

					return container;
				}
				});

				map.addControl(new RecenterCtl{{ this.get_name() }}());
			})();
			{% endmacro %}
			"""),
			"style" : """
			.leaflet-control-recenter{
			  background:transparent;border:0;box-shadow:none;margin:6px;
			}
			.leaflet-control-recenter .recenter-btn{
			  --rc-size:36px;--rc-bg:rgba(28,28,30,.88);--rc-bg-hover:rgba(28,28,30,.96);--rc-color:#fff;
			  width:var(--rc-size);height:var(--rc-size);display:grid;place-items:center;border-radius:9999px;
			  background:var(--rc-bg);color:var(--rc-color);text-decoration:none;line-height:0;cursor:pointer;
			  box-shadow:0 3px 10px rgba(0,0,0,.32), inset 0 0 0 1px rgba(255,255,255,.12);
			  transition:transform .15s ease, box-shadow .15s ease, background-color .15s ease, opacity .15s ease;
			  -webkit-tap-highlight-color:transparent;
			}
			.leaflet-control-recenter .recenter-btn svg{width:18px;height:18px;display:block;}
			.leaflet-control-recenter .recenter-btn:hover{
			  transform:scale(1.08);background:var(--rc-bg-hover);
			  box-shadow:0 8px 22px rgba(0,0,0,.38), inset 0 0 0 1px rgba(255,255,255,.18);
			}
			.leaflet-control-recenter .recenter-btn:active{transform:scale(0.98);box-shadow:0 3px 10px rgba(0,0,0,.45) inset;}
			.leaflet-control-recenter .recenter-btn:focus-visible{outline:2px solid #60a5fa;outline-offset:2px;}
			"""
		},
	}

	def __init__(
		self,
		lat: float,
		lon: float,
		zoom: int,
		position: str = 'bottomleft',
		variant: str = "classic",
		# optional overrides
		template: Optional[Union[str, Template]] = None,
		template_file: Optional[Union[str, Path]] = None,
		style_css: Optional[str] = None,
		):
		"""
		Initialize the re-center control.
		"""
		super().__init__()
		self._name = "Recenter"
		self.lat = float(lat)
		self.lon = float(lon)
		self.zoom = int(zoom)
		self.position = position.lower()
		self.variant = variant

		# resolve template (priority: explicit template > file > registry by variant)
		self._template = self._resolve_template(template, template_file, variant)

		# resolve CSS (variant CSS + user CSS)
		self._style_text = self._resolve_style(style_css, variant)

		# prepare CSS element (added in render)
		self._css_element = Element(f"<style>\n{self._style_text}\n</style>") if self._style_text else None

	@classmethod
	def register_template(cls, name: str, script_template: Union[str, Template], style_css: str | None = None):
		if isinstance(script_template, str):
			script_template = Template(script_template)
		cls.TEMPLATES[name] = {"script": script_template, "style": style_css or ""}

	# 3) Internal helpers
	def _resolve_template(self, template, template_file, variant) -> Template:
		if template is not None:
			return template if isinstance(template, Template) else Template(str(template))
		if template_file is not None:
			text = Path(template_file).read_text(encoding="utf-8")
			return Template(text)
		if variant not in self.TEMPLATES:
			raise ValueError(f"Unknown variant '{variant}'. Available: {list(self.TEMPLATES)}")
		return self.TEMPLATES[variant]["script"]	# type: ignore[return-value]

	def _resolve_style(self, style_css: Optional[str], variant: str) -> str:
		base = ""
		if variant in self.TEMPLATES:
			base = (self.TEMPLATES[variant].get("style") or "").strip()
		extra = (style_css or "").strip()
		return "\n".join(s for s in (base, extra) if s)

	# 4) Hook CSS into the document head before the map renders
	def render(self, **kwargs):
		fig = self.get_root()
		if self._css_element is not None:
			unique = f"recenter-style-{self.get_name()}"
			if hasattr(fig, "header"):
				fig.header.add_child(self._css_element, name=unique)
			else:
				fig.html.add_child(self._css_element, name=unique)
		super().render(**kwargs)

from pathlib import Path
from branca.element import MacroElement, Element
from jinja2 import Template

class FilterSidebar(MacroElement):

    DEFAULT_HTML = """
<div id="sidebar">
  <div class="leaflet-sidebar-content">
    <div class="leaflet-sidebar-pane" id="filter" aria-labelledby="filter">
      <h1 class="leaflet-sidebar-header">Filters</h1>

      <div id="filters-container"></div>

      <p style="margin-top:12px;color:#666;">
        Click values or drag sliders to filter. Each box filters one column (AND logic).
      </p>
    </div>
  </div>
</div>
""".strip()

    _template = Template("""
{% macro script(this, kwargs) %}
var __sidebar = L.control.sidebar('{{ this.container_id }}', {
    position: '{{ this.position }}',
    autoPan: {{ 'true' if this.autopan else 'false' }},
    closeButton: true
}).addTo({{ this._parent.get_name() }});
{% if this.visible %}__sidebar.show();{% endif %}

// 🔑 Add your custom hotkey handler here
document.addEventListener('keydown', function(e) {
  if (e.shiftKey && (e.key === 'f' || e.key === 'F')) {
    __sidebar.toggle();
  }
});
{% endmacro %}
""")

    def __init__(self, container_id="sidebar", position="left", autopan:bool = False, visible:bool=True,
        sidebar_html: str | None = None):

        super().__init__()
        
        self.container_id = container_id
        self.position = position.lower()
        self.autopan = autopan
        self.visible = visible

        self.sidebar_html = (sidebar_html or self.DEFAULT_HTML)

        self._name = "FilterSidebar"

        self._html_element = Element(self.sidebar_html)

        # Read your uploaded assets (same ones in the demo HTML)
        css_text = Path("L.Control.Sidebar.css").read_text(encoding="utf-8")
        js_text  = Path("L.Control.Sidebar.js").read_text(encoding="utf-8")

        self._css_element = Element(f"<style>\n{css_text}\n</style>")
        self._js_element  = Element(f"<script>\n{js_text}\n</script>")

    def render(self,**kwargs):
        # Attach CSS & JS to the <head> of the figure (before map is finalized)
        fig = self.get_root()
        if hasattr(fig, "header"):
            fig.header.add_child(self._css_element, name="leaflet-sidebar-css")
            fig.header.add_child(self._js_element, name="leaflet-sidebar-js")
        else:
            # Fallback (older Folium): add to html
            fig.html.add_child(self._css_element, name="leaflet-sidebar-css")
            fig.html.add_child(self._js_element, name="leaflet-sidebar-js")

        target = getattr(fig, "html", fig)

        target.add_child(self._html_element, name=f"{self._name}-container-{self.container_id}")

        super().render(**kwargs)
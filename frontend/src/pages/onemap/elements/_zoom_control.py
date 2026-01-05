from branca.element import MacroElement
from jinja2 import Template

class ZoomControl(MacroElement):
    """Custom Zoom control for Folium maps"""
    _template = Template(u"""
        {% macro script(this, kwargs) %}
            L.control.zoom({
                position: '{{this.position}}'
            }).addTo({{this._parent.get_name()}});
        {% endmacro %}
    """)

    def __init__(self, position="topright"):
        super().__init__()
        self._name = "ZoomControl"
        self.position = position
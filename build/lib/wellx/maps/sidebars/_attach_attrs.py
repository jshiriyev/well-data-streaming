# _attach_attrs.py
import json
from branca.element import MacroElement
from jinja2 import Template

class AttachAttrs(MacroElement):
    """
    After a Folium marker is created, attach arbitrary attributes on the Leaflet side:
        marker.__attrs = {...}
    """
    _template = Template("""
    {% macro script(this, kwargs) %}
    (function(){
      var m = {{ this.marker_name }};
      if (!m) return;
      m.__attrs = {{ this.attrs_json | safe }};
    })();
    {% endmacro %}
    """)
    def __init__(self, marker, attrs: dict):
        super().__init__()
        self._name = "AttachAttrs"
        self.marker_name = marker.get_name()
        self.attrs_json = json.dumps(attrs, ensure_ascii=False)

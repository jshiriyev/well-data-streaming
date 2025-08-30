from branca.element import MacroElement, Template

class LayerControl(MacroElement):
    """
    Dropdown layer switcher that snaps to Leaflet control corners.

    Parameters
    ----------
    layers : dict[str, folium.Layer] | list[tuple[str, folium.Layer]]
        Mapping or iterable of (label, layer). Only the selected layer is shown.
    position : {'topleft','topright','bottomleft','bottomright'}, default 'topright'
        Corner to attach the control.
    min_size : (int, int) | None
        Minimum (width_px, height_px) for the control.

    """
    _template = Template("""
    {% macro html(this, kwargs) %}
    <!-- container CSS is created dynamically in onAdd -->
    {% endmacro %}

    {% macro script(this, kwargs) %}
    (function(){
      // Resolve Leaflet map object safely
      var mapVarName = {{ this._parent.get_name()|tojson }};
      var mapObj = window[mapVarName];
      if (!mapObj) return;

      function initDropdown(){
        // Define a unique control class per instance
        var Control_{{ this.get_name() }} = L.Control.extend({
          options: { position: '{{ this.position }}' },
          onAdd: function(map) {
            var div = L.DomUtil.create('div', 'leaflet-bar');
            div.id = '{{ this.get_name() }}_container';
            div.style.background = 'white';
            div.style.padding = '6px';
            div.style.boxShadow = '0 1px 4px rgba(0,0,0,0.3)';
            div.style.borderRadius = '6px';
            div.style.display = 'flex';
            div.style.alignItems = 'center';
            div.style.zIndex = '1000';
            {% if this.min_width %}div.style.minWidth = '{{ this.min_width }}px';{% endif %}
            {% if this.min_height %}div.style.minHeight = '{{ this.min_height }}px';{% endif %}

            var select = L.DomUtil.create('select', '', div);
            select.id = '{{ this.get_name() }}_select';
            select.style.border = 'none';
            select.style.outline = 'none';
            select.style.padding = '4px 6px';
            select.style.font = '14px/1.2 sans-serif';
            select.style.background = 'transparent';

            // Fill options
            {% for label in this.layer_labels %}
              var opt = document.createElement('option');
              opt.value = {{ label|tojson }};
              opt.text  = {{ label|tojson }};
              select.appendChild(opt);
            {% endfor %}

            // Prevent map interactions when using the control
            L.DomEvent.disableClickPropagation(div);
            L.DomEvent.disableScrollPropagation(div);
            return div;
          }
        });

        var ctl = new Control_{{ this.get_name() }}();
        ctl.addTo(mapObj);

        // Map label -> Layer object
        var layersMap = {
          {% for label, varname in this.layer_varnames.items() %}
          {{ label|tojson }}: {{ varname }}{% if not loop.last %},{% endif %}
          {% endfor %}
        };

        function switchLayer(label){
          for (var k in layersMap){
            if (mapObj.hasLayer(layersMap[k])) mapObj.removeLayer(layersMap[k]);
          }
          var lyr = layersMap[label];
          if (lyr) mapObj.addLayer(lyr);
        }

        // Bind after the control is in the DOM
        var sel = document.getElementById('{{ this.get_name() }}_select');
        if (sel){
          sel.addEventListener('change', function(e){ switchLayer(e.target.value); });
          if (sel.options.length){
            var initial = sel.options[0].value;
            sel.value = initial;
            switchLayer(initial);
          }
        }
      }

      // Ensure Leaflet is ready and layers are defined
      if (mapObj.whenReady) {
        mapObj.whenReady(function(){ setTimeout(initDropdown, 0); });
      } else {
        // Fallback
        setTimeout(initDropdown, 0);
      }
    })();
    {% endmacro %}
    """)

    def __init__(self, layers, position='topright', min_size=None):

        super().__init__()

        # Normalize layers
        items = list(layers.items()) if isinstance(layers, dict) else list(layers)
        if not items:
            raise ValueError("`layers` must contain at least one (label, layer).")

        valid_positions = {'topleft','topright','bottomleft','bottomright'}
        if position not in valid_positions:
            raise ValueError(f"`position` must be one of {valid_positions}")

        self.position = position

        # Optional min size
        self.min_width = self.min_height = None
        if min_size is not None:
            if (not isinstance(min_size, (tuple, list))) or len(min_size) != 2:
                raise ValueError("`min_size` must be a (min_width_px, min_height_px) tuple.")
            self.min_width, self.min_height = int(min_size[0]), int(min_size[1])

        # Labels and JS var names (Folium exposes these as globals)
        self.layer_labels = []
        self.layer_varnames = {}
        for label, layer in items:
            self.layer_labels.append(str(label))
            self.layer_varnames[str(label)] = layer.get_name()

if __name__ == "__main__":

	import folium

	m = folium.Map(location=[40.4, 49.8], zoom_start=8, zoom_control="topright",)

	wells_A = folium.FeatureGroup(name="Wells – Group A").add_to(m)
	folium.CircleMarker([40.4, 49.8], radius=6, popup="A1").add_to(wells_A)

	wells_B = folium.FeatureGroup(name="Wells – Group B").add_to(m)
	folium.CircleMarker([40.6, 49.9], radius=6, popup="B1").add_to(wells_B)

	# Add the dropdown (defaults to 'topright'); enforce a minimum size of 160×36 px
	dropdown = DropdownLayerControl(
	    layers=[("Group A", wells_A), ("Group B", wells_B)],
	    position='topleft',              # or 'topleft' / 'topright' / 'bottomleft'
	    # min_size=(160, 36)                   # optional
	)
	m.add_child(dropdown)

	# You can still keep the standard LayerControl if you want (optional)
	# folium.LayerControl(position='topright').add_to(m)

	m.save("dropdown_demo.html")
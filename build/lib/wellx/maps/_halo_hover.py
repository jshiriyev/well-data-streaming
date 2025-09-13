from branca.element import MacroElement
from jinja2 import Template

class HaloHover(MacroElement):
    """
    Adds a hover "halo" effect to CircleMarker layers in a Folium/Leaflet map.

    This class injects a small JavaScript snippet that creates a single, 
    non-interactive hollow circle (a "halo") which is dynamically repositioned 
    over any CircleMarker as the user hovers their cursor over it.  

    The halo:
      - Adapts its radius based on the hovered marker's radius plus a padding offset.
      - Is purely visual (non-interactive) and does not interfere with mouse events.
      - Is rendered efficiently with Leaflet’s Canvas renderer, so the cost is 
        essentially constant regardless of the number of CircleMarkers.

    Parameters
    ----------
    layer : folium.FeatureGroup or folium.Layer
        A group of CircleMarkers (or nested groups) to which the hover halo will be bound.  
        The effect applies to every CircleMarker inside this layer.
    color : str, optional (default="#111")
        Stroke color of the halo.
    weight : int, optional (default=1)
        Line weight (thickness) of the halo.
    opacity : float, optional (default=1.0)
        Opacity of the halo line (between 0.0 and 1.0).
    pad : int, optional (default=4)
        Extra radius (in pixels) added to the hovered marker’s radius to form the halo.

    Example
    -------
    >>> import folium
    >>> from wellx.maps import HoverHalo
    >>>
    >>> m = folium.Map(location=[40, -74], zoom_start=6)
    >>> group = folium.FeatureGroup().add_to(m)
    >>> folium.CircleMarker([40, -74], radius=6, color="blue").add_to(group)
    >>> m.get_root().add_child(HoverHalo(group, color="red", pad=6))
    >>> m.save("map_with_halo.html")

    Notes
    -----
    - Only CircleMarkers are supported (not Polygons, Polylines, or regular Markers).
    - Works best with Folium maps rendered in the browser using the Canvas renderer.
    - Only one halo element is created and reused across all markers, minimizing DOM cost.

    """
    _template = Template("""
    {% macro script(this, kwargs) %}
    (function () {
        var map = {{ this._parent.get_name() }};
        var group = {{ this.layer_name }};

        // Single reusable halo (hollow circle)
        var halo = L.circleMarker([0,0], {
            radius: 8,    // will be bumped relative to marker radius
            color: "{{ this.color }}",
            weight: {{ this.weight }},
            opacity: {{ this.opacity }},
            fill: false,
            interactive: false  // don't steal mouse events
        });

        function bindHover(layer){
            if (!layer || !layer.on) return;
            layer.on('mouseover', function (e) {
                var r = (layer.options && layer.options.radius) ? layer.options.radius : 5;
                halo.setLatLng(e.latlng);
                halo.setStyle({radius: r + {{ this.pad }}});
                if (!map.hasLayer(halo)) { halo.addTo(map); }
            });
            layer.on('mouseout', function () {
                if (map.hasLayer(halo)) { map.removeLayer(halo); }
            });
        }

        // Attach to each CircleMarker inside the feature group
        group.eachLayer(function (lyr) {
            if (lyr instanceof L.CircleMarker) {
                bindHover(lyr);
            } else if (lyr && lyr.eachLayer) {
                lyr.eachLayer(function (inner) {
                    if (inner instanceof L.CircleMarker) bindHover(inner);
                });
            }
        });
    })();
    {% endmacro %}
    """)

    def __init__(self, layer, color="#111", weight=1, opacity=1.0, pad=4):
        """
        Initialize the HoverHalo macro.

        Parameters
        ----------
        layer : folium.map.FeatureGroup
            The target FeatureGroup (or LayerGroup) containing CircleMarkers
            that should get hover halos.
        color : str, optional
            Halo stroke color (default: "#111").
        weight : int, optional
            Halo stroke width in pixels (default: 1).
        opacity : float, optional
            Halo stroke opacity (0.0 transparent → 1.0 opaque, default: 1.0).
        pad : int, optional
            Extra radius added to the hovered CircleMarker's radius to size the halo (default: 4).
            
        """

        super().__init__()

        self._name = "HoverHalo"

        self.layer_name = layer.get_name()
        self.color = color
        self.weight = weight
        self.opacity = opacity
        self.pad = pad

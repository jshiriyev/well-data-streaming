from branca.element import Element

import folium

import geopandas as gpd

def contours(gdf:gpd.GeoDataFrame,
    name:str=None,
    spacing:float=100,
    group:folium.FeatureGroup=None,
    display_pane="overlayPane",
    interactive_pane="overlayPane",
    **kwargs
    ):

    gdf_spaced = gdf[gdf["depth"] % spacing == 0]

    if name is None: name = ""

    display_contour = folium.GeoJson(
        data=gdf_spaced.__geo_interface__, name=name,
        pane=display_pane,
        control=False,  # avoid a second entry in LayerControl
        style_function=lambda f: {
            "color": "black",
            "weight": 0.5,
            "opacity": 0.5,
        },
    )

    if group is not None: display_contour.add_to(group)

    hidden_contour = folium.GeoJson(
        data=gdf_spaced.__geo_interface__,
        pane=interactive_pane,
        control=False,
        style_function=lambda f: {
            "color": "#000000",         # it could be any color
            "weight": 10,               # big hit area without visual thickness
            "opacity": 0,               # invisible but interactive
            "className": "no-focus"     # we'll target this with CSS
        },
        popup=folium.GeoJsonPopup(
            fields=["depth"],
            aliases=["Contour:"],
        ),
        popup_keep_highlighted=True,
        tooltip=folium.GeoJsonTooltip(
            fields=["depth"],           # adjust to your property/column names
            aliases=["Contour:"],
            sticky=True,                # tooltip follows pointer
            direction="top",            # or 'right'/'auto'
            opacity=0.9
        ),
    )

    if group is not None: hidden_contour.add_to(group)

def css():
    return Element("""
<style>
/* And specifically for our hit layer */
.no-focus:focus { outline: none; }
</style>
""")
from __future__ import annotations

from typing import Callable, Iterable, Optional, Sequence, Union, Dict, Any

import numpy as np
import folium
import geopandas as gpd
from branca.element import Element


# -----------------------------
# Utilities (CSS + conversions)
# -----------------------------
def _attach_css_once(
    group: Union[folium.Map, folium.FeatureGroup],
    css_text: str,
    *,
    key: str,
) -> Optional[Element]:
    """
    Attach a <style>...</style> block to the Folium figure exactly once.
    Uses a simple registry on the figure object to avoid duplicates.
    """
    if group is None:
        return None

    fig = group.get_root()  # works for Map and FeatureGroup
    if not hasattr(fig, "_custom_css_registry"):
        fig._custom_css_registry = set()

    if key in fig._custom_css_registry:
        return None

    el = Element(f"<style>\n{css_text}\n</style>")
    if hasattr(fig, "header"):
        fig.header.add_child(el, name=key)
    else:
        fig.html.add_child(el, name=key)

    fig._custom_css_registry.add(key)
    return el


def _maybe_inject_contour_css(
    group: Optional[Union[folium.Map, folium.FeatureGroup]],
    interactive_class: str,
    add_css: bool,
    css_text: Optional[str],
) -> None:
    """
    Inject CSS for the interactive hit layer (e.g., remove focus outline) if requested.
    """
    if not add_css or group is None:
        return

    default_css = f"""
/* Remove focus outline on invisible hit-layer paths so click/hover feels clean */
.{interactive_class}:focus {{ outline: none; }}
"""
    _attach_css_once(
        group=group,
        css_text=(css_text or default_css).strip(),
        key=f"contours-css-{interactive_class}",
    )


def _to_numeric(series) -> np.ndarray:
    """Coerce a Series-like to float ndarray; non-numeric become NaN upstream."""
    arr = np.asarray(series)
    try:
        return np.array(arr, dtype=float)
    except Exception:
        import pandas as pd  # local import to keep top clean
        return pd.to_numeric(series, errors="coerce").to_numpy()


# ------------------------------------
# Core: Flexible contour layer builder
# ------------------------------------
StyleDict = Dict[str, Any]
StyleFunc = Callable[[dict], StyleDict]  # f(feature) -> style dict


def contours(
    gdf: gpd.GeoDataFrame,
    *,
    name: Optional[str] = "Contours",
    level_column: str = "depth",
    # --- filtering options (pick one or combine) ---
    spacing: Optional[float] = 100.0,
    spacing_offset: float = 0.0,
    tolerance: float = 1e-6,
    levels: Optional[Iterable[float]] = None,
    predicate: Optional[Callable[[float], bool]] = None,
    # --- CRS handling ---
    reproject_to_wgs84: bool = True,
    # --- folium layer control & placement ---
    group: Optional[Union[folium.Map, folium.FeatureGroup]] = None,
    control_name: Optional[str] = None,  # if None, uses `name`
    display_pane: str = "overlayPane",
    interactive_pane: str = "overlayPane",
    # --- display styling (thin, visible lines) ---
    style: Optional[StyleDict] = None,
    style_function: Optional[StyleFunc] = None,
    highlight_function: Optional[StyleFunc] = None,
    # --- interactive styling (fat, invisible hit area) ---
    interactive: bool = True,
    interactive_style: Optional[StyleDict] = None,
    interactive_weight: int = 10,
    interactive_opacity: float = 0.0,
    interactive_class: str = "no-focus",
    # --- popup / tooltip (either pass fields/aliases or full Folium objects) ---
    popup_fields: Optional[Sequence[str]] = None,
    popup_aliases: Optional[Sequence[str]] = None,
    popup: Optional[folium.Popup] = None,
    tooltip_fields: Optional[Sequence[str]] = None,
    tooltip_aliases: Optional[Sequence[str]] = None,
    tooltip: Optional[folium.Tooltip] = None,
    # Optional geometry simplification (server-side before serializing)
    simplify_tolerance: Optional[float] = None,
    simplify_preserve_topology: bool = True,
    # --- CSS injection for interactive layer ---
    add_css: bool = True,
    css_text: Optional[str] = None,
    # --- misc GeoJson kwargs for both layers (e.g., show=False, zoom_on_click=False) ---
    **geojson_kwargs,
) -> dict:
    """
    Create Folium GeoJson layers for contour lines with rich filtering, styling, and UX.

    The function generates:
      1) a thin, visible **display layer** (listed in LayerControl), and
      2) an optional thick but invisible **interactive layer** (not listed) that
         provides generous hit areas for clicks/hover (popups/tooltips).

    Filtering (applies to `level_column`, which must be numeric):
      - `spacing`: keep contours at regular intervals (e.g., every 100 units), with
        optional `spacing_offset` (e.g., keep 50, 150, 250 by using spacing=100 & offset=50).
      - `levels`: keep only specific values (with absolute `tolerance`).
      - `predicate(level) -> bool`: final custom test (ANDed with the others).

    If multiple filters are provided, they are **ANDed**.

    CRS:
      - If `reproject_to_wgs84=True` and `gdf.crs` is set and not EPSG:4326, a
        copy is reprojected to EPSG:4326 (required by Leaflet/Folium).
      - If `gdf.crs` is missing and coordinates are already lon/lat, set `reproject_to_wgs84=False`.

    Styling:
      - Provide either a constant `style` dict or a `style_function(feature)` for dynamic styling.
      - `highlight_function(feature)` can adjust hover appearance on the display layer.
      - The interactive layer style is built from `interactive_*` params unless you pass
        a full `interactive_style` dict.

    Popups/Tooltips:
      - Pass `popup_fields`/`popup_aliases` or supply a ready Folium `popup`.
      - Pass `tooltip_fields`/`tooltip_aliases` or supply a ready Folium `tooltip`.

    CSS:
      - If `interactive=True` and `add_css=True`, a small `<style>` block is injected once
        into the page (when `group` is provided) to remove focus outlines for the
        interactive layer class (defaults to `.no-focus`). Override with `css_text`.

    Parameters
    ----------
    gdf : GeoDataFrame
        LineString/MultiLineString contours. Must contain `level_column`.
    name : str, default "Contours"
        Display name for the visible layer (LayerControl label).
    level_column : str, default "depth"
        Column containing numeric levels (e.g., depth/elevation).
    spacing : float, optional
        Keep levels that satisfy the modulo rule within `tolerance`. Set to None to disable.
    spacing_offset : float, default 0.0
        Offset for modulo test (see description above).
    tolerance : float, default 1e-6
        Absolute tolerance used in spacing and levels checks.
    levels : Iterable[float], optional
        Explicit set/list of contour values to keep (within `tolerance`).
    predicate : Callable[[float], bool], optional
        Custom inclusion test evaluated last (ANDed).
    reproject_to_wgs84 : bool, default True
        Reproject to EPSG:4326 if GeoDataFrame CRS indicates a different CRS.
    group : folium.Map | folium.FeatureGroup, optional
        If provided, layers are added to this object; otherwise returned unattached.
    control_name : str, optional
        Custom label for LayerControl (defaults to `name`).
    display_pane : str, default "overlayPane"
        Leaflet pane for the visible layer.
    interactive_pane : str, default "overlayPane"
        Leaflet pane for the interactive layer.
    style : dict, optional
        Static style dict for the visible layer.
    style_function : Callable[[feature], dict], optional
        Dynamic style function for the visible layer (wins over `style`).
    highlight_function : Callable[[feature], dict], optional
        Hover style function for the visible layer.
    interactive : bool, default True
        Whether to create the invisible, thick interactive layer.
    interactive_style : dict, optional
        Full style dict for the interactive layer; if omitted, built from params below.
    interactive_weight : int, default 10
        Stroke weight in pixels for the interactive layer (bigger => easier to click).
    interactive_opacity : float, default 0.0
        Opacity for the interactive stroke (0 = invisible but still interactive).
    interactive_class : str, default "no-focus"
        Class added to interactive paths (useful for CSS targeting).
    popup_fields, popup_aliases, popup, tooltip_fields, tooltip_aliases, tooltip :
        Popup/tooltip configuration (see description above).
    simplify_tolerance : float, optional
        If given (units of layer CRS / degrees if already 4326), geometries are
        simplified on the server prior to serialization to reduce payload size.
    simplify_preserve_topology : bool, default True
        Preserve topology when simplifying (recommended for lines).
    add_css : bool, default True
        Inject a `<style>` block once to remove focus outlines for `interactive_class`.
        Only effective if `group` is provided.
    css_text : str, optional
        Custom CSS text to inject instead of the default.
    **geojson_kwargs :
        Extra kwargs passed to both Folium GeoJson layers (e.g., show=False, smooth_factor=0).

    Returns
    -------
    dict
        {
          "display": folium.GeoJson,          # thin, visible layer (in LayerControl)
          "interactive": folium.GeoJson|None, # fat, invisible hit layer (not in control)
          "group": folium.FeatureGroup|None   # same object you passed via `group`
        }
    """
    if level_column not in gdf.columns:
        raise ValueError(
            f"`level_column='{level_column}'` not found in columns: {list(gdf.columns)}"
        )

    # Reproject if requested and CRS indicates it's needed
    gdf_work = gdf
    if reproject_to_wgs84:
        try:
            if gdf.crs is not None and str(gdf.crs).lower() not in {"epsg:4326", "epsg:4326:84", "wgs84"}:
                gdf_work = gdf.to_crs(epsg=4326)
        except Exception as e:
            raise ValueError(f"CRS reprojection to EPSG:4326 failed: {e}") from e

    # Ensure numeric levels
    levels_series = _to_numeric(gdf_work[level_column])

    # Build mask using all provided filters
    mask = np.ones(len(gdf_work), dtype=bool)

    if spacing is not None:
        mod = np.mod(levels_series - spacing_offset, spacing)
        spacing_hit = (np.isclose(mod, 0.0, atol=tolerance)) | np.isclose(spacing - mod, 0.0, atol=tolerance)
        mask &= spacing_hit

    if levels is not None:
        lv = np.asarray(list(levels), dtype=float)
        dist = np.min(np.abs(levels_series[:, None] - lv[None, :]), axis=1)
        mask &= dist <= tolerance

    if predicate is not None:
        pred_mask = np.fromiter((bool(predicate(v)) for v in levels_series), count=len(levels_series), dtype=bool)
        mask &= pred_mask

    gdf_filtered = gdf_work.loc[mask].copy()

    # Default styles if none provided
    if style_function is None and style is None:
        style = {"color": "black", "weight": 0.6, "opacity": 0.7}

    # optional simplification before reprojection (cheaper in native CRS)
    if simplify_tolerance is not None and not gdf.empty:
        gdf = gdf.copy()
        gdf["geometry"] = gdf.geometry.simplify(simplify_tolerance, preserve_topology=simplify_preserve_topology)

    display_layer = folium.GeoJson(
        data=gdf_filtered.__geo_interface__,
        name=(control_name or name or ""),
        pane=display_pane,
        control=True,  # visible layer appears in LayerControl
        style_function=(style_function or (lambda f, _style=style: _style)),
        highlight_function=highlight_function,
        **geojson_kwargs,
    )

    interactive_layer = None
    if interactive:
        # Build popup/tooltip if fields are provided (unless custom objects passed)
        popup_obj = (
            popup
            if popup is not None
            else (folium.GeoJsonPopup(fields=list(popup_fields), aliases=list(popup_aliases or []))
                  if popup_fields else None)
        )

        tooltip_obj = (
            tooltip
            if tooltip is not None
            else (folium.GeoJsonTooltip(fields=list(tooltip_fields),
                                        aliases=list(tooltip_aliases or []),
                                        sticky=True, direction="top")
                  if tooltip_fields else None)
        )

        if interactive_style is None:
            interactive_style = {
                "color": "#000000",
                "weight": interactive_weight,
                "opacity": interactive_opacity,
                "className": interactive_class,
            }

        interactive_layer = folium.GeoJson(
            data=gdf_filtered.__geo_interface__,
            name=None,  # keep LayerControl clean
            pane=interactive_pane,
            control=False,
            style_function=lambda f, _s=interactive_style: _s,
            popup=popup_obj,
            tooltip=tooltip_obj,
            popup_keep_highlighted=False if popup_obj is None else True,
            **geojson_kwargs,
        )

    # Attach to target map/group if provided
    if group is not None:
        display_layer.add_to(group)
        if interactive_layer is not None:
            interactive_layer.add_to(group)
        # Inject CSS once (idempotent)
        if interactive:
            _maybe_inject_contour_css(
                group=group,
                interactive_class=interactive_class,
                add_css=add_css,
                css_text=css_text,
            )

    return {"display": display_layer, "interactive": interactive_layer, "group": group}


# ----------------------------------------------------
# (Optional) Quick usage example — delete if not needed
# ----------------------------------------------------
if __name__ == "__main__":
    # This block is safe to remove. It shows how you'd call the function.
    # Requires you to have a GeoDataFrame `gdf` with a 'depth' column.
    #
    # Example:
    #   m = folium.Map(location=[40.4, 49.8], zoom_start=9)
    #   layers = contours(
    #       gdf,
    #       name="Depth Contours",
    #       level_column="depth",
    #       spacing=100,
    #       levels=[500],  # also keep 500 explicitly
    #       interactive=True,
    #       popup_fields=["depth"],
    #       popup_aliases=["Contour:"],
    #       group=m,
    #       show=False,            # via **geojson_kwargs
    #       smooth_factor=0.0,     # via **geojson_kwargs
    #   ).add_to(m)
    #   m.save("contours.html")
    pass

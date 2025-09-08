from __future__ import annotations

from typing import Optional, List, Tuple, Any, Dict
import html
import math

import folium
from folium.features import DivIcon
import pandas as pd

def wells(
    frame: pd.DataFrame,
    *,
    label_group: Optional[folium.FeatureGroup] = None,
    point_group: Optional[folium.FeatureGroup] = None,
    label_pane: str = "overlayPane",
    point_pane: str = "overlayPane",
    units: Optional[Dict[str, str]] = None,
) -> Tuple[List[folium.CircleMarker], List[folium.Marker]]:
    """
    Add well points (CircleMarker) and text labels (DivIcon) for each row of a fixed-schema DataFrame.

    Expected DataFrame columns (fixed; no *_col parameters):
        - well : str                         (name/identifier)
        - date : datetime64/str/None         (last operation date)
        - field : str
        - formation : str
        - orate : float
        - wrate : float
        - grate : float
        - lat : float                        (WGS84 latitude)
        - lon : float                        (WGS84 longitude)
        - color : str                        (CSS color for point stroke/fill)
        - fill_opacity : float               (0..1)
        - radius : float                     (point radius, optional; if missing, defaults to 5)

    What it does
    ------------
    - Creates a `folium.CircleMarker` for each valid row (finite lat/lon).
    - Builds a **safe** HTML popup per your template:
        <b>{well}</b><br/>
        Last Operation Date: {date_dd-mm-YYYY or 'N/A'}<br/>
        Field-Formation: {field}-{formation}<br/>
        Cum. Oil: {orate:.1f} {units['orate']}<br/>
        Cum. Water: {wrate:.1f} {units['wrate']}<br/>
        Cum. Gas: {grate:.1f} {units['grate']}<br/>
      All values are HTML-escaped; missing/NaN handled gracefully.
    - Adds a text label (DivIcon) with the well name at the same coordinate.
    - Adds points to `point_group` and labels to `label_group` if provided.
    - Returns the list of point markers and label markers.

    Parameters
    ----------
    frame : pd.DataFrame
        Table with the fixed columns described above.
    label_group, point_group : folium.FeatureGroup, optional
        Target groups to attach the created markers. If omitted, layers are returned unattached.
    label_pane, point_pane : str
        Leaflet pane names for z-ordering.
    units : dict, optional
        Units to append in the popup for cumulative metrics, e.g.
        {"orate": " bbl", "wrate": " bbl", "grate": " m³"}.
        Missing keys default to "" (no unit).

    Returns
    -------
    (points, labels) : Tuple[List[folium.CircleMarker], List[folium.Marker]]
        The created point markers and label markers.
    """

    units = dict(units or {})

    def _is_nan(v: Any) -> bool:
        return v is None or (isinstance(v, float) and math.isnan(v))

    def _safe_text(v: Any) -> str:
        return "" if _is_nan(v) else html.escape(str(v), quote=True)

    def _fmt_date(v: Any) -> str:
        if pd.isna(v):
            return "N/A"
        # datetime-like: prefer strftime
        try:
            if hasattr(v, "strftime"):
                return html.escape(v.strftime("%d-%m-%Y"), quote=True)
        except Exception:
            pass
        # fallback: stringify and escape
        s = str(v).strip()
        return html.escape(s, quote=True) if s else "N/A"

    def _fmt_num(v: Any) -> str:
        """Format numeric value as 'x.x' or '' if missing/NaN/not a number."""
        if _is_nan(v):
            return ""
        try:
            return f"{float(v):.1f}"
        except Exception:
            return ""

    def _unit(key: str) -> str:
        # ensure the unit text itself is escaped (paranoia)
        return html.escape(units.get(key, "") or "", quote=True)

    points: List[folium.CircleMarker] = []
    labels: List[folium.Marker] = []

    # iterate rows using itertuples for speed while keeping attribute access
    for r in frame.itertuples(index=False):
        lat = getattr(r, "lat", None)
        lon = getattr(r, "lon", None)
        if _is_nan(lat) or _is_nan(lon):
            continue

        # Safe building blocks
        well = _safe_text(getattr(r, "well", ""))
        date_html = _fmt_date(getattr(r, "date", None))
        field_html = _safe_text(getattr(r, "field", ""))
        formation_html = _safe_text(getattr(r, "formation", ""))
        platform_html = _safe_text(getattr(r, "platform", ""))

        oil_val = _fmt_num(getattr(r, "orate", None))
        wtr_val = _fmt_num(getattr(r, "wrate", None))
        gas_val = _fmt_num(getattr(r, "grate", None))

        oil_unit = _unit("orate")
        wtr_unit = _unit("wrate")
        gas_unit = _unit("grate")

        # Assemble safe popup HTML (only show value+unit if value is non-empty)
        popup_lines = [
            f"<b>{well}</b><br/>",
            f"Field-Platform: {field_html}-{platform_html}<br/>",
            f"Last Record Date: {date_html}<br/>",
            f"{formation_html} Daily Oil Rate: {oil_val}{(' ' + oil_unit) if oil_val else ''}<br/>",
            f"{formation_html} Daily Water Rate: {wtr_val}{(' ' + wtr_unit) if wtr_val else ''}<br/>",
            f"{formation_html} Daily Gas Rate: {gas_val}{(' ' + gas_unit) if gas_val else ''}<br/>",
        ]
        popup_html = "".join(popup_lines)

        # Marker styling with sensible fallbacks
        color = getattr(r, "color", "#22c55e")
        fill_opacity = getattr(r, "fill_opacity", None)
        radius = getattr(r, "radius", None)

        point = folium.CircleMarker(
            location=[float(lat), float(lon)],
            radius=(5 if _is_nan(radius) else float(radius)),
            weight=0,
            color=(color if isinstance(color, str) and color else "#22c55e"),
            pane=point_pane,
            fill=True,
            fill_opacity=(0.85 if _is_nan(fill_opacity) else float(fill_opacity)),
        ).add_child(
            folium.Popup(popup_html, max_width=300)
        )

        point.options.update({"title": well})

        if point_group is not None:
            point.add_to(point_group)
        points.append(point)

        # Text label (DivIcon) with safe content
        label_html = f'<div class="well-label-div">{well}</div>'
        label = folium.Marker(
            [float(lat), float(lon)],
            pane=label_pane,
            icon=DivIcon(
                icon_size=(1, 1),
                icon_anchor=(0, 0),
                html=label_html,
            ),
        )
        if label_group is not None:
            label.add_to(label_group)
        labels.append(label)

    return points, labels

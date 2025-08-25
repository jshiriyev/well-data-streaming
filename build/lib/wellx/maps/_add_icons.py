import math

from html import escape as _escape
from typing import Optional

from folium import Marker
from folium.features import DivIcon

def platform(
    lat: float,
    lon: float,
    width: int = 40,
    height: int = 18,
    angle_deg: float = 45,
    fill: str = "#22c55e",
    border: str = "#111",
    border_px: int = 2,
    *,
    corner_radius: int = 0,
    label: Optional[str] = None,
    label_color: str = "#111",
    label_size_px: int = 12,
    label_bold: bool = False,
    class_name: str = "",
    **kwargs,
) -> Marker:
    """
    Create a Folium marker that renders as a rotated rectangular badge (DivIcon).

    The rectangle's pixel size remains constant regardless of map zoom.
    The marker is anchored at its center to the given latitude/longitude.

    Args:
        lat, lon: Geographic coordinates of the marker (WGS84).
        width: Rectangle width in pixels.
        height: Rectangle height in pixels.
        angle_deg: Rotation angle in degrees (clockwise, CSS-style).
        fill: CSS color for the rectangle fill (e.g., "#22c55e", "rgba(…)", "red").
        border: CSS color for the rectangle border.
        border_px: Border thickness in pixels.

        corner_radius: Optional rounded corner radius in pixels (CSS border-radius).
        label: Optional text label drawn on top of the rectangle.
        label_color: CSS color for the label text.
        label_size_px: Font size (pixels) for the label.
        label_bold: If True, render label in bold.
        class_name: Optional CSS class to add to the DivIcon root element.

        **kwargs: Passed through to `folium.Marker` (e.g., `z_index_offset=`, `draggable=`).

    Returns:
        folium.Marker: A marker ready to `.add_to(map_or_group)`.

    Raises:
        ValueError: If width/height are not positive.

    """
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive integers.")

    # Normalize angle to [0, 360)
    angle = float(angle_deg) % 360.0
    a = math.radians(angle)

    # Bounding box of the rotated rectangle so the inner <div> doesn’t get clipped
    Wc = int(round(abs(width * math.cos(a)) + abs(height * math.sin(a))))
    Hc = int(round(abs(width * math.sin(a)) + abs(height * math.cos(a))))

    # Optional label HTML (escaped to be safe)
    label_html = ""
    if label is not None:
        weight = "700" if label_bold else "400"
        label_html = f"""
          <div style="
            position:absolute;top:50%;left:50%;
            transform: translate(-50%,-50%) rotate({angle}deg);
            transform-origin:center center;
            font-size:{int(label_size_px)}px;
            color:{_escape(label_color)};
            font-weight:{weight};
            white-space:nowrap;
            pointer-events:none;">
            {_escape(str(label))}
          </div>
        """

    # Inner rectangle (rotated), centered within a larger, unrotated container
    rect_html = f"""
      <div style="
        position:absolute;top:50%;left:50%;
        width:{int(width)}px;height:{int(height)}px;
        transform: translate(-50%,-50%) rotate({angle}deg);
        transform-origin:center center;
        background:{_escape(fill)};
        border:{int(border_px)}px solid {_escape(border)};
        border-radius:{int(corner_radius)}px;
        box-sizing:border-box;">
      </div>
    """

    outer_html = f"""
    <div class="{_escape(class_name)}" style="position:relative;width:{Wc}px;height:{Hc}px;">
      {rect_html}
      {label_html}
    </div>
    """

    icon = DivIcon(html=outer_html, icon_size=(Wc, Hc), icon_anchor=(Wc // 2, Hc // 2))

    return Marker([lat, lon], icon=icon, **kwargs)
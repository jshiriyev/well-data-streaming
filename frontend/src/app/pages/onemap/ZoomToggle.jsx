import { useEffect } from "react";

function resolveLeaflet(explicitLeaflet) {
  if (explicitLeaflet) return explicitLeaflet;
  if (typeof window !== "undefined" && window.L) return window.L;
  return null;
}

export function ZoomToggle({
  map,
  layer,
  parentLayer = null,
  minZoom = 16,
  leaflet,
}) {
  useEffect(() => {
    const L = resolveLeaflet(leaflet);
    if (!L || !map || !layer) return;

    const refresh = () => {
      const zoomOk = map.getZoom() >= minZoom;
      const parentOk = parentLayer ? map.hasLayer(parentLayer) : true;
      const shouldShow = zoomOk && parentOk;

      if (shouldShow) {
        if (!map.hasLayer(layer)) map.addLayer(layer);
      } else if (map.hasLayer(layer)) {
        map.removeLayer(layer);
      }
    };

    map.on("zoomend", refresh);
    map.on("overlayadd", refresh);
    map.on("overlayremove", refresh);
    refresh();

    return () => {
      map.off("zoomend", refresh);
      map.off("overlayadd", refresh);
      map.off("overlayremove", refresh);
    };
  }, [map, layer, parentLayer, minZoom, leaflet]);

  return null;
}

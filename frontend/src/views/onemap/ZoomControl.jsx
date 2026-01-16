import { useEffect } from "react";

function resolveLeaflet(explicitLeaflet) {
  if (explicitLeaflet) return explicitLeaflet;
  if (typeof window !== "undefined" && window.L) return window.L;
  return null;
}

export function ZoomControl({
  map,
  position = "topright",
  options = {},
  leaflet,
}) {
  useEffect(() => {
    const L = resolveLeaflet(leaflet);
    if (!L || !map) return;

    const control = L.control.zoom({ ...options, position });
    control.addTo(map);

    return () => {
      control.remove();
    };
  }, [map, position, options, leaflet]);

  return null;
}

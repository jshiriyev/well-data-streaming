import { useEffect } from "react";

function resolveLeaflet(explicitLeaflet) {
  if (explicitLeaflet) return explicitLeaflet;
  if (typeof window !== "undefined" && window.L) return window.L;
  return null;
}

function isCircleMarker(layer, L) {
  if (!layer) return false;
  if (L?.CircleMarker && layer instanceof L.CircleMarker) return true;
  return Boolean(layer.options && typeof layer.options.radius === "number");
}

export function HaloHover({
  map,
  layer,
  color = "#111",
  weight = 1,
  opacity = 1,
  pad = 4,
  leaflet,
}) {
  useEffect(() => {
    const L = resolveLeaflet(leaflet);
    if (!L || !map || !layer) return;

    const halo = L.circleMarker([0, 0], {
      radius: 8,
      color,
      weight,
      opacity,
      fill: false,
      interactive: false,
    });

    const listeners = new Map();

    const bindHover = (targetLayer) => {
      if (!targetLayer?.on) return;

      const onOver = (event) => {
        const radius =
          targetLayer?.options && typeof targetLayer.options.radius === "number"
            ? targetLayer.options.radius
            : 5;
        halo.setLatLng(event.latlng);
        halo.setStyle({ radius: radius + pad });
        if (!map.hasLayer(halo)) halo.addTo(map);
      };

      const onOut = () => {
        if (map.hasLayer(halo)) map.removeLayer(halo);
      };

      targetLayer.on("mouseover", onOver);
      targetLayer.on("mouseout", onOut);
      listeners.set(targetLayer, { onOver, onOut });
    };

    const visitLayer = (current) => {
      if (!current) return;
      if (isCircleMarker(current, L)) {
        bindHover(current);
      } else if (typeof current.eachLayer === "function") {
        current.eachLayer(visitLayer);
      }
    };

    visitLayer(layer);

    return () => {
      listeners.forEach((handlers, targetLayer) => {
        targetLayer.off("mouseover", handlers.onOver);
        targetLayer.off("mouseout", handlers.onOut);
      });
      if (map.hasLayer(halo)) map.removeLayer(halo);
    };
  }, [map, layer, color, weight, opacity, pad, leaflet]);

  return null;
}

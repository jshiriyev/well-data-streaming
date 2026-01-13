import { useEffect, useMemo } from "react";

function resolveLeaflet(explicitLeaflet) {
  if (explicitLeaflet) return explicitLeaflet;
  if (typeof window !== "undefined" && window.L) return window.L;
  return null;
}

function normalizeLayers(layers) {
  if (!layers) return [];
  if (Array.isArray(layers)) {
    return layers
      .map((entry) => {
        if (Array.isArray(entry)) {
          return { label: String(entry[0]), layer: entry[1] };
        }
        if (entry && typeof entry === "object") {
          return { label: String(entry.label), layer: entry.layer };
        }
        return null;
      })
      .filter(Boolean);
  }
  if (typeof layers === "object") {
    return Object.entries(layers).map(([label, layer]) => ({
      label: String(label),
      layer,
    }));
  }
  return [];
}

function normalizeMinSize(minSize) {
  if (!minSize) return { minWidth: null, minHeight: null };
  if (Array.isArray(minSize)) {
    return {
      minWidth: Number.isFinite(minSize[0]) ? minSize[0] : null,
      minHeight: Number.isFinite(minSize[1]) ? minSize[1] : null,
    };
  }
  if (typeof minSize === "object") {
    return {
      minWidth: Number.isFinite(minSize.width) ? minSize.width : null,
      minHeight: Number.isFinite(minSize.height) ? minSize.height : null,
    };
  }
  return { minWidth: null, minHeight: null };
}

export function LayerControl({
  map,
  layers,
  position = "topright",
  minSize,
  leaflet,
}) {
  const normalizedLayers = useMemo(() => normalizeLayers(layers), [layers]);
  const { minWidth, minHeight } = useMemo(
    () => normalizeMinSize(minSize),
    [minSize]
  );

  useEffect(() => {
    const L = resolveLeaflet(leaflet);
    if (!L || !map || normalizedLayers.length === 0) return;

    let selectEl = null;
    let handleChange = null;

    const Control = L.Control.extend({
      options: { position },
      onAdd: function onAdd() {
        const container = L.DomUtil.create("div", "leaflet-bar");
        container.style.background = "white";
        container.style.padding = "6px";
        container.style.boxShadow = "0 1px 4px rgba(0,0,0,0.3)";
        container.style.borderRadius = "6px";
        container.style.display = "flex";
        container.style.alignItems = "center";
        container.style.zIndex = "1000";
        if (minWidth) container.style.minWidth = `${minWidth}px`;
        if (minHeight) container.style.minHeight = `${minHeight}px`;

        selectEl = L.DomUtil.create("select", "", container);
        selectEl.style.border = "none";
        selectEl.style.outline = "none";
        selectEl.style.padding = "4px 6px";
        selectEl.style.font = "14px/1.2 sans-serif";
        selectEl.style.background = "transparent";

        normalizedLayers.forEach(({ label }) => {
          const option = document.createElement("option");
          option.value = label;
          option.textContent = label;
          selectEl.appendChild(option);
        });

        const switchLayer = (label) => {
          normalizedLayers.forEach(({ layer: target }) => {
            if (target && map.hasLayer(target)) map.removeLayer(target);
          });
          const next = normalizedLayers.find((item) => item.label === label);
          if (next?.layer) map.addLayer(next.layer);
        };

        handleChange = (event) => {
          switchLayer(event.target.value);
        };
        selectEl.addEventListener("change", handleChange);

        if (selectEl.options.length) {
          const initial = selectEl.options[0].value;
          selectEl.value = initial;
          switchLayer(initial);
        }

        L.DomEvent.disableClickPropagation(container);
        L.DomEvent.disableScrollPropagation(container);
        return container;
      },
    });

    const control = new Control();
    control.addTo(map);

    return () => {
      if (selectEl && handleChange) {
        selectEl.removeEventListener("change", handleChange);
      }
      map.removeControl(control);
    };
  }, [map, leaflet, position, minWidth, minHeight, normalizedLayers]);

  return null;
}

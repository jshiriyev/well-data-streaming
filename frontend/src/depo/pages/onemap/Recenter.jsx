import { useEffect, useMemo } from "react";

const MODERN_STYLE = `
.leaflet-control-recenter {
  background: transparent;
  border: 0;
  box-shadow: none;
  margin: 6px;
}
.leaflet-control-recenter .recenter-btn {
  --rc-size: 36px;
  --rc-bg: rgba(28, 28, 30, 0.88);
  --rc-bg-hover: rgba(28, 28, 30, 0.96);
  --rc-color: #fff;
  width: var(--rc-size);
  height: var(--rc-size);
  display: grid;
  place-items: center;
  border-radius: 9999px;
  background: var(--rc-bg);
  color: var(--rc-color);
  text-decoration: none;
  line-height: 0;
  cursor: pointer;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.32), inset 0 0 0 1px rgba(255, 255, 255, 0.12);
  transition: transform 0.15s ease, box-shadow 0.15s ease, background-color 0.15s ease, opacity 0.15s ease;
  -webkit-tap-highlight-color: transparent;
}
.leaflet-control-recenter .recenter-btn svg {
  width: 18px;
  height: 18px;
  display: block;
}
.leaflet-control-recenter .recenter-btn:hover {
  transform: scale(1.08);
  background: var(--rc-bg-hover);
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.38), inset 0 0 0 1px rgba(255, 255, 255, 0.18);
}
.leaflet-control-recenter .recenter-btn:active {
  transform: scale(0.98);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.45) inset;
}
.leaflet-control-recenter .recenter-btn:focus-visible {
  outline: 2px solid #60a5fa;
  outline-offset: 2px;
}
`;

function resolveLeaflet(explicitLeaflet) {
  if (explicitLeaflet) return explicitLeaflet;
  if (typeof window !== "undefined" && window.L) return window.L;
  return null;
}

function ensureStyleTag(id, cssText) {
  if (!cssText) return;
  let styleTag = document.getElementById(id);
  if (!styleTag) {
    styleTag = document.createElement("style");
    styleTag.id = id;
    styleTag.textContent = cssText;
    document.head.appendChild(styleTag);
  } else if (styleTag.textContent !== cssText) {
    styleTag.textContent = cssText;
  }
}

function removeStyleTag(id) {
  const styleTag = document.getElementById(id);
  if (styleTag?.parentNode) styleTag.parentNode.removeChild(styleTag);
}

function buildClassicControl(L, map, { lat, lon, zoom }) {
  const container = L.DomUtil.create("div", "leaflet-bar leaflet-control");
  const button = L.DomUtil.create("a", "", container);
  button.innerHTML = "&#8635;";
  button.title = "Re-center";
  button.href = "#";

  button.style.width = "30px";
  button.style.height = "30px";
  button.style.lineHeight = "30px";
  button.style.textAlign = "center";
  button.style.fontSize = "16px";
  button.style.textDecoration = "none";
  button.style.backgroundColor = "white";
  button.style.color = "black";
  button.style.display = "block";
  button.style.borderBottom = "1px solid #ccc";

  button.onmouseover = function onMouseOver() {
    this.style.backgroundColor = "#f4f4f4";
  };
  button.onmouseout = function onMouseOut() {
    this.style.backgroundColor = "white";
  };

  button.setAttribute("role", "button");
  button.setAttribute("aria-label", "Re-center map");
  button.setAttribute("tabindex", "0");

  const recenter = (event) => {
    if (event) L.DomEvent.stop(event);
    map.setView([lat, lon], zoom);
  };

  L.DomEvent.disableClickPropagation(container);
  L.DomEvent.disableScrollPropagation(container);
  L.DomEvent.on(button, "click", recenter);
  L.DomEvent.on(button, "keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") recenter(event);
  });

  return container;
}

function buildModernControl(L, map, { lat, lon, zoom }) {
  const container = L.DomUtil.create("div", "leaflet-control leaflet-control-recenter");
  const button = L.DomUtil.create("a", "recenter-btn", container);
  button.href = "#";
  button.title = "Re-center";
  button.setAttribute("role", "button");
  button.setAttribute("aria-label", "Re-center map");

  button.innerHTML = `
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="2"/>
      <path d="M12 4v3 M12 17v3 M4 12h3 M17 12h3" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/>
    </svg>
  `;

  const recenter = (event) => {
    if (event) L.DomEvent.stop(event);
    map.setView([lat, lon], zoom);
  };

  L.DomEvent.disableClickPropagation(container);
  L.DomEvent.disableScrollPropagation(container);
  L.DomEvent.on(button, "click", recenter);
  L.DomEvent.on(button, "keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") recenter(event);
  });

  return container;
}

export function Recenter({
  map,
  lat,
  lon,
  zoom,
  position = "bottomleft",
  variant = "classic",
  styleCss = "",
  leaflet,
}) {
  const styleId = useMemo(
    () => `recenter-style-${Math.random().toString(36).slice(2)}`,
    []
  );

  useEffect(() => {
    const L = resolveLeaflet(leaflet);
    if (!L || !map) return;

    if (variant === "modern") {
      const css = [MODERN_STYLE.trim(), styleCss.trim()].filter(Boolean).join("\n");
      ensureStyleTag(styleId, css);
    }

    const Control = L.Control.extend({
      options: { position },
      onAdd: function onAdd() {
        return variant === "modern"
          ? buildModernControl(L, map, { lat, lon, zoom })
          : buildClassicControl(L, map, { lat, lon, zoom });
      },
    });

    const control = new Control();
    control.addTo(map);

    return () => {
      map.removeControl(control);
      if (variant === "modern") removeStyleTag(styleId);
    };
  }, [map, lat, lon, zoom, position, variant, styleCss, leaflet, styleId]);

  return null;
}

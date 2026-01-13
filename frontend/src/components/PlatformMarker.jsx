import { useEffect } from "react";

const DEFAULTS = {
  width: 40,
  height: 18,
  angleDeg: 45,
  fill: "#22c55e",
  border: "#111",
  borderPx: 2,
  cornerRadius: 0,
  label: null,
  labelColor: "#111",
  labelSizePx: 12,
  labelBold: false,
  className: "",
  wrapperClassName: "",
};

function resolveLeaflet(explicitLeaflet) {
  if (explicitLeaflet) return explicitLeaflet;
  if (typeof window !== "undefined" && window.L) return window.L;
  return null;
}

function normalizeAngle(angleDeg) {
  const raw = Number.isFinite(angleDeg) ? angleDeg : 0;
  return ((raw % 360) + 360) % 360;
}

function assertPositiveSize(width, height) {
  const widthOk = Number.isFinite(width) && width > 0;
  const heightOk = Number.isFinite(height) && height > 0;
  if (!widthOk || !heightOk) {
    throw new Error("width and height must be positive numbers.");
  }
}

function buildPlatformElements(options) {
  const {
    width,
    height,
    angleDeg,
    fill,
    border,
    borderPx,
    cornerRadius,
    label,
    labelColor,
    labelSizePx,
    labelBold,
    className,
  } = options;

  assertPositiveSize(width, height);

  const angle = normalizeAngle(angleDeg);
  const radians = (angle * Math.PI) / 180;

  const containerWidth = Math.round(
    Math.abs(width * Math.cos(radians)) + Math.abs(height * Math.sin(radians))
  );
  const containerHeight = Math.round(
    Math.abs(width * Math.sin(radians)) + Math.abs(height * Math.cos(radians))
  );

  const outer = document.createElement("div");
  if (className) outer.className = className;
  outer.style.position = "relative";
  outer.style.width = `${containerWidth}px`;
  outer.style.height = `${containerHeight}px`;

  const rect = document.createElement("div");
  rect.style.position = "absolute";
  rect.style.top = "50%";
  rect.style.left = "50%";
  rect.style.width = `${width}px`;
  rect.style.height = `${height}px`;
  rect.style.transform = `translate(-50%, -50%) rotate(${angle}deg)`;
  rect.style.transformOrigin = "center center";
  rect.style.background = fill;
  rect.style.border = `${borderPx}px solid ${border}`;
  rect.style.borderRadius = `${cornerRadius}px`;
  rect.style.boxSizing = "border-box";
  outer.appendChild(rect);

  if (label !== null && label !== undefined) {
    const labelDiv = document.createElement("div");
    labelDiv.style.position = "absolute";
    labelDiv.style.top = "50%";
    labelDiv.style.left = "50%";
    labelDiv.style.transform = `translate(-50%, -50%) rotate(${angle}deg)`;
    labelDiv.style.transformOrigin = "center center";
    labelDiv.style.fontSize = `${labelSizePx}px`;
    labelDiv.style.color = labelColor;
    labelDiv.style.fontWeight = labelBold ? "700" : "400";
    labelDiv.style.whiteSpace = "nowrap";
    labelDiv.style.pointerEvents = "none";
    labelDiv.textContent = String(label);
    outer.appendChild(labelDiv);
  }

  return {
    html: outer,
    size: [containerWidth, containerHeight],
    anchor: [Math.floor(containerWidth / 2), Math.floor(containerHeight / 2)],
  };
}

export function createPlatformIcon(userOptions = {}, explicitLeaflet) {
  const L = resolveLeaflet(explicitLeaflet);
  if (!L) {
    throw new Error("Leaflet is not available. Pass `leaflet` or load it globally.");
  }

  const options = { ...DEFAULTS, ...userOptions };
  const { html, size, anchor } = buildPlatformElements(options);

  return L.divIcon({
    html,
    iconSize: size,
    iconAnchor: anchor,
    className: options.wrapperClassName || "",
  });
}

export function createPlatformMarker(userOptions = {}) {
  const {
    leaflet,
    map,
    layer,
    lat,
    lon,
    lng,
    markerOptions = {},
    ...iconOptions
  } = userOptions;

  const L = resolveLeaflet(leaflet);
  if (!L) {
    throw new Error("Leaflet is not available. Pass `leaflet` or load it globally.");
  }

  const longitude = lon ?? lng;
  if (!Number.isFinite(lat) || !Number.isFinite(longitude)) {
    throw new Error("lat and lon (or lng) must be valid numbers.");
  }

  const icon = createPlatformIcon(iconOptions, L);
  const marker = L.marker([lat, longitude], { ...markerOptions, icon });

  if (layer) {
    marker.addTo(layer);
  } else if (map) {
    marker.addTo(map);
  }

  return marker;
}

export function PlatformMarker({
  leaflet,
  map,
  layer,
  lat,
  lon,
  lng,
  width = DEFAULTS.width,
  height = DEFAULTS.height,
  angleDeg = DEFAULTS.angleDeg,
  fill = DEFAULTS.fill,
  border = DEFAULTS.border,
  borderPx = DEFAULTS.borderPx,
  cornerRadius = DEFAULTS.cornerRadius,
  label = DEFAULTS.label,
  labelColor = DEFAULTS.labelColor,
  labelSizePx = DEFAULTS.labelSizePx,
  labelBold = DEFAULTS.labelBold,
  className = DEFAULTS.className,
  wrapperClassName = DEFAULTS.wrapperClassName,
  markerOptions,
}) {
  useEffect(() => {
    if (!map && !layer) return;

    let marker;
    try {
      marker = createPlatformMarker({
        leaflet,
        map,
        layer,
        lat,
        lon,
        lng,
        width,
        height,
        angleDeg,
        fill,
        border,
        borderPx,
        cornerRadius,
        label,
        labelColor,
        labelSizePx,
        labelBold,
        className,
        wrapperClassName,
        markerOptions,
      });
    } catch (error) {
      console.error("PlatformMarker failed to mount:", error);
      return undefined;
    }

    return () => {
      if (marker) marker.remove();
    };
  }, [
    leaflet,
    map,
    layer,
    lat,
    lon,
    lng,
    width,
    height,
    angleDeg,
    fill,
    border,
    borderPx,
    cornerRadius,
    label,
    labelColor,
    labelSizePx,
    labelBold,
    className,
    wrapperClassName,
    markerOptions,
  ]);

  return null;
}

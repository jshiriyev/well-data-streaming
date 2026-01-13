import { useEffect, useMemo } from "react";

function resolveLeaflet(explicitLeaflet) {
  if (explicitLeaflet) return explicitLeaflet;
  if (typeof window !== "undefined" && window.L) return window.L;
  return null;
}

function normalizeDate(value) {
  if (value instanceof Date && !Number.isNaN(value.getTime())) return value;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed;
}

function toMonthKey(date) {
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  return `${year}-${month}-01`;
}

const DEFAULT_ICON_STYLE = {
  fillColor: "#22c55e",
  fillOpacity: 0.8,
  stroke: "false",
  radius: 7,
};

const DEFAULT_TIME_LAYER_OPTIONS = {
  updateTimeDimension: true,
  duration: "PT1S",
  addLastPoint: false,
};

function normalizeTimeLayerOptions(options = {}) {
  const merged = { ...DEFAULT_TIME_LAYER_OPTIONS, ...options };
  const hasAddLastPoint = Object.prototype.hasOwnProperty.call(merged, "addLastPoint");
  const hasAddlastPoint = Object.prototype.hasOwnProperty.call(merged, "addlastPoint");
  if (hasAddLastPoint && !hasAddlastPoint) {
    merged.addlastPoint = merged.addLastPoint;
  }
  if (hasAddLastPoint) {
    delete merged.addLastPoint;
  }
  return merged;
}

function defaultPointToLayer(feature, latLng, L) {
  const iconStyle = feature?.properties?.iconstyle || {};
  const style = feature?.properties?.style || {};
  const radius = Number(iconStyle.radius) || DEFAULT_ICON_STYLE.radius;
  const fillColor = iconStyle.fillColor || style.color || DEFAULT_ICON_STYLE.fillColor;
  const fillOpacity =
    iconStyle.fillOpacity ?? DEFAULT_ICON_STYLE.fillOpacity;
  const strokeDisabled = String(iconStyle.stroke).toLowerCase() === "false";
  const strokeColor = style.color || fillColor;

  return L.circleMarker(latLng, {
    radius,
    fillColor,
    fillOpacity,
    color: strokeColor,
    weight: 1,
    fill: true,
    stroke: !strokeDisabled,
  });
}

function defaultOnEachFeature(feature, layer) {
  const popup = feature?.properties?.popup;
  if (popup !== null && popup !== undefined) {
    layer.bindPopup(String(popup));
  }
}

function wrapTimeDimensionLayer(L, baseLayer, options) {
  if (L?.timeDimension?.layer?.geoJson) {
    return L.timeDimension.layer.geoJson(baseLayer, options);
  }
  if (L?.TimeDimension?.Layer?.GeoJson) {
    return new L.TimeDimension.Layer.GeoJson(baseLayer, options);
  }
  return baseLayer;
}

export function buildTimeStampedGeojson({
  wells = [],
  rates = [],
  color = DEFAULT_ICON_STYLE.fillColor,
  wellIdKey = "well",
  wellLatKey = "lat",
  wellLonKey = "lon",
  rateWellKey = "well",
  rateDateKey = "date",
  iconStyle = {},
  style = {},
} = {}) {
  const features = [];
  const monthsByWell = new Map();

  rates.forEach((rate) => {
    if (!rate) return;
    const wellId = rate[rateWellKey];
    if (wellId === null || wellId === undefined) return;
    const date = normalizeDate(rate[rateDateKey]);
    if (!date) return;
    const monthKey = toMonthKey(date);
    const key = String(wellId);
    if (!monthsByWell.has(key)) monthsByWell.set(key, new Set());
    monthsByWell.get(key).add(monthKey);
  });

  wells.forEach((well) => {
    if (!well) return;
    const wellId = well[wellIdKey];
    if (wellId === null || wellId === undefined) return;
    const lat = Number(well[wellLatKey]);
    const lon = Number(well[wellLonKey]);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;

    const monthKeys = monthsByWell.get(String(wellId));
    if (!monthKeys || monthKeys.size === 0) return;

    monthKeys.forEach((monthKey) => {
      features.push({
        type: "Feature",
        geometry: { type: "Point", coordinates: [lon, lat] },
        properties: {
          time: monthKey,
          popup: String(wellId),
          icon: "circle",
          iconstyle: { ...DEFAULT_ICON_STYLE, fillColor: color, ...iconStyle },
          style: { color, ...style },
        },
      });
    });
  });

  return { type: "FeatureCollection", features };
}

export function createTimeStampedGeojsonLayer({
  leaflet,
  map,
  data,
  geoJsonOptions = {},
  timeLayerOptions = {},
}) {
  const L = resolveLeaflet(leaflet);
  if (!L) {
    throw new Error("Leaflet is not available. Pass `leaflet` or load it globally.");
  }

  const pointToLayer =
    geoJsonOptions.pointToLayer ||
    ((feature, latLng) => defaultPointToLayer(feature, latLng, L));
  const onEachFeature = geoJsonOptions.onEachFeature || defaultOnEachFeature;

  const baseLayer = L.geoJSON(data, {
    ...geoJsonOptions,
    pointToLayer,
    onEachFeature,
  });

  const timeLayer = wrapTimeDimensionLayer(
    L,
    baseLayer,
    normalizeTimeLayerOptions(timeLayerOptions)
  );

  if (map) timeLayer.addTo(map);
  return timeLayer;
}

export function TimeStampedGeojsonLayer({
  map,
  wells,
  rates,
  color = DEFAULT_ICON_STYLE.fillColor,
  wellIdKey = "well",
  wellLatKey = "lat",
  wellLonKey = "lon",
  rateWellKey = "well",
  rateDateKey = "date",
  iconStyle,
  style,
  geoJsonOptions,
  timeLayerOptions,
  leaflet,
}) {
  const data = useMemo(
    () =>
      buildTimeStampedGeojson({
        wells,
        rates,
        color,
        wellIdKey,
        wellLatKey,
        wellLonKey,
        rateWellKey,
        rateDateKey,
        iconStyle,
        style,
      }),
    [
      wells,
      rates,
      color,
      wellIdKey,
      wellLatKey,
      wellLonKey,
      rateWellKey,
      rateDateKey,
      iconStyle,
      style,
    ]
  );

  useEffect(() => {
    const L = resolveLeaflet(leaflet);
    if (!L || !map) return;

    const layer = createTimeStampedGeojsonLayer({
      leaflet: L,
      map,
      data,
      geoJsonOptions,
      timeLayerOptions,
    });

    return () => {
      if (layer) layer.remove();
    };
  }, [map, leaflet, data, geoJsonOptions, timeLayerOptions]);

  return null;
}

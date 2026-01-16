import { useEffect } from "react";

function resolveLeaflet(explicitLeaflet) {
  if (explicitLeaflet) return explicitLeaflet;
  if (typeof window !== "undefined" && window.L) return window.L;
  return null;
}

function toLatLngBounds(L, bounds) {
  if (!Array.isArray(bounds) || bounds.length !== 2) return null;
  const [sw, ne] = bounds;
  if (!Array.isArray(sw) || !Array.isArray(ne)) return null;
  return L.latLngBounds(L.latLng(sw[0], sw[1]), L.latLng(ne[0], ne[1]));
}

export function SceneLock({
  map,
  bounds,
  pad = 0.02,
  fit = true,
  fitPadding = [20, 20],
  fitMaxZoom = null,
  animate = false,
  noWrap = true,
  viscosity = 0.8,
  lockMinZoom = true,
  leaflet,
}) {
  useEffect(() => {
    const L = resolveLeaflet(leaflet);
    if (!L || !map) return;

    const targetBounds = toLatLngBounds(L, bounds);
    if (!targetBounds) return;

    const previousMaxBounds = map.getMaxBounds ? map.getMaxBounds() : map.options.maxBounds;
    const previousViscosity = map.options.maxBoundsViscosity;
    const previousMinZoom = map.getMinZoom ? map.getMinZoom() : map.options.minZoom;

    const paddedMax = targetBounds.pad(pad);
    map.setMaxBounds(paddedMax);
    map.options.maxBoundsViscosity = viscosity;

    const updatedNoWrap = new Map();
    const applyNoWrap = (layer) => {
      if (layer instanceof L.TileLayer) {
        if (!updatedNoWrap.has(layer)) {
          updatedNoWrap.set(layer, layer.options.noWrap);
        }
        layer.options.noWrap = true;
      }
    };

    const handleLayerAdd = (event) => applyNoWrap(event.layer);
    if (noWrap) {
      map.eachLayer(applyNoWrap);
      map.on("layeradd", handleLayerAdd);
    }

    const doFit = () => {
      if (!fit) return;
      const options = {
        padding: L.point(fitPadding[0], fitPadding[1]),
        animate: Boolean(animate),
      };
      if (fitMaxZoom !== null && fitMaxZoom !== undefined) {
        options.maxZoom = fitMaxZoom;
      }

      map.fitBounds(targetBounds, options);

      if (lockMinZoom) {
        const lock = () => map.setMinZoom(map.getZoom());
        if (options.animate) {
          map.once("zoomend", lock);
        } else {
          lock();
        }
      }
    };

    const handleLoad = () => {
      if (typeof window !== "undefined" && window.requestAnimationFrame) {
        window.requestAnimationFrame(doFit);
      } else {
        doFit();
      }
    };

    if (map._loaded) {
      handleLoad();
    } else {
      map.once("load", handleLoad);
    }

    const handleResize = () => {
      const targetZoom = map.getBoundsZoom(
        targetBounds,
        true,
        L.point(fitPadding[0], fitPadding[1])
      );
      if (map.getZoom() < targetZoom) {
        map.setView(targetBounds.getCenter(), targetZoom, { animate: false });
        if (lockMinZoom) map.setMinZoom(targetZoom);
      }
    };
    map.once("resize", handleResize);

    return () => {
      if (noWrap) {
        map.off("layeradd", handleLayerAdd);
      }

      updatedNoWrap.forEach((value, layer) => {
        layer.options.noWrap = value;
      });

      map.setMaxBounds(previousMaxBounds || null);
      map.options.maxBoundsViscosity = previousViscosity;

      if (lockMinZoom && previousMinZoom !== undefined) {
        map.setMinZoom(previousMinZoom);
      }

      map.off("load", handleLoad);
      map.off("resize", handleResize);
    };
  }, [
    map,
    bounds,
    pad,
    fit,
    fitPadding,
    fitMaxZoom,
    animate,
    noWrap,
    viscosity,
    lockMinZoom,
    leaflet,
  ]);

  return null;
}

import { updateMap } from "./Marker.Update.js";
import { SessionState } from "./Session.State.js";

export function createOnemap({
  mapId = "onemap-map",
  sidebarId = "sidebar-filter",
} = {}) {
  if (typeof document === "undefined") return null;
  if (typeof L === "undefined") {
    console.error("Leaflet is not available on the page.");
    return null;
  }

  const mapEl = document.getElementById(mapId);
  if (!mapEl) return null;

  const latlng = L.latLng(40.21838483721167, 51.07054395510173);
  const initialDate = new Date(SessionState.time);

  const map = L.map(mapId, {
    center: latlng,
    zoom: 14,
    zoomControl: false,
    preferCanvas: false,
    attributionControl: 0,
    timeDimension: true,
    timeDimensionOptions: {
      timeInterval: "1980-01-01/2025-12-01",
      period: "P1M",
      currentTime: initialDate.getTime(),
    },
  });

  const tileLayer = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    minZoom: 0,
    maxZoom: 19,
    maxNativeZoom: 19,
    noWrap: false,
    attribution:
      "&copy; <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a> contributors",
    subdomains: "abc",
    detectRetina: false,
    tms: false,
    opacity: 1,
  }).addTo(map);

  const bounds = [
    [40.18237924998362, 51.01761966086437],
    [40.25439042443973, 51.1234682493391],
  ];

  const fieldContours = L.tileLayer("/onemap/tile/{z}/{x}/{y}.png", {
    tms: true,
    name: "FLD Contours",
    overlay: true,
    opacity: 1.0,
    maxNativeZoom: 17,
    minZoom: 14,
    maxZoom: 18,
    noWrap: true,
    bounds,
    attribution: "Ac Azneft IB",
  }).addTo(map);

  const filterSidebar = L.control
    .sidebar(sidebarId, {
      position: "left",
      autoPan: true,
      closeButton: false,
    })
    .addTo(map);

  const SidebarToggleControl = L.Control.extend({
    options: {
      position: "topleft",
    },
    onAdd: function () {
      const container = L.DomUtil.create(
        "div",
        "leaflet-bar sidebar-toggle-control"
      );
      const button = L.DomUtil.create("a", "sidebar-toggle-btn", container);
      button.href = "#";
      button.title = "Toggle filter sidebar";
      button.setAttribute("aria-label", "Toggle filter sidebar");
      button.innerHTML = "&#9776;";

      L.DomEvent.disableClickPropagation(container);
      L.DomEvent.on(button, "click", function (event) {
        L.DomEvent.preventDefault(event);
        filterSidebar.toggle();
      });

      return container;
    },
  });

  map.addControl(new SidebarToggleControl());

  const wellPointFeatureGroup = L.featureGroup().addTo(map);
  if (typeof window !== "undefined") {
    window.wellPointFeatureGroup = wellPointFeatureGroup;
  }

  const searchControl = new L.Control.Search({
    layer: wellPointFeatureGroup,
    propertyName: "searchKey",
    collapsed: true,
    textPlaceholder: "Search Well...",
    position: "topleft",
    initial: true,
    zoom: 16,
    hideMarkerOnCollapse: true,
  });

  map.addControl(searchControl);

  L.control.zoom({ position: "topleft" }).addTo(map);

  (function () {
    const BASE_RECENTER = latlng;
    const BASE_RECENTER_ZOOM = 14;

    function recenterWithSidebarAwareness(mapInstance) {
      const sidebarVisible = filterSidebar?.isVisible?.();
      let targetCenter = BASE_RECENTER;

      if (sidebarVisible) {
        const sidebarOffset = filterSidebar.getOffset?.() || 0;
        if (sidebarOffset !== 0) {
          const projected = mapInstance.project(BASE_RECENTER, BASE_RECENTER_ZOOM);
          const shifted = projected.add(L.point(-sidebarOffset / 2, 0));
          targetCenter = mapInstance.unproject(shifted, BASE_RECENTER_ZOOM);
        }
      }

      const currentCenter = mapInstance.getCenter();
      const currentZoom = mapInstance.getZoom();
      const needsCenterUpdate =
        Math.abs(currentCenter.lat - targetCenter.lat) > 1e-6 ||
        Math.abs(currentCenter.lng - targetCenter.lng) > 1e-6;
      const needsZoomUpdate = currentZoom !== BASE_RECENTER_ZOOM;

      if (needsCenterUpdate || needsZoomUpdate) {
        mapInstance.setView(targetCenter, BASE_RECENTER_ZOOM, { animate: false });
      }
    }

    const Recenter = L.Control.extend({
      options: { position: "topleft" },
      onAdd: function (mapInstance) {
        const container = L.DomUtil.create(
          "div",
          "leaflet-control leaflet-control-recenter"
        );

        const btn = L.DomUtil.create("a", "recenter-btn", container);
        btn.href = "#";
        btn.title = "Re-center";
        btn.setAttribute("role", "button");
        btn.setAttribute("aria-label", "Re-center map");

        btn.innerHTML = `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="2"/>
          <path d="M12 4v3 M12 17v3 M4 12h3 M17 12h3" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/>
        </svg>
        `;

        L.DomEvent.disableClickPropagation(container);
        L.DomEvent.disableScrollPropagation(container);

        L.DomEvent.on(btn, "click", function (e) {
          if (e) L.DomEvent.stop(e);
          recenterWithSidebarAwareness(mapInstance);
        });

        L.DomEvent.on(btn, "keydown", function (e) {
          if (e.key === "Enter" || e.key === " ") {
            if (e) L.DomEvent.stop(e);
            recenterWithSidebarAwareness(mapInstance);
          }
        });

        return container;
      },
    });
    map.addControl(new Recenter());
  })();

  const horizonList = [
    "KaS",
    "PK",
    "KS",
    "NKP",
    "NKG",
    "FLD",
    "Bal_X",
    "Bal_IX",
    "Bal_VIII",
    "Bal_VII",
    "Bal_VI",
    "Bal_V",
    "Bal_IV",
    "Sabunchi",
  ];

  function createHorizonControl(horizons = []) {
    const container = document.createElement("div");
    container.className = "leaflet-control horizon-dropup-container";

    L.DomEvent.disableClickPropagation(container);
    L.DomEvent.disableScrollPropagation(container);

    const button = document.createElement("button");
    button.type = "button";
    button.className = "horizon-dropup-button";

    let selected = SessionState.horizon;
    button.textContent = selected || "Select horizon";

    const menu = document.createElement("ul");
    menu.className = "horizon-dropup-menu";

    horizons.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      li.dataset.value = item;
      if (item === selected) {
        li.style.fontWeight = "bold";
      }

      li.addEventListener("click", () => {
        selected = item;
        button.textContent = selected;

        Array.from(menu.children).forEach((child) => {
          child.style.fontWeight = "normal";
        });
        li.style.fontWeight = "bold";

        button.classList.remove("open");
        menu.classList.remove("show");

        SessionState.horizon = selected;
        updateMap(wellPointFeatureGroup).catch((error) => {
          console.error("Failed to update wells for horizon", selected, error);
        });
      });

      menu.appendChild(li);
    });

    button.addEventListener("click", () => {
      button.classList.toggle("open");
      menu.classList.toggle("show");
    });

    const handleDocClick = (e) => {
      if (!container.contains(e.target)) {
        button.classList.remove("open");
        menu.classList.remove("show");
      }
    };

    document.addEventListener("click", handleDocClick);

    container.appendChild(button);
    container.appendChild(menu);

    return {
      container,
      destroy: () => document.removeEventListener("click", handleDocClick),
    };
  }

  const HorizonControl = L.Control.extend({
    options: {
      position: "bottomleft",
      horizons: [],
    },
    initialize: function (options = {}) {
      L.Util.setOptions(this, options);
      this._horizons = options.horizons || [];
    },
    onAdd: function () {
      const api = createHorizonControl(this._horizons);
      this._cleanup = api.destroy;
      this._container = api.container;
      return this._container;
    },
    onRemove: function () {
      if (this._cleanup) {
        this._cleanup();
        this._cleanup = null;
      }
    },
  });

  const horizonControl = new HorizonControl({
    position: "bottomleft",
    horizons: horizonList,
  });

  map.addControl(horizonControl);

  const timeControl = new L.Control.TimeDimension({
    position: "bottomleft",
    autoPlay: false,
    minSpeed: 1,
    speedStep: 1,
    timeSliderDragUpdate: true,
  });

  map.addControl(timeControl);

  const onTimeLoad = (e) => {
    const isoDate = new Date(e.time).toISOString().slice(0, 10);

    SessionState.time = isoDate;

    updateMap(wellPointFeatureGroup).catch((error) => {
      console.error("Failed to update wells for time", isoDate, error);
    });
  };

  map.timeDimension.on("timeload", onTimeLoad);

  const ensureBottomLeftColumn = () => {
    const mapContainer = map?.getContainer?.();
    if (!mapContainer) return null;
    const bottomLeftCorner = mapContainer.querySelector(
      ".leaflet-bottom.leaflet-left"
    );
    if (!bottomLeftCorner) return null;

    let columnContainer = bottomLeftCorner.querySelector(
      ".leaflet-bottom-left-row"
    );
    if (!columnContainer) {
      columnContainer = document.createElement("div");
      columnContainer.className = "leaflet-bottom-left-row";
      bottomLeftCorner.appendChild(columnContainer);
    }
    return columnContainer;
  };

  const placeControlInColumn = (control) => {
    const columnContainer = ensureBottomLeftColumn();
    const controlContainer = control?.getContainer?.();
    if (!columnContainer || !controlContainer) {
      return false;
    }
    if (controlContainer.parentElement !== columnContainer) {
      columnContainer.appendChild(controlContainer);
    }
    return true;
  };

  let alignRaf = 0;
  let destroyed = false;

  const alignBottomLeftControls = () => {
    if (destroyed) return;
    const horizonReady = placeControlInColumn(horizonControl);
    const timeReady = placeControlInColumn(timeControl);
    if (!horizonReady || !timeReady) {
      alignRaf = requestAnimationFrame(alignBottomLeftControls);
    }
  };

  map.whenReady(() => {
    alignBottomLeftControls();
  });

  const layerControl = L.control.layers().addTo(map);

  layerControl.addBaseLayer(tileLayer, "OpenStreetMap");

  const measureControl = new L.Control.Measure({
    position: "bottomright",
    primaryLengthUnit: "meters",
    secondaryLengthUnit: "kilometers",
    primaryAreaUnit: "sqmeters",
    secondaryAreaUnit: "hectares",
    activeColor: "#ABE67E",
    completedColor: "#C8F2BE",
    collapsed: false,
  });

  map.addControl(measureControl);

  L.Control.Measure.include({
    _setCaptureMarkerIcon: function () {
      this._captureMarker.options.autoPanOnFocus = false;
      this._captureMarker.setIcon(
        L.divIcon({
          iconSize: this._map.getSize().multiplyBy(2),
        })
      );
    },
  });

  map.whenReady(() => {
    updateMap(wellPointFeatureGroup).catch((error) => {
      console.error("Failed to update wells", error);
    });
  });

  return {
    map,
    destroy: () => {
      destroyed = true;
      if (alignRaf) {
        cancelAnimationFrame(alignRaf);
        alignRaf = 0;
      }
      map.timeDimension?.off?.("timeload", onTimeLoad);
      map.removeControl?.(horizonControl);
      map.remove();
      if (typeof window !== "undefined" && window.wellPointFeatureGroup === wellPointFeatureGroup) {
        delete window.wellPointFeatureGroup;
      }
    },
  };
}

import "@styles/onemap-sidebar.css";
import "@styles/onemap-setup.css";
import "@styles/onemap-marker-settings.css";

import "@composables/onemap/Onemap.Sidebar.js";
import { initMarkerSettings } from "@composables/onemap/Marker.Settings.js";
import { createOnemap } from "@composables/onemap/Onemap.Setup.js";

let onemapInstance = null;
let markerSettings = null;

export function initOnemap() {
  if (onemapInstance) {
    return onemapInstance;
  }
  markerSettings = initMarkerSettings();
  onemapInstance = createOnemap();
  return onemapInstance;
}

export function destroyOnemap() {
  markerSettings?.destroy?.();
  markerSettings = null;
  onemapInstance?.destroy?.();
  onemapInstance = null;
}

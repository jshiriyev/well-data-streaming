<template>
  <div class="onemap-view">
    <div class="onemap-map" id="onemap-map"></div>
    <div id="sidebar-filter">
      <div class="leaflet-sidebar-content">
        <div class="leaflet-sidebar-pane" id="filter" aria-labelledby="filter-heading">
          <h1 class="leaflet-sidebar-header" id="filter-heading">Filters</h1>
          <div id="filters-container"></div>
          <p class="sidebar-hint">
            Click values or drag sliders to filter. Each box filters one column (AND logic).
          </p>
        </div>
      </div>
    </div>
    <div
      class="modal fade"
      id="marker-settings-modal"
      tabindex="-1"
      role="dialog"
      aria-labelledby="marker-settings-title"
      aria-hidden="true"
    >
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h4 class="modal-title" id="marker-settings-title">Marker Settings</h4>
          </div>
          <div class="modal-body">
            <div class="container-fluid">
              <p class="text-muted">Marker configuration form will be injected here.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="status" class="onemap-status">{{ status }}</div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import { loadScriptOnce, loadStyleOnce } from "../utils/loaders.js";

const status = ref("Loading map...");
let onemapComponent = null;

async function loadOnemapAssets() {
  await Promise.all([
    loadStyleOnce("https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"),
    loadStyleOnce("https://unpkg.com/leaflet-search@3.0.2/dist/leaflet-search.min.css"),
    loadStyleOnce("https://cdn.jsdelivr.net/gh/ljagis/leaflet-measure@2.1.7/dist/leaflet-measure.min.css"),
    loadStyleOnce("https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"),
    loadStyleOnce(
      "https://cdn.jsdelivr.net/npm/leaflet-timedimension@1.1.0/dist/leaflet.timedimension.control.min.css"
    ),
  ]);

  await loadScriptOnce("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js");
  await loadScriptOnce("https://unpkg.com/leaflet-search@3.0.2/dist/leaflet-search.min.js");
  await loadScriptOnce("https://cdn.jsdelivr.net/npm/iso8601-js-period@0.2.1/iso8601.min.js");
  await loadScriptOnce(
    "https://cdn.jsdelivr.net/npm/leaflet-timedimension@1.1.0/dist/leaflet.timedimension.min.js"
  );
  await loadScriptOnce(
    "https://cdn.jsdelivr.net/gh/ljagis/leaflet-measure@2.1.7/dist/leaflet-measure.min.js"
  );
  await loadScriptOnce("https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js");
}

onMounted(async () => {
  try {
    await loadOnemapAssets();
    onemapComponent = await import("@pages/onemap.js");
    onemapComponent.initOnemap?.();
    status.value = "";
  } catch (error) {
    console.error("Failed to load OneMap", error);
    status.value = "Failed to load map assets.";
  }
});

onBeforeUnmount(() => {
  onemapComponent?.destroyOnemap?.();
  onemapComponent = null;
});
</script>

<style scoped>
.onemap-view {
  position: relative;
  width: 100%;
  min-height: 100vh;
  overflow: hidden;
}

.onemap-map {
  width: 100%;
  height: 100%;
  min-height: 100vh;
}

.onemap-status {
  position: absolute;
  top: 16px;
  left: 16px;
  background: rgba(15, 23, 42, 0.85);
  color: #fff;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.9rem;
  z-index: 2000;
}
</style>

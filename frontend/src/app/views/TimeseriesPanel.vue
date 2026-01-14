<template>
  <div ref="rootEl" class="timeseries-panel" :style="panelStyle">
    <div ref="sceneEl" class="scene" :class="{ 'is-open': sidebarOpen }">
      <aside ref="sidebarEl" class="sidebar" :class="{ 'is-open': sidebarOpen }" aria-label="Sidebar">
        <div class="sidebar-header">
          <h1 class="sidebar-title">Filters</h1>
        </div>
        <TimeseriesFilters
          :meta="meta"
          :pill-target="pillHost"
          @change="handleFiltersChange"
        />
        <p class="sidebar-hint">Click values to filter. Each box filters one column (AND logic).</p>
        <div ref="resizerEl" class="sidebar-resizer" title="Drag to resize"></div>
      </aside>

      <main class="main">
        <div class="card">
          <div class="main-toolbar">
            <button
              class="sidebar-toggle"
              type="button"
              aria-label="Toggle menu"
              :aria-expanded="sidebarOpen ? 'true' : 'false'"
              @click="toggleSidebar"
            >
              <span></span>
              <span></span>
              <span></span>
            </button>
            <div ref="pillHost"></div>
          </div>
          <div class="plot-wrapper">
            <TimeseriesBox
              v-for="box in boxes"
              :key="box.id"
              :box-id="box.id"
              :fields="fields"
              @ready="handleBoxReady"
              @destroy="handleBoxDestroy"
              @agg-change="handleAggChange"
            />
            <button class="box-bottom" type="button" aria-label="Add box" @click="addBox">+</button>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { fetchRateMeta } from "@api/fetch.rates.js";
import "@styles/timeseries-panel.css";
import "@styles/timeseries-sidebar.css";
import "@styles/timeseries-filter.css";
import "@styles/timeseries-parcel-box.css";
import TimeseriesBox from "./TimeseriesBox.vue";
import TimeseriesFilters from "./TimeseriesFilters.vue";
import {
  createTimeseriesState,
} from "@components/workspace/plotly-configs/timeseries/timeseries.js";

const props = defineProps({
  state: {
    type: Object,
    default: () => ({}),
  },
});

const rootEl = ref(null);
const sceneEl = ref(null);
const sidebarEl = ref(null);
const resizerEl = ref(null);
const pillHost = ref(null);
const boxes = ref([{ id: 1 }]);
const nextBoxId = ref(2);
const panelState = createTimeseriesState(props.state?.timeseries || {});
const sidebarOpen = ref(panelState.sidebarOpen !== false);
const sidebarWidth = ref(panelState.sidebarWidth || "");
const panelStyle = computed(() =>
  sidebarWidth.value ? { "--sidebar-width": sidebarWidth.value } : {}
);
const meta = ref(null);
const activeFilters = ref({});
const fields = ref([]);
const boxApis = new Map();
const disposers = [];
let resizeRaf = 0;
let metaCancelled = false;

function addListener(target, type, handler, options) {
  if (!target || !target.addEventListener) return;
  target.addEventListener(type, handler, options);
  disposers.push(() => target.removeEventListener(type, handler, options));
}

function clamp(n, min, max) {
  return Math.max(min, Math.min(max, n));
}

function readPxVar(name, fallback) {
  if (!rootEl.value) return fallback;
  const value = getComputedStyle(rootEl.value).getPropertyValue(name).trim();
  const parsed = parseFloat(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function scheduleResize() {
  if (resizeRaf) return;
  resizeRaf = window.requestAnimationFrame(() => {
    resizeRaf = 0;
    boxApis.forEach((api) => api?.resize?.());
  });
}

function openSidebar() {
  sidebarOpen.value = true;
  panelState.sidebarOpen = true;
}

function closeSidebar() {
  sidebarOpen.value = false;
  panelState.sidebarOpen = false;
}

function toggleSidebar() {
  if (sidebarOpen.value) {
    closeSidebar();
  } else {
    openSidebar();
  }
}

function addBox() {
  boxes.value.push({ id: nextBoxId.value++ });
}

function handleBoxReady({ id, api }) {
  if (!id || !api) return;
  boxApis.set(id, api);
  if (fields.value.length) {
    api.setFields?.(fields.value);
  }
  if (Object.keys(activeFilters.value).length) {
    api.refreshData?.(activeFilters.value);
  }
}

function handleBoxDestroy(id) {
  if (!id) return;
  boxApis.delete(id);
}

function handleAggChange(id) {
  const api = boxApis.get(id);
  api?.refreshData?.(activeFilters.value);
}

function handleFiltersChange(filters) {
  activeFilters.value = filters || {};
  refreshAll(activeFilters.value);
}

function refreshAll(filters) {
  const current = filters || activeFilters.value;
  boxApis.forEach((api) => api?.refreshData?.(current));
}

onMounted(() => {
  if (!rootEl.value) return;

  const savedWidth =
    panelState.sidebarWidth || localStorage.getItem("timeseriesSidebarWidth");
  if (savedWidth) {
    sidebarWidth.value = savedWidth;
    panelState.sidebarWidth = savedWidth;
  }

  if (panelState.sidebarOpen === false) {
    closeSidebar();
  } else {
    openSidebar();
  }

  const minW = readPxVar("--sidebar-min", 220);
  const maxW = readPxVar("--sidebar-max", 520);
  let dragging = false;
  let startX = 0;
  let startW = 0;

  addListener(resizerEl.value, "pointerdown", (event) => {
    if (!sidebarOpen.value) return;
    dragging = true;
    resizerEl.value?.setPointerCapture(event.pointerId);
    startX = event.clientX;
    startW = readPxVar("--sidebar-width", 360);
    event.preventDefault();
  });

  addListener(resizerEl.value, "pointermove", (event) => {
    if (!dragging) return;
    const dx = event.clientX - startX;
    const nextW = clamp(startW + dx, minW, maxW);
    const px = `${Math.round(nextW)}px`;
    sidebarWidth.value = px;
    panelState.sidebarWidth = px;
    localStorage.setItem("timeseriesSidebarWidth", px);
    scheduleResize();
  });

  addListener(resizerEl.value, "pointerup", (event) => {
    if (!dragging) return;
    dragging = false;
    try {
      resizerEl.value?.releasePointerCapture(event.pointerId);
    } catch {}
    scheduleResize();
  });

  addListener(resizerEl.value, "pointercancel", () => {
    dragging = false;
  });

  addListener(window, "keydown", (event) => {
    if (event.key === "Escape") closeSidebar();
    if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === "F") {
      openSidebar();
    }
  });

  fetchRateMeta()
    .then((payload) => {
      if (metaCancelled) return;
      meta.value = payload;
      fields.value = Array.isArray(payload?.numeric_fields) ? payload.numeric_fields : [];
      boxApis.forEach((api) => api?.setFields?.(fields.value));
    })
    .catch((error) => {
      console.error("Failed to load rate meta data", error);
    });
});

onBeforeUnmount(() => {
  metaCancelled = true;
  if (resizeRaf) {
    window.cancelAnimationFrame(resizeRaf);
    resizeRaf = 0;
  }
  while (disposers.length) {
    const dispose = disposers.pop();
    dispose();
  }
  boxApis.forEach((api) => api?.destroy?.());
  boxApis.clear();
});

function resize() {
  scheduleResize();
}

function getState() {
  return panelState;
}

defineExpose({ resize, getState });
</script>

<script setup>
import { ref, computed, defineAsyncComponent } from "vue";

import Button from "primevue/button";

import WellTreeDrawer from "./components/WellTreeDrawer.vue"

const view = ref(null); // "time" | "log" | null

const TimePanel = defineAsyncComponent(() => import("./components/PlotlyTimePanel.vue"));
const TimeDrawer = defineAsyncComponent(() => import("./components/PlotlyTimeDrawer.vue"));
const LogPanel  = defineAsyncComponent(() => import("./components/PlotlyLogPanel.vue"));
const LogDrawer = defineAsyncComponent(() => import("./components/PlotlyLogDrawer.vue"));

const CurrentPanel = computed(() => {
  if (view.value === "time") return TimePanel;
  if (view.value === "log") return LogPanel;
  return null;
});

const CurrentDrawer = computed(() => {
  if (view.value === "time") return TimeDrawer;
  if (view.value === "log") return LogDrawer;
  return null;
});

const visibleLeft = ref(false);
const visibleRight = ref(false);

const fig = ref({
  data: [
    { x: [1, 2, 3, 4], y: [10, 15, 13, 17], type: "scatter", mode: "lines+markers" },
  ],
  layout: { title: "Oil Rate" },
  config: { scrollZoom: true },
});

const depth = Array.from({ length: 2000 }, (_, i) => i + 1000); // 1000..2999
// Example curves
const gr = depth.map((d) => 40 + 20 * Math.sin(d / 80));
const res = depth.map((d) => 10 + 5 * Math.cos(d / 120));

const tracks = ref([
  {
    id: "gr",
    title: "GR (API)",
    xRange: [0, 150],
    scale: "linear",
    curves: [{ name: "GR", x: gr, y: depth, unit: "API" }],
  },
  {
    id: "res",
    title: "Resistivity (ohm·m)",
    xRange: [0.2, 200],
    scale: "log",
    curves: [{ name: "RT", x: res, y: depth, unit: "ohm·m" }],
  },
]);

function onPointClick(info) {
  console.log("Clicked:", info);
}

function onRefresh() {
  // Example: update data
  fig.value = {
    ...fig.value,
    data: [
      { x: [1, 2, 3, 4], y: [12, 14, 11, 19], type: "scatter", mode: "lines+markers" },
    ],
  };
}
</script>

<template>
  <div class="edge-hover left">
    <Button class="drawer-button" icon="pi pi-arrow-right" @click="visibleLeft = true" />
  </div>

  <WellTreeDrawer v-model:visible="visibleLeft" />

  <component v-if="CurrentPanel" :is="CurrentPanel" />
  <!-- <TimePanel title="Well GW8-001" :figure="fig" :height="420" @refresh="onRefresh" /> -->
  <LogPanel
    title="GW8-001 Logs"
    :tracks="tracks"
    :depthRange="[1000, 3000]"
    @track-click="onPointClick"
  />

  <div class="edge-hover right">
    <Button class="drawer-button" icon="pi pi-arrow-left" @click="visibleRight = true" />
  </div>

  <component v-if="CurrentDrawer" :is="CurrentDrawer" />
  <!-- <TimeDrawer v-model:visible="visibleRight" /> -->
  <LogDrawer v-model:visible="visibleRight" />
</template>

<style scoped>
.edge-hover {
  position: fixed;
  top: 0;
  height: 100vh;
  width: 24px; /* invisible hover area */
  z-index: 1000;

  display: flex;
  align-items: center;
  justify-content: center;
}

.edge-hover.left {
  left: 0;
}
.edge-hover.right {
  right: 0;
}

.drawer-button {
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
  transform: translateX(6px);
}

.edge-hover:hover .drawer-button {
  opacity: 1;
  pointer-events: auto;
  transform: translateX(0);
}

.draggable-panel {
  display: flex;
  flex-direction: column;
}

.draggable-panel > * {
  flex: 1 1 auto;
  min-height: 0; /* important for flex children */
}
</style>

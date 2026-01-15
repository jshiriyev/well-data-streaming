<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from "vue";

import "vue-draggable-resizable/style.css";
import VueDraggableResizable from "vue-draggable-resizable";
import Card from "primevue/card";
import Button from "primevue/button";
import Menu from "primevue/menu";

import Plotly from "plotly.js-dist-min";

/**
 * Props
 * - title: card title
 * - figure: { data: [], layout: {}, config: {} }
 * - height: fixed plot height (optional)
 * - showToolbar: show header buttons
 */
const props = defineProps({
  title: { type: String, default: "Plot" },
  figure: {
    type: Object,
    default: () => ({ data: [], layout: {}, config: {} }),
  },
  height: { type: [Number, String], default: 360 },
  showToolbar: { type: Boolean, default: true },
});

const emit = defineEmits(["refresh", "export", "close"]);

const plotEl = ref(null);
const menu = ref(null);

let ro = null;

const menuItems = [
  {
    label: "Export PNG",
    icon: "pi pi-image",
    command: () => emit("export"),
  },
  {
    label: "Refresh",
    icon: "pi pi-refresh",
    command: () => emit("refresh"),
  },
  { separator: true },
  {
    label: "Close",
    icon: "pi pi-times",
    command: () => emit("close"),
  },
];

function normalizedHeight() {
  return typeof props.height === "number" ? `${props.height}px` : props.height;
}

async function render() {
  if (!plotEl.value) return;

  const data = props.figure?.data ?? [];
  const layout = props.figure?.layout ?? {};
  const config = props.figure?.config ?? {};

  // Make Plotly auto-resize-friendly
  const mergedLayout = {
    margin: { l: 50, r: 20, t: 30, b: 40 },
    autosize: true,
    ...layout,
  };

  const mergedConfig = {
    displaylogo: false,
    responsive: true,
    ...config,
  };

  // If already rendered, react is faster; otherwise newPlot
  const already = plotEl.value.__plotly;
  if (already) {
    await Plotly.react(plotEl.value, data, mergedLayout, mergedConfig);
  } else {
    await Plotly.newPlot(plotEl.value, data, mergedLayout, mergedConfig);
  }

  // Ensure it fits after mount/layout
  Plotly.Plots.resize(plotEl.value);
}

function resetView() {
  if (!plotEl.value) return;
  Plotly.relayout(plotEl.value, { "xaxis.autorange": true, "yaxis.autorange": true });
}

function downloadPng() {
  if (!plotEl.value) return;
  Plotly.downloadImage(plotEl.value, {
    format: "png",
    filename: props.title?.replace(/\s+/g, "_").toLowerCase() || "plot",
    scale: 2,
  });
}

function toggleMenu(e) {
  menu.value?.toggle(e);
}

onMounted(async () => {
  await nextTick();
  await render();

  // ResizeObserver keeps Plotly fitting inside Card when container changes size
  ro = new ResizeObserver(() => {
    if (plotEl.value) Plotly.Plots.resize(plotEl.value);
  });
  ro.observe(plotEl.value.parentElement);
});

onBeforeUnmount(() => {
  ro?.disconnect();
  ro = null;
  if (plotEl.value?.__plotly) {
    Plotly.purge(plotEl.value);
  }
});

// Re-render when figure changes (deep watch)
watch(
  () => props.figure,
  async () => {
    await nextTick();
    await render();
  },
  { deep: true }
);

// Expose a couple methods for parent components (optional)
defineExpose({ render, resetView, downloadPng });
</script>

<template>
  <VueDraggableResizable
    class="draggable-panel"
    :w="400"
    :h="560"
    :draggable="true"
    :resizable="true"
  >
    <Card class="w-full">
      <template #title>
        <div class="flex items-center justify-between gap-2">
          <span class="font-semibold">{{ title }}</span>

          <div v-if="showToolbar" class="flex items-center gap-2">
            <Button
              icon="pi pi-refresh"
              text
              rounded
              aria-label="Refresh"
              @click="$emit('refresh')"
            />
            <Button
              icon="pi pi-expand"
              text
              rounded
              aria-label="Reset view"
              @click="resetView"
            />
            <Button
              icon="pi pi-download"
              text
              rounded
              aria-label="Download"
              @click="downloadPng"
            />
            <Button
              icon="pi pi-ellipsis-v"
              text
              rounded
              aria-label="More"
              @click="toggleMenu"
            />
            <Menu ref="menu" :model="menuItems" popup />
          </div>
        </div>
      </template>

      <template #content>
        <div class="plot-wrap" :style="{ height: normalizedHeight() }">
          <div ref="plotEl" class="plotly-host" />
        </div>
      </template>
    </Card>
  </VueDraggableResizable>
</template>

<style scoped>
.plot-wrap {
  width: 100%;
  position: relative;
}

/* Plotly needs the container to have explicit dimensions */
.plotly-host {
  width: 100%;
  height: 100%;
}
</style>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick, computed } from "vue";

import { fetchWellLog } from "@services/fetch.well.log.js";

import { createArchiePanel } from "@utils/archie.js";

import "vue-draggable-resizable/style.css";
import VueDraggableResizable from "vue-draggable-resizable";
import Card from "primevue/card";
import Button from "primevue/button";
import Menu from "primevue/menu";

import Plotly from "plotly.js-dist-min";

const props = defineProps({
  title: { type: String, default: "Well Log" },

  showToolbar: { type: Boolean, default: true },
  // Optional: show a top "label axis" band (like Techlog) - kept simple here
  showHeaderBand: { type: Boolean, default: false },

  height: { type: [Number, String], default: 520 },

  depthRange: { type: Array, default: () => [null, null] }, // [top, base]
  // depthTop: "",
  // depthBase: "",
  trailCount: {type: Number, default: 2 },
  trailGap: { type: Number, default: 0.012 },
  trails: { type: Object, default: [] } ,
  grid: {
    show: true,
    width: 0.05,
    color: "#20305f",
    alpha: 0.55,
    minor: {
      show: false,
      width: 0.03,
      color: "#20305f",
      alpha: 0.25,
    },
  },
  separator: {
    show: true,
    width: 1,
    color: "#20305f",
    alpha: 0.9,
  },
});

const data = await fetchWellLog(props.title);

const tracks = ref([
  {
    id: "gr",
    title: data.gr.mnemo,
    xRange: [0, 150],
    scale: "linear",
    curves: [{ name: data.gr.mnemo, x: data.gr.value, y: data.DEPT, unit: data.gr.unit }],
  },
  {
    id: "res",
    title: data.res.mnemo,
    xRange: [0, 2],
    scale: "log",
    curves: [
      { name: data.res.mnemo, x: data.res.value, y: data.DEPT, unit: data.res.unit },
    ],
  },
]);

const emit = defineEmits(["refresh", "export", "close", "track-click"]);

const plotEl = ref(null);
const menu = ref(null);
let ro = null;

const menuItems = computed(() => [
  {
    label: "Export PNG",
    icon: "pi pi-image",
    command: () => downloadPng(),
  },
  { separator: true },
  { label: "Refresh", icon: "pi pi-refresh", command: () => emit("refresh") },
  { label: "Close", icon: "pi pi-times", command: () => emit("close") },
]);

function normalizedHeight() {
  return typeof props.height === "number" ? `${props.height}px` : props.height;
}

function clamp(n, min, max) {
    return Math.max(min, Math.min(max, n));
}

function clampRange(a, b) {
  // Keep Plotly happy if user passes nulls
  if (a == null || b == null) return undefined;
  return [a, b];
}

function toNumber(value) {
    if (value === "" || value == null) return null;
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
}

function toRgba(hex, alpha) {
    if (!hex || typeof hex !== "string") return `rgba(32, 48, 95, ${alpha ?? 0.6})`;
    const raw = hex.replace("#", "").trim();
    if (raw.length !== 6) return `rgba(32, 48, 95, ${alpha ?? 0.6})`;
    const r = parseInt(raw.slice(0, 2), 16);
    const g = parseInt(raw.slice(2, 4), 16);
    const b = parseInt(raw.slice(4, 6), 16);
    if (![r, g, b].every(Number.isFinite)) {
        return `rgba(32, 48, 95, ${alpha ?? 0.6})`;
    }
    const a = Number.isFinite(alpha) ? alpha : 0.6;
    return `rgba(${r}, ${g}, ${b}, ${a})`;
}

function normalizeTrails(trails, count) {
    const target = Math.max(1, Number(count) || 1);
    const next = [];
    const existing = Array.isArray(trails) ? trails : [];

    for (let i = 0; i < target; i += 1) {
        const id = i + 1;
        const prev = existing.find((t) => t.id === id) || existing[i] || {};
        const curves = prev.curves instanceof Set
            ? new Set(prev.curves)
            : new Set(Array.isArray(prev.curves) ? prev.curves : []);
        next.push({
            id,
            xMin: prev.xMin ?? "",
            xMax: prev.xMax ?? "",
            curves
        });
    }

    return next;
}

function buildFigure() {
  const trackDefs = tracks.value ?? [];
  const n = Math.max(1, props.trails.length);

  // const trails =
  //   Array.isArray(state.trails) && state.trails.length
  //     ? state.trails
  //     : normalizeTrails([], state.trailCount);
  const gap = clamp(Number(props.trailGap) || 0, 0, 0.05);

  // Domain slices for x-axes (tracks)
  // const gap = 0.02;
  const totalGap = gap * (n - 1);
  const w = (1 - totalGap) / n;

  const layout = {
    autosize: true,
    margin: { l: 68, r: 24, t: 28, b: 44 },
    showlegend: false,

    hovermode: "closest",
    uirevision: "archie",
    // Depth axis (shared)
    yaxis: {
      autorange: "reversed", // depth downward
      showgrid: true, // !!state.grid?.show,
      range: clampRange(props.depthRange?.[0], props.depthRange?.[1]),
      // gridcolor: toRgba(state.grid?.color, state.grid?.alpha),
      // gridwidth: Number(state.grid?.width) || 0.5,
      tickformat: ",.0f",
      ticks: "outside",

      zeroline: false,
      shapes: [],
    },

    // Make panning/zooming feel "log-view-ish"
    // dragmode: "pan",

    // Optional: background
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
  };

  // if (state.grid?.minor?.show) {
  //   layout.yaxis.minor = {
  //       showgrid: true,
  //       gridcolor: toRgba(state.grid.minor.color, state.grid.minor.alpha),
  //       gridwidth: Number(state.grid.minor.width) || 0.25
  //   };
  // }

  const data = [];

  trackDefs.forEach((trk, i) => {
    const xaxisName = i === 0 ? "xaxis" : `xaxis${i + 1}`;
    const xName = i === 0 ? "x" : `x${i + 1}`;

    const x0 = i * (w + gap);
    const x1 = x0 + w;

    // Configure per-track x-axis
    layout[xaxisName] = {
      domain: [x0, x1],
      title: trk.title ?? trk.id ?? `Track ${i + 1}`,
      range: trk.xRange ?? undefined,
      type: trk.scale === "log" ? "log" : "linear",
      ticks: "outside",
      showgrid: true,
      zeroline: false,
      // show tick labels for every track (set false if you want a cleaner look)
      showticklabels: true,
    };

    // Curves in this track
    (trk.curves ?? []).forEach((c) => {
      data.push({
        type: "scatter", // faster for big log arrays
        mode: "lines",
        name: c.name ?? "Curve",
        x: c.x ?? [],
        y: c.y ?? [],
        xaxis: xName,
        yaxis: "y",
        hovertemplate: `${c.name ?? "Curve"}: %{x}<br>` + `Depth: %{y}<extra></extra>`,
        line: { width: 1.25 },
      });
    });

    // Track boundary lines (visual separators)
    // Use layout shapes so the separators don't zoom weirdly
    layout.shapes = layout.shapes || [];
    if (i > 0) {
      layout.shapes.push({
        type: "line",
        xref: "paper",
        yref: "paper",
        x0,
        x1: x0,
        y0: 0,
        y1: 1,
        line: { width: 1 },
      });
    }
  });

  const config = {
    responsive: true,
    displaylogo: false,
    scrollZoom: true,
    displayModeBar: false,
    modeBarButtonsToRemove: [
      "select2d",
      "lasso2d",
      "autoScale2d", // we implement our own x-autoscale
    ],
  };

  return { data, layout, config };
}

async function render() {
  if (!plotEl.value) return;

  const fig = buildFigure();

  if (!fig.data || fig.data.length === 0) {
    plotEl.value.innerHTML = ""; // optional: clear
    return;
  }

  const already = plotEl.value.__plotly;
  if (already) {
    await Plotly.react(plotEl.value, fig.data, fig.layout, fig.config);
  } else {
    await Plotly.newPlot(plotEl.value, fig.data, fig.layout, fig.config);

    // Example: click handling (optional)
    plotEl.value.on?.("plotly_click", (ev) => {
      // Emit clicked curve/track info
      const pt = ev?.points?.[0];
      if (!pt) return;
      emit("track-click", {
        curveName: pt.data?.name,
        x: pt.x,
        depth: pt.y,
        // pt.xaxis / pt.yaxis contain ids like "x2" etc.
        xaxis: pt.xaxis?._id,
      });
    });
  }

  Plotly.Plots.resize(plotEl.value);
}

function resetView() {
  if (!plotEl.value) return;

  const update = { "yaxis.autorange": "reversed" };
  // Reset each x-axis too
  const trackDefs = tracks.value ?? [];
  const n = Math.max(1, trackDefs.length);
  for (let i = 1; i <= n; i++) {
    const ax = i === 1 ? "xaxis" : `xaxis${i}`;
    update[`${ax}.autorange`] = true;
  }
  Plotly.relayout(plotEl.value, update);
}

function autoscaleXFromData(padFrac = 0.03) {
  if (!plotEl.value) return;

  // Compute per-track x extents from rendered data
  const updates = {};
  const trackDefs = tracks.value ?? [];

  trackDefs.forEach((trk, i) => {
    let xmin = +Infinity;
    let xmax = -Infinity;

    (trk.curves ?? []).forEach((c) => {
      const xs = c.x ?? [];
      for (let k = 0; k < xs.length; k++) {
        const v = xs[k];
        if (v == null || Number.isNaN(v)) continue;
        if (v < xmin) xmin = v;
        if (v > xmax) xmax = v;
      }
    });

    if (!Number.isFinite(xmin) || !Number.isFinite(xmax)) return;

    const span = xmax - xmin || 1;
    const pad = span * padFrac;

    const ax = i === 0 ? "xaxis" : `xaxis${i + 1}`;
    updates[`${ax}.range`] = [xmin - pad, xmax + pad];
  });

  Plotly.relayout(plotEl.value, updates);
}

function downloadPng() {
  if (!plotEl.value) return;
  Plotly.downloadImage(plotEl.value, {
    format: "png",
    filename: props.title?.replace(/\s+/g, "_").toLowerCase() || "well_log",
    scale: 2,
  });
}

function toggleMenu(e) {
  menu.value?.toggle(e);
}

onMounted(async () => {
  await nextTick();
  await render();

  ro = new ResizeObserver(() => {
    if (plotEl.value) Plotly.Plots.resize(plotEl.value);
  });
  ro.observe(plotEl.value.parentElement);
});

onBeforeUnmount(() => {
  ro?.disconnect();
  ro = null;
  if (plotEl.value?.__plotly) Plotly.purge(plotEl.value);
});

// Re-render when tracks/depthRange change
watch(
  () => [tracks.value, props.depthRange],
  async () => {
    await nextTick();
    await render();
  },
  { deep: true }
);

// Optional: expose methods to parent
defineExpose({ render, resetView, autoscaleXFromData, downloadPng });
</script>

<template>
  <VueDraggableResizable
    class="draggable-panel"
    :w="400"
    :h="560"
    :draggable="true"
    :resizable="true"
  >
    <Card class="plot-card h-full w-full">
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
              icon="pi pi-arrows-h"
              text
              rounded
              aria-label="Autoscale X"
              @click="autoscaleXFromData()"
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
.plot-card {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.plot-card :deep(.p-card-body) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.plot-card :deep(.p-card-content) {
  flex: 1;
  min-height: 0;
}

.plot-wrap {
  width: 100%;
  height: 100% !important;
  /* position: relative; */
}

/* Plotly needs explicit container dimensions */
.plotly-host {
  width: 100%;
  height: 100%;
}
</style>

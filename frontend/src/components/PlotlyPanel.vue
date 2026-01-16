<script setup>
import { computed, defineAsyncComponent } from "vue";

/**
 * Expected panel shape (you can tweak names, but keep it consistent):
 * panel = {
 *   id: string,
 *   title: string,
 *   type: "time" | "log",     // or "TimePanel" | "LogPanel"
 *   payload: { ... }          // well, curves, date range, etc.
 * }
 */
const props = defineProps({
  panel: { type: Object, required: true },
});

const emit = defineEmits(["close", "focus"]);

const TimePanel = defineAsyncComponent(() => import("@components/PlotlyTimePanel.vue"));
const LogPanel = defineAsyncComponent(() => import("@components/PlotlyLogPanel.vue"));

function normalizeType(t) {
  const s = String(t || "")
    .toLowerCase()
    .trim();
  if (s === "timepanel") return "time";
  if (s === "logpanel") return "log";
  return s;
}

// Decide which component to render
const panelType = computed(() => normalizeType(props.panel?.viewType));

// Map type -> component
const panelComponent = computed(() => {
  if (panelType.value === "time") return TimePanel;
  if (panelType.value === "log") return LogPanel;
  return null;
});
</script>

<template>
  <KeepAlive>
    <component v-if="panelComponent" :is="panelComponent" v-bind="props.panel" />
  </KeepAlive>
</template>

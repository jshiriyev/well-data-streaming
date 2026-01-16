<template>
  <div ref="rootEl"></div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import {
  createArchiePanel,
  createArchieState,
} from "@components/workspace/plotly-configs/archie/archie.js";
import { loadPlotly } from "../utils/plotly.js";

const props = defineProps({
  state: {
    type: Object,
    default: () => ({}),
  },
});

const rootEl = ref(null);
let instance = null;
let aborted = false;

onMounted(async () => {
  if (!rootEl.value) return;
  try {
    await loadPlotly();
    if (aborted || !rootEl.value) return;
    const archieState = createArchieState(props.state?.archie || {});
    instance = createArchiePanel({
      root: rootEl.value,
      state: archieState,
    });
  } catch (error) {
    console.error("Failed to load Plotly for Archie panel", error);
    rootEl.value.innerHTML = "<div class=\"status\">Plotly failed to load.</div>";
  }
});

onBeforeUnmount(() => {
  aborted = true;
  if (instance) {
    instance.destroy();
    instance = null;
  }
});

function resize() {
  if (instance?.resize) instance.resize();
}

function render() {
  if (instance?.render) instance.render();
}

function bindSettings(root) {
  if (instance?.bindSettings) instance.bindSettings(root);
}

function getState() {
  return instance?.state || null;
}

defineExpose({ resize, render, bindSettings, getState });
</script>

<template>
  <div ref="rootEl"></div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import {
  createArchiePanel,
  createArchieState,
} from "../../../pages/workspaces/plotly-configs/archie/archie.js";

const props = defineProps({
  state: {
    type: Object,
    default: () => ({}),
  },
});

const rootEl = ref(null);
let instance = null;

onMounted(() => {
  if (!rootEl.value) return;
  const archieState = createArchieState(props.state?.archie || {});
  instance = createArchiePanel({
    root: rootEl.value,
    state: archieState,
  });
});

onBeforeUnmount(() => {
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

function getState() {
  return instance?.state || null;
}

defineExpose({ resize, render, getState });
</script>

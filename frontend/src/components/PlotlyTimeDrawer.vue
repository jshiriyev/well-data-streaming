<script setup>
import { computed, ref } from "vue";

import Drawer from "primevue/drawer";

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["update:modelValue"]);
const visibleLeft = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});
</script>

<template>
  <Drawer v-model:visible="visibleRight" header="Time Plot Settings" position="right">
  </Drawer>
</template>

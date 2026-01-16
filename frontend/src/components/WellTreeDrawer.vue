<script setup>
import { computed, onMounted, ref } from "vue";
import { fetchWells } from "@services/fetch.wells.js";

import Drawer from "primevue/drawer";
import Tree from "primevue/tree";

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  onNodeSelect: {
    type: Function,
  }
});

const emit = defineEmits(["update:modelValue", "node-select"]);
const visibleLeft = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});

const nodes = ref([]);

async function loadWellList() {
  try {
    const wells = await fetchWells();
    nodes.value = 
      wells.map((well) => ({
        key: `well:${well.well}`,
        label: well.well,
        icon: "pi pi-server",
        data: { kind: "well", meta: well },
      }));
  } catch (error) {
    console.error("Failed to load wells", error);
  }
}

onMounted(() => {
  loadWellList();
});

</script>

<template>
  <Drawer v-model:visible="visibleLeft" header="Well Stock">
    <Tree
      :value="nodes"
      selectionMode="single"
      @node-select="onNodeSelect"
      class="w-full"
    />
  </Drawer>
</template>

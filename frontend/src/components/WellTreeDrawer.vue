<script setup>
import { computed, ref } from "vue";

import Drawer from "primevue/drawer";
import Tree from "primevue/tree";

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

const nodes = ref([
  {
    key: "asset:socar",
    label: "SOCAR Upstream",
    children: [
      {
        key: "field:gunashli",
        label: "Günəşli Field",
        children: [
          {
            key: "platform:gw8",
            label: "Platform GW-8",
            children: [
              { key: "well:gw8-001", label: "GW8-001", data: { kind: "well" } },
              { key: "well:gw8-002", label: "GW8-002", data: { kind: "well" } },
            ],
          },
        ],
      },
    ],
  },
]);

async function onNodeExpand(node) {
  // Avoid reloading if already loaded
  if (node.children && node.children.length > 0) return;

  node.loading = true;

  // Example: fetch platforms for this field from your API
  // const platforms = await fetch(`/api/fields/${node.data.id}/platforms`).then(r => r.json());

  // Mock data:
  const platforms = [
    { id: "gw8", name: "Platform GW-8" },
    { id: "gw9", name: "Platform GW-9" },
  ];

  node.children = platforms.map((p) => ({
    key: `platform:${p.id}`,
    label: p.name,
    children: [], // platforms can lazy-load wells
    data: { kind: "platform", id: p.id },
  }));

  node.loading = false;
}

function onSelect(node) {
  // Typical next step: fetch well details when a well node is selected
  if (node?.data?.kind === "well") {
    console.log("Selected well:", node.key, node.label);
  }
}

const selectionKeys = ref({});

</script>

<template>
  <Drawer v-model:visible="visibleLeft" header="Well List">
    <Tree
      :value="nodes"
      @node-expand="onNodeExpand"
      selectionMode="single"
      v-model:selectionKeys="selectionKeys"
      @node-select="onSelect"
      class="w-full"
    />
  </Drawer>
</template>

<script setup>
import { ref } from "vue";

import Button from "primevue/button";

import WellTreeDrawer from "./components/WellTreeDrawer.vue";
import PlotlyPanel from "./components/PlotlyPanel.vue";

// Each panel describes what it should display
const openPanels = ref([]); // [{ id, title, nodeKey, viewType, props }]

const visibleLeft = ref(false);
const visibleRight = ref(false);

function makePanelFromNode(node) {
  // node should at least have: { key, label, type, payload }
  // You decide mapping rules here.
  return {
    id: crypto.randomUUID(),
    title: node.label,
    nodeKey: node.key,
    viewType: "logpanel", // e.g. "rates", "log", "meta"
    props: {
      // anything PlotPanel needs to fetch/plot
      well: node.payload?.well,
      // more…
    },
  };
}

function onNodeSelect(node) {
  const existing = openPanels.value.find((p) => p.nodeKey === node.key);
  if (existing) return; // or "focus" it, or move it to top
  openPanels.value.push(makePanelFromNode(node));
  visibleLeft.value = false;
}

function closePanel(panelId) {
  openPanels.value = openPanels.value.filter((p) => p.id !== panelId);
}
</script>

<template>
  <div class="edge-hover left">
    <Button class="drawer-button" icon="pi pi-arrow-right" @click="visibleLeft = true" />
  </div>

  <WellTreeDrawer v-model:visible="visibleLeft" @node-select="onNodeSelect" />

  <main class="workspace">
    <!-- <div v-if="openPanels.length === 0" class="empty">Click a node to open a panel.</div> -->
    <div class="panel-grid">
      <Suspense v-for="p in openPanels" :key="p.id">
        <template #default>
          <PlotlyPanel :panel="p" @close="closePanel(p.id)" />
        </template>
        <template #fallback>
          <div class="panel-skeleton">Loading {{ p.title }}…</div>
        </template>
      </Suspense>
    </div>
  </main>

  <div class="edge-hover right">
    <Button class="drawer-button" icon="pi pi-arrow-left" @click="visibleRight = true" />
  </div>

  <!-- <PlotlyDrawer /> -->
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

.workspace {
  padding: 12px 36px; /* leave room for edge hover zones */
  min-height: 100vh;
}

.panel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(520px, 1fr));
  gap: 12px;
  align-items: start;
}

.panel-skeleton {
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: #fff;
  padding: 14px;
  min-height: 240px;
  opacity: 0.75;
}

.empty {
  opacity: 0.7;
  padding: 12px;
}
</style>

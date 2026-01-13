<template>
  <div class="app workspaces-app">
    <aside class="sidebar" id="control">
      <h1>Workspace Builder</h1>
      <div class="settings-panel">
        <div class="settings-heading">Workspace</div>
        <label class="settings-field">
          <span class="settings-label">Workspace type</span>
          <select v-model="workspaceType" class="settings-input" id="workspaceType">
            <option v-for="option in workspaceTypes" :key="option.id" :value="option.id">
              {{ option.label }}
            </option>
          </select>
        </label>

        <div class="settings-heading">Plot types</div>
        <label class="settings-field">
          <span class="settings-label">Panel plot</span>
          <select v-model="plotType" class="settings-input" id="plotType">
            <option v-for="option in plotTypes" :key="option.id" :value="option.id">
              {{ option.label }}
            </option>
          </select>
        </label>
        <div class="settings-actions">
          <button class="settings-button" id="addPanelBtn" type="button" @click="addPanel">
            Add panel
          </button>
        </div>
        <p class="sidebar-note" id="workspaceStatus">
          {{ status }}
        </p>
      </div>
    </aside>

    <div
      ref="controlResizer"
      class="vertical-resizer"
      id="controlResizer"
      aria-label="Resize control"
    ></div>

    <main class="workspace">
      <div
        ref="goldenLayoutRoot"
        class="golden-layout-root"
        id="goldenLayoutRoot"
        role="application"
        aria-label="Workspace"
      ></div>
    </main>

    <div
      ref="settingsResizer"
      class="vertical-resizer"
      id="settingsResizer"
      aria-label="Resize settings"
    ></div>

    <aside class="sidebar" id="settings">
      <h1>Panel Settings</h1>
      <div ref="settingsContent" id="settingsContent">
        <p class="sidebar-note">Select a panel to view and edit its settings.</p>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import "../../styles/workspace-golden.css";
import { useWorkspaceDependencies } from "../composables/useWorkspaceDependencies.js";
import { useGoldenWorkspace } from "../composables/useGoldenWorkspace.js";

const goldenLayoutRoot = ref(null);
const controlResizer = ref(null);
const settingsResizer = ref(null);
const settingsContent = ref(null);

const { ready, error, load } = useWorkspaceDependencies();
const {
  workspaceTypes,
  plotTypes,
  workspaceType,
  plotType,
  status,
  init,
  addPanel,
  destroy,
} = useGoldenWorkspace({
  rootEl: goldenLayoutRoot,
  controlResizer,
  settingsResizer,
  settingsContent,
});

onMounted(async () => {
  try {
    await load();
    if (error.value) return;
    if (ready.value) init();
  } catch (err) {
    console.error("Failed to initialize workspaces view:", err);
  }
});

onBeforeUnmount(() => {
  destroy();
});
</script>

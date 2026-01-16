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
const visibleRight = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});
</script>

<template>
  <Drawer v-model:visible="visibleRight" header="Log Plot Settings" position="right">
    <div class="settings-heading">Suite Settings</div>
    <div class="settings-section">Depth Range</div>
    <div class="settings-row">
      <label class="settings-field">
        <span class="settings-label">Top Depth</span>
        <input
          class="settings-input"
          type="number"
          step="any"
          placeholder="e.g., 1000"
          data-role="top-depth"
        />
      </label>
      <label class="settings-field">
        <span class="settings-label">Base Depth</span>
        <input
          class="settings-input"
          type="number"
          step="any"
          placeholder="e.g., 2000"
          data-role="base-depth"
        />
      </label>
    </div>
    <div class="settings-actions">
      <button class="settings-button" type="button" data-action="apply-depths">
        Apply depths
      </button>
    </div>

    <div class="settings-section">Trail Controls</div>
    <div class="settings-row">
      <label class="settings-field">
        <span class="settings-label">Trail Count</span>
        <input
          class="settings-input"
          type="number"
          min="1"
          step="1"
          max="10"
          data-role="trail-count"
        />
      </label>
      <label class="settings-field">
        <span class="settings-label">Trail gap</span>
        <input
          class="settings-input"
          type="number"
          min="0"
          max="0.1"
          step="0.005"
          data-role="trail-gap"
        />
      </label>
    </div>

    <div class="settings-section">Grid Settings</div>
    <label class="settings-field settings-checkbox">
      <input type="checkbox" data-role="grid-show" />
      <span class="settings-label">Show grid</span>
    </label>
    <label class="settings-field">
      <span class="settings-label">Width</span>
      <input
        class="settings-input"
        type="number"
        min="0"
        step="0.05"
        data-role="grid-width"
      />
    </label>
    <label class="settings-field">
      <span class="settings-label">Color</span>
      <input class="settings-input" type="color" data-role="grid-color" />
    </label>
    <label class="settings-field">
      <span class="settings-label">Alpha</span>
      <input
        class="settings-input"
        type="number"
        min="0"
        max="1"
        step="0.05"
        data-role="grid-alpha"
      />
    </label>

    <div class="settings-section">Minor Grid</div>
    <label class="settings-field settings-checkbox">
      <input type="checkbox" data-role="grid-minor-show" />
      <span class="settings-label">Show minors</span>
    </label>
    <label class="settings-field">
      <span class="settings-label">Width</span>
      <input
        class="settings-input"
        type="number"
        min="0"
        step="0.05"
        data-role="grid-minor-width"
      />
    </label>
    <label class="settings-field">
      <span class="settings-label">Color</span>
      <input class="settings-input" type="color" data-role="grid-minor-color" />
    </label>
    <label class="settings-field">
      <span class="settings-label">Alpha</span>
      <input
        class="settings-input"
        type="number"
        min="0"
        max="1"
        step="0.05"
        data-role="grid-minor-alpha"
      />
    </label>

    <div class="settings-section">Separator</div>
    <label class="settings-field settings-checkbox">
      <input type="checkbox" data-role="separator-show" />
      <span class="settings-label">Show separator</span>
    </label>
    <label class="settings-field">
      <span class="settings-label">Width</span>
      <input
        class="settings-input"
        type="number"
        step="0.05"
        data-role="separator-width"
      />
    </label>
    <label class="settings-field">
      <span class="settings-label">Color</span>
      <input class="settings-input" type="color" data-role="separator-color" />
    </label>
    <label class="settings-field">
      <span class="settings-label">Alpha</span>
      <input
        class="settings-input"
        type="number"
        min="0"
        max="1"
        step="0.05"
        data-role="separator-alpha"
      />
    </label>

    <div class="settings-section">Trail</div>
    <label class="settings-field">
      <span class="settings-label">Choose trail</span>
      <select class="settings-input" data-role="trail-select"></select>
    </label>
    <div class="trail-panel" data-role="trail-panel"></div>

    <template>
      <div class="settings-panel">
        <div class="settings-row settings-row--split">
          <div class="settings-heading" data-role="trail-title">Trail</div>
          <button
            class="settings-button settings-button--danger"
            data-action="clearTrail"
            type="button"
          >
            Clear curves
          </button>
        </div>

        <div class="settings-row">
          <label class="settings-field">
            <span class="settings-label" data-role="xmin-label">X min (optional)</span>
            <input
              class="settings-input"
              type="number"
              step="any"
              placeholder="auto"
              data-field="xMin"
              data-role="xmin-input"
            />
          </label>
          <label class="settings-field">
            <span class="settings-label" data-role="xmax-label">X max (optional)</span>
            <input
              class="settings-input"
              type="number"
              step="any"
              placeholder="auto"
              data-field="xMax"
              data-role="xmax-input"
            />
          </label>
        </div>

        <div class="settings-section">Curves</div>
        <div class="curve-list"></div>
      </div>
    </template>
  </Drawer>
</template>

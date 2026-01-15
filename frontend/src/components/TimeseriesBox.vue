<template>
  <div ref="rootEl" class="box" :id="boxIdAttr">
    <div class="box-header">
      <button
        ref="addButtonEl"
        class="add-button"
        type="button"
        title="Add series"
        @click="openPicker"
      >
        +
      </button>
      <div
        v-for="pill in tracePills"
        :key="pill.name"
        class="name-pill"
        :data-name="pill.name"
      >
        <span class="label" :title="pill.name">{{ pill.label }}</span>
        <button class="close-btn" type="button" @click="removeTracePill(pill.name)">
          x
        </button>
      </div>
      <button
        ref="settingsButtonEl"
        class="settings-circle"
        type="button"
        aria-label="Settings"
        @click="openStyler"
      >
        <svg class="settings-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path
            d="M19.14 12.94c.04-.31.06-.63.06-.94s-.02-.63-.06-.94l2.03-1.58a.5.5 0 0 0 .12-.64l-1.92-3.32a.5.5 0 0 0-.6-.22l-2.39.96a7.5 7.5 0 0 0-1.63-.94l-.36-2.54A.5.5 0 0 0 13.9 1h-3.8a.5.5 0 0 0-.49.42l-.36 2.54c-.58.23-1.12.54-1.63.94l-2.39-.96a.5.5 0 0 0-.6.22L2.71 7.48a.5.5 0 0 0 .12.64l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94L2.83 14.52a.5.5 0 0 0-.12.64l1.92 3.32a.5.5 0 0 0 .6.22l2.39-.96c.5.4 1.05.71 1.63.94l.36 2.54a.5.5 0 0 0 .49.42h3.8a.5.5 0 0 0 .49-.42l.36-2.54c.58-.23 1.12-.54 1.63-.94l2.39.96a.5.5 0 0 0 .6-.22l1.92-3.32a.5.5 0 0 0-.12-.64l-2.03-1.58ZM12 15.5A3.5 3.5 0 1 1 12 8a3.5 3.5 0 0 1 0 7.5Z"
          />
        </svg>
      </button>
    </div>

    <div ref="pickerEl" class="series-picker" :class="{ 'is-open': pickerOpen }">
      <h2 class="series-picker-header">Box #{{ boxLabel }}: Series & Aggregation</h2>
      <div class="series-picker-choices">
        <label v-for="field in fieldOptions" :key="field">
          <input
            type="checkbox"
            name="choice"
            :value="field"
            :checked="isDraftSelected(field)"
            @change="toggleDraft(field, $event.target.checked)"
          />
          <span>{{ field }}</span>
          <select
            name="agg-select"
            :disabled="!isDraftSelected(field)"
            :value="draftAggs[field] || defaultAgg"
            @change="updateDraftAgg(field, $event.target.value)"
          >
            <option v-for="option in aggOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
      </div>
      <div class="series-picker-buttons">
        <button class="cancelButton" type="button" @click="closePicker">Cancel</button>
        <button
          class="confirmButton"
          type="button"
          :disabled="pickerBusy"
          @click="confirmPicker"
        >
          OK
        </button>
      </div>
    </div>

    <div ref="stylerEl" class="trace-styler" :class="{ 'is-open': stylerOpen }">
      <h2 class="board-title">Style Settings</h2>

      <div class="form-group">
        <label class="trace-label" :for="traceSelectId">Select Trace</label>
        <select
          class="trace-select"
          :id="traceSelectId"
          v-model="styleState.traceIndex"
          :disabled="!traces.length"
        >
          <option v-if="!traces.length" value="">No traces</option>
          <option v-else-if="styleState.traceIndex === ''" value="">Select...</option>
          <option v-for="option in traceOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>

      <div class="select-style-and-color">
        <div class="form-group">
          <label class="line-dash-label" :for="lineDashId">Line Style</label>
          <select
            class="line-dash-select"
            :id="lineDashId"
            v-model="styleState.lineDash"
            :disabled="!canStyle"
          >
            <option v-for="option in lineDashOptions" :key="option" :value="option">
              {{ option }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label class="line-color-label" :for="lineColorId">Line Color</label>
          <input
            type="color"
            class="line-color-input"
            :id="lineColorId"
            v-model="styleState.lineColor"
            :disabled="!canStyle"
          />
        </div>
      </div>

      <div class="range-mount line-width-mount">
        <div class="form-group range-row">
          <label>Line Width (px)</label>
          <input
            type="range"
            min="0"
            max="10"
            step="0.5"
            v-model.number="styleState.lineWidth"
            :disabled="!canStyle"
          />
          <span class="range-value">{{ styleState.lineWidth }}</span>
        </div>
      </div>
      <div class="range-mount line-opacity-mount">
        <div class="form-group range-row">
          <label>Opacity</label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            v-model.number="styleState.opacity"
            :disabled="!canStyle"
          />
          <span class="range-value">{{ styleState.opacity }}</span>
        </div>
      </div>

      <div class="form-group checkbox-group">
        <input
          type="checkbox"
          class="marker-toggle-input"
          :id="markerToggleId"
          v-model="styleState.markerEnabled"
          :disabled="!canStyle"
        />
        <label class="marker-toggle-label" :for="markerToggleId">Enable Markers</label>
      </div>

      <div class="marker-settings" v-show="styleState.markerEnabled">
        <div class="range-mount marker-size-mount">
          <div class="form-group range-row">
            <label>Marker Size</label>
            <input
              type="range"
              min="0"
              max="20"
              step="1"
              v-model.number="styleState.markerSize"
              :disabled="!canStyle"
            />
            <span class="range-value">{{ styleState.markerSize }}</span>
          </div>
        </div>

        <div class="form-group">
          <label class="marker-symbol-label" :for="markerSymbolId">Marker Symbol</label>
          <select
            class="marker-symbol-select"
            :id="markerSymbolId"
            v-model="styleState.markerSymbol"
            :disabled="!canStyle"
          >
            <option v-for="option in markerSymbolOptions" :key="option" :value="option">
              {{ option }}
            </option>
          </select>
        </div>
      </div>

      <div class="button-row">
        <button class="apply-style" type="button" :disabled="!canStyle" @click="applyStyle">
          Apply
        </button>
        <button
          class="reset-style secondary"
          type="button"
          :disabled="!canStyle"
          @click="resetStyle"
        >
          Reset
        </button>
      </div>
    </div>

    <div class="plot-display"></div>
    <div class="axis-control"></div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import {
  getTraceData,
  initTimeseriesBox,
  removeTrace,
  setTrace,
} from "@components/workspace/plotly-configs/timeseries/js/parcel.box.js";
import { useClickOutside } from "@composables/useClickOutside.js";
import { useDraggablePanel } from "@composables/useDraggablePanel.js";
import { useEscapeKey } from "@composables/useEscapeKey.js";
import { loadPlotly } from "../utils/plotly.js";

const props = defineProps({
  boxId: {
    type: [Number, String],
    required: true,
  },
  fields: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["ready", "destroy", "agg-change"]);

const rootEl = ref(null);
const addButtonEl = ref(null);
const settingsButtonEl = ref(null);
const pickerEl = ref(null);
const stylerEl = ref(null);

const pickerOpen = ref(false);
const stylerOpen = ref(false);
const pickerBusy = ref(false);

const boxIdAttr = computed(() => `box-${props.boxId}`);
const boxLabel = computed(() => String(props.boxId));
const fieldOptions = computed(() => (Array.isArray(props.fields) ? props.fields : []));

const boxApi = ref(null);
const traces = ref([]);
let aborted = false;

const aggSelections = reactive({});
const draftAggs = reactive({});
const draftSelected = ref(new Set());
const appliedSelected = ref(new Set());

const pickerPosition = ref(null);
const stylerPosition = ref(null);

const defaultAgg = "sum";
const aggOptions = [
  { value: "sum", label: "Sum" },
  { value: "mean", label: "Mean" },
  { value: "median", label: "Median" },
  { value: "min", label: "Min" },
  { value: "max", label: "Max" },
  { value: "count", label: "Count" },
  { value: "std", label: "Standard deviation" },
  { value: "var", label: "Variance" },
  { value: "first", label: "First" },
  { value: "last", label: "Last" },
];

const lineDashOptions = ["solid", "dash", "dot", "dashdot", "longdash", "longdashdot"];
const markerSymbolOptions = [
  "circle",
  "square",
  "diamond",
  "cross",
  "triangle-up",
  "triangle-down",
];

const defaultTraceStyle = {
  lineDash: "solid",
  lineColor: "#1f77b4",
  lineWidth: 2,
  opacity: 1.0,
  markerEnabled: false,
  markerSize: 6,
  markerSymbol: "circle",
};

const styleState = reactive({
  traceIndex: "",
  lineDash: defaultTraceStyle.lineDash,
  lineColor: defaultTraceStyle.lineColor,
  lineWidth: defaultTraceStyle.lineWidth,
  opacity: defaultTraceStyle.opacity,
  markerEnabled: defaultTraceStyle.markerEnabled,
  markerSize: defaultTraceStyle.markerSize,
  markerSymbol: defaultTraceStyle.markerSymbol,
});

const traceOptions = computed(() =>
  traces.value.map((trace, index) => ({
    value: String(index),
    label: trace.name || `Trace ${index + 1}`,
  }))
);

const selectedTraceIndex = computed(() => {
  if (styleState.traceIndex === "") return null;
  const parsed = Number(styleState.traceIndex);
  return Number.isFinite(parsed) ? parsed : null;
});

const canStyle = computed(() =>
  Number.isFinite(selectedTraceIndex.value) && traces.value.length > 0
);

const idPrefix = computed(() => `trace-styler-${props.boxId}`);
const traceSelectId = computed(() => `${idPrefix.value}-trace-select`);
const lineDashId = computed(() => `${idPrefix.value}-line-dash`);
const lineColorId = computed(() => `${idPrefix.value}-line-color`);
const markerToggleId = computed(() => `${idPrefix.value}-marker-toggle`);
const markerSymbolId = computed(() => `${idPrefix.value}-marker-symbol`);

const tracePills = computed(() =>
  traces.value.map((trace) => ({
    name: trace.name,
    label: formatTraceLabel(trace.name),
  }))
);

const { applyPosition: applyPickerPosition } = useDraggablePanel(pickerEl, {
  enabled: pickerOpen,
  position: pickerPosition,
  onPositionChange: (pos) => {
    if (boxApi.value) {
      boxApi.value._seriesPickerPos = pos;
    }
  },
});

const { applyPosition: applyStylerPosition } = useDraggablePanel(stylerEl, {
  enabled: stylerOpen,
  position: stylerPosition,
  onPositionChange: (pos) => {
    if (boxApi.value) {
      boxApi.value._traceStylerPos = pos;
    }
  },
});

useClickOutside(
  pickerEl,
  () => {
    pickerOpen.value = false;
  },
  { enabled: pickerOpen, ignore: [addButtonEl] }
);

useClickOutside(
  stylerEl,
  () => {
    stylerOpen.value = false;
  },
  { enabled: stylerOpen, ignore: [settingsButtonEl] }
);

useEscapeKey(
  () => {
    pickerOpen.value = false;
  },
  { enabled: pickerOpen }
);

useEscapeKey(
  () => {
    stylerOpen.value = false;
  },
  { enabled: stylerOpen }
);

function formatTraceLabel(name) {
  const maxLen = 15;
  if (!name) return "";
  return name.length > maxLen ? `${name.slice(0, maxLen)}...` : name;
}

function syncTraces() {
  const figTraces = boxApi.value?.fig?.traces || [];
  traces.value = figTraces
    .filter((trace) => trace?.name)
    .map((trace) => ({ name: trace.name }));
  appliedSelected.value = new Set(traces.value.map((trace) => trace.name));
}

function resetDraftAggs() {
  Object.keys(draftAggs).forEach((key) => delete draftAggs[key]);
  draftSelected.value.forEach((name) => {
    draftAggs[name] = aggSelections[name] || defaultAgg;
  });
}

function openPicker() {
  if (!boxApi.value) return;
  syncTraces();
  draftSelected.value = new Set(appliedSelected.value);
  resetDraftAggs();
  pickerOpen.value = true;
  stylerOpen.value = false;
  if (pickerPosition.value) {
    requestAnimationFrame(() => applyPickerPosition(pickerPosition.value));
  }
}

function closePicker() {
  pickerOpen.value = false;
}

function openStyler() {
  if (!boxApi.value) return;
  ensureTraceIndex();
  syncStyleFromTrace();
  stylerOpen.value = true;
  pickerOpen.value = false;
  if (stylerPosition.value) {
    requestAnimationFrame(() => applyStylerPosition(stylerPosition.value));
  }
}

function isDraftSelected(name) {
  return draftSelected.value.has(name);
}

function toggleDraft(name, checked) {
  const next = new Set(draftSelected.value);
  if (checked) {
    next.add(name);
    if (!draftAggs[name]) {
      draftAggs[name] = aggSelections[name] || defaultAgg;
    }
  } else {
    next.delete(name);
  }
  draftSelected.value = next;
}

function updateDraftAgg(name, value) {
  draftAggs[name] = value;
}

function confirmPicker() {
  if (!boxApi.value) {
    closePicker();
    return;
  }

  const fig = boxApi.value.fig;
  const currentNames = new Set((fig?.traces || []).map((trace) => trace.name));
  const selectionSet = new Set(draftSelected.value);

  const toRemove = [...currentNames].filter((name) => !selectionSet.has(name));
  const toAdd = [...selectionSet].filter((name) => !currentNames.has(name));

  let aggChanged = false;
  selectionSet.forEach((name) => {
    const nextAgg = draftAggs[name] || defaultAgg;
    if (currentNames.has(name) && aggSelections[name] !== nextAgg) {
      aggChanged = true;
    }
    aggSelections[name] = nextAgg;
  });

  Object.keys(aggSelections).forEach((name) => {
    if (!selectionSet.has(name)) {
      delete aggSelections[name];
    }
  });

  pickerBusy.value = true;
  try {
    toRemove.forEach((name) => removeTrace(boxApi.value, name));
    toAdd.forEach((name) => {
      setTrace(boxApi.value, getTraceData(boxApi.value.data, name));
    });
    syncTraces();
    boxApi.value.lastAggs = { ...aggSelections };

    if (toRemove.length || toAdd.length || aggChanged) {
      emit("agg-change", props.boxId);
    }
    closePicker();
  } catch (error) {
    console.error("Failed to update series selection", error);
  } finally {
    pickerBusy.value = false;
  }
}

function removeTracePill(name) {
  if (!boxApi.value) return;
  removeTrace(boxApi.value, name);
  syncTraces();
  const draftNext = new Set(draftSelected.value);
  draftNext.delete(name);
  draftSelected.value = draftNext;
  if (aggSelections[name]) {
    delete aggSelections[name];
  }
  if (draftAggs[name]) {
    delete draftAggs[name];
  }
  boxApi.value.lastAggs = { ...aggSelections };
}

function ensureTraceIndex() {
  if (!traces.value.length) {
    styleState.traceIndex = "";
    return;
  }
  const idx = selectedTraceIndex.value;
  if (idx === null || idx >= traces.value.length) {
    styleState.traceIndex = "0";
  }
}

function getTraceSource(traceIndex) {
  const plotTrace = boxApi.value?.plotDiv?.data?.[traceIndex];
  if (plotTrace) return plotTrace;
  return boxApi.value?.fig?.traces?.[traceIndex] || null;
}

function extractTraceStyle(trace) {
  const line = trace?.line || {};
  const marker = trace?.marker || {};
  const hasMarkers =
    (trace?.mode || "").includes("markers") || (marker.size ?? 0) > 0;

  return {
    lineDash: line.dash ?? defaultTraceStyle.lineDash,
    lineColor: line.color ?? defaultTraceStyle.lineColor,
    lineWidth: line.width ?? defaultTraceStyle.lineWidth,
    opacity: trace?.opacity ?? defaultTraceStyle.opacity,
    markerEnabled: hasMarkers,
    markerSize: marker.size ?? defaultTraceStyle.markerSize,
    markerSymbol: marker.symbol ?? defaultTraceStyle.markerSymbol,
  };
}

function syncStyleFromTrace() {
  const idx = selectedTraceIndex.value;
  if (idx === null) return;
  const trace = getTraceSource(idx);
  if (!trace) return;
  const style = extractTraceStyle(trace);
  styleState.lineDash = style.lineDash;
  styleState.lineColor = style.lineColor;
  styleState.lineWidth = style.lineWidth;
  styleState.opacity = style.opacity;
  styleState.markerEnabled = style.markerEnabled;
  styleState.markerSize = style.markerSize;
  styleState.markerSymbol = style.markerSymbol;
}

function persistStyleToFigure(traceIndex) {
  const figTrace = boxApi.value?.fig?.traces?.[traceIndex];
  if (!figTrace) return;

  figTrace.line = {
    ...(figTrace.line || {}),
    dash: styleState.lineDash,
    color: styleState.lineColor,
    width: styleState.lineWidth,
  };
  figTrace.opacity = styleState.opacity;
  if (styleState.markerEnabled) {
    figTrace.mode = "lines+markers";
    figTrace.marker = {
      ...(figTrace.marker || {}),
      size: styleState.markerSize,
      symbol: styleState.markerSymbol,
    };
  } else {
    figTrace.mode = "lines";
    if (figTrace.marker) {
      figTrace.marker.size = 0;
    }
  }
}

function applyStyle() {
  const idx = selectedTraceIndex.value;
  if (idx === null) return;
  const plotDiv = boxApi.value?.plotDiv;
  if (!plotDiv) return;
  if (typeof Plotly === "undefined") return;

  const restyle = {
    "line.color": styleState.lineColor,
    "line.dash": styleState.lineDash,
    "line.width": styleState.lineWidth,
    opacity: styleState.opacity,
    mode: styleState.markerEnabled ? "lines+markers" : "lines",
    "marker.size": styleState.markerEnabled ? styleState.markerSize : 0,
    "marker.symbol": styleState.markerEnabled ? styleState.markerSymbol : undefined,
  };

  Plotly.restyle(plotDiv, restyle, [idx]);
  persistStyleToFigure(idx);
}

function resetStyle() {
  const idx = selectedTraceIndex.value;
  if (idx === null) return;
  styleState.lineDash = defaultTraceStyle.lineDash;
  styleState.lineColor = defaultTraceStyle.lineColor;
  styleState.lineWidth = defaultTraceStyle.lineWidth;
  styleState.opacity = defaultTraceStyle.opacity;
  styleState.markerEnabled = defaultTraceStyle.markerEnabled;
  styleState.markerSize = defaultTraceStyle.markerSize;
  styleState.markerSymbol = defaultTraceStyle.markerSymbol;
  applyStyle();
}

watch(
  () => props.fields,
  (next) => {
    const nextFields = Array.isArray(next) ? next : [];
    boxApi.value?.setFields?.(nextFields);
    const allowed = new Set(nextFields);
    Object.keys(aggSelections).forEach((name) => {
      if (!allowed.has(name)) {
        delete aggSelections[name];
      }
    });
    if (boxApi.value) {
      boxApi.value.lastAggs = { ...aggSelections };
    }
  },
  { immediate: true }
);

watch(traces, () => {
  ensureTraceIndex();
  if (stylerOpen.value) {
    syncStyleFromTrace();
  }
});

watch(
  () => styleState.traceIndex,
  () => {
    if (stylerOpen.value) {
      syncStyleFromTrace();
    }
  }
);

watch(pickerOpen, (open) => {
  if (open && pickerPosition.value) {
    requestAnimationFrame(() => applyPickerPosition(pickerPosition.value));
  }
});

watch(stylerOpen, (open) => {
  if (open && stylerPosition.value) {
    requestAnimationFrame(() => applyStylerPosition(stylerPosition.value));
  }
});

onMounted(async () => {
  if (!rootEl.value) return;
  try {
    await loadPlotly();
    if (aborted || !rootEl.value) return;
    const instance = initTimeseriesBox(rootEl.value, {
      index: props.boxId,
      fields: fieldOptions.value,
      enablePicker: false,
      enableStyler: false,
      useDomPills: false,
    });
    boxApi.value = instance;
    if (instance?._seriesPickerPos) {
      pickerPosition.value = { ...instance._seriesPickerPos };
    }
    if (instance?._traceStylerPos) {
      stylerPosition.value = { ...instance._traceStylerPos };
    }
    syncTraces();
    emit("ready", { id: props.boxId, api: instance });
  } catch (error) {
    console.error("Failed to load Plotly for timeseries box", error);
    const plotHost = rootEl.value.querySelector(".plot-display");
    if (plotHost) {
      plotHost.innerHTML = "<div class=\"status\">Plotly failed to load.</div>";
    }
  }
});

onBeforeUnmount(() => {
  aborted = true;
  if (boxApi.value?.destroy) {
    boxApi.value.destroy();
  }
  emit("destroy", props.boxId);
  boxApi.value = null;
});

defineExpose({ getApi: () => boxApi.value });
</script>

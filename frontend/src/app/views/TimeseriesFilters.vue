<template>
  <div class="filter-container">
    <div class="efs-wrap">
      <div class="efs-columns">
        <div v-for="field in fields" :key="field.key" class="efs-col">
          <div class="efs-head">
            <div class="efs-title">{{ field.label }}</div>
          </div>
          <input
            v-model="field.search"
            class="efs-search"
            type="text"
            :placeholder="`Search ${field.label}...`"
          />
          <div class="efs-list">
            <label class="efs-item efs-all">
              <input
                type="checkbox"
                :checked="isAllVisibleSelected(field)"
                :indeterminate.prop="isIndeterminate(field)"
                @change="toggleSelectAll(field, $event.target.checked)"
              />
              <span>Select all</span>
            </label>
            <label
              v-for="item in visibleItems(field)"
              :key="item.key"
              class="efs-item"
            >
              <input
                type="checkbox"
                :checked="isSelected(field, item.index)"
                @change="toggleValue(field, item.index, $event.target.checked)"
              />
              <span>{{ item.label }}</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  </div>

  <teleport v-if="pillTarget" :to="pillTarget">
    <div ref="pillEl" class="filter-pill">
      <button
        class="filter-chip"
        type="button"
        aria-haspopup="true"
        :aria-expanded="dropdownOpen ? 'true' : 'false'"
        @click="toggleDropdown"
      >
        <span class="filter-chip-prefix">Active filters:</span>
        <span class="filter-chip-label">{{ summary }}</span>
        <span class="filter-chip-caret" aria-hidden="true">&#9662;</span>
      </button>
      <div class="filter-dropdown" :hidden="!dropdownOpen">
        <div class="filter-dropdown-content">
          <div v-if="entries.length === 0" class="filter-empty">
            All data (no filter applied)
          </div>
          <div v-else v-for="entry in entries" :key="entry.key" class="filter-row">
            <div class="filter-row-field">{{ entry.label }}</div>
            <div class="filter-row-values">
              {{ entry.values.length ? entry.values.join(", ") : "[ ]" }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useClickOutside } from "../composables/useClickOutside.js";
import { useEscapeKey } from "../composables/useEscapeKey.js";

const props = defineProps({
  meta: {
    type: Object,
    default: null,
  },
  pillTarget: {
    type: [Object, String],
    default: null,
  },
});

const emit = defineEmits(["change"]);

const dropdownOpen = ref(false);
const pillEl = ref(null);
const fields = ref([]);

const summary = computed(() => {
  if (!entries.value.length) return "All data";
  return entries.value
    .map((entry) => {
      const values = entry.values.length ? entry.values.join(", ") : "[ ]";
      return `${entry.label}: ${values}`;
    })
    .join(" | ");
});

const entries = computed(() => {
  return fields.value
    .filter((field) => !isAllSelected(field))
    .map((field) => ({
      key: field.key,
      label: field.label || field.key,
      values: field.values
        .map((_, idx) => (field.selectedValues.has(idx) ? field.labels[idx] : null))
        .filter(Boolean),
    }));
});

useClickOutside(
  pillEl,
  () => {
    dropdownOpen.value = false;
  },
  { enabled: dropdownOpen }
);

useEscapeKey(
  () => {
    dropdownOpen.value = false;
  },
  { enabled: dropdownOpen }
);

function toggleDropdown() {
  dropdownOpen.value = !dropdownOpen.value;
}

function formatFilterValue(value) {
  if (value === null || value === undefined || value === "") return "(blank)";
  return String(value);
}

function normalizeValues(values) {
  if (values === null || values === undefined) return [];
  if (Array.isArray(values)) return values.slice();
  if (values instanceof Set) return Array.from(values);
  return [values];
}

function moveBlankToFront(values) {
  const list = Array.isArray(values) ? values.slice() : [];
  const blankIndex = list.indexOf("");
  if (blankIndex > 0) {
    const [blank] = list.splice(blankIndex, 1);
    list.unshift(blank);
  }
  return list;
}

function normalizeMetadata(meta) {
  if (!meta) return { fields: [] };

  if (Array.isArray(meta.fields)) {
    const valuesByField =
      meta.valuesByField && typeof meta.valuesByField === "object"
        ? meta.valuesByField
        : meta.categories && typeof meta.categories === "object"
          ? meta.categories
          : {};
    return {
      fields: meta.fields
        .map((field) => {
          if (typeof field === "string" || typeof field === "number") {
            const text = String(field);
            return { key: text, label: text, values: valuesByField?.[text] ?? [] };
          }
          const key = field?.key ?? field?.name ?? field?.id ?? field?.label;
          if (!key) return null;
          const label = field?.label ?? field?.name ?? key;
          const values =
            field?.values ?? field?.options ?? valuesByField?.[key] ?? [];
          return { key, label, values };
        })
        .filter(Boolean),
    };
  }

  const categories =
    meta.categories && typeof meta.categories === "object"
      ? meta.categories
      : meta.valuesByField && typeof meta.valuesByField === "object"
        ? meta.valuesByField
        : {};
  const fieldNames = Array.isArray(meta.categorical_fields)
    ? meta.categorical_fields
    : Object.keys(categories);

  return {
    fields: fieldNames.map((name) => ({
      key: name,
      label: name,
      values: categories?.[name] ?? [],
    })),
  };
}

function buildFields(meta) {
  const normalized = normalizeMetadata(meta);
  fields.value = normalized.fields.map((field) => {
    const values = moveBlankToFront(normalizeValues(field.values));
    const labels = values.map((value) => formatFilterValue(value));
    const selectedValues = new Set(values.map((_, idx) => idx));
    return {
      key: field.key,
      label: field.label || field.key,
      values,
      labels,
      selectedValues,
      search: "",
    };
  });
  emitChange();
}

function emitChange() {
  const normalized = {};
  fields.value.forEach((field) => {
    if (!field.values.length) return;
    if (field.selectedValues.size === field.values.length) return;
    const selected = field.values
      .map((value, idx) => (field.selectedValues.has(idx) ? value : undefined))
      .filter((value) => value !== undefined);
    normalized[field.key] = selected;
  });
  emit("change", Object.keys(normalized).length ? normalized : {});
}

function isAllSelected(field) {
  return field.selectedValues.size === field.values.length;
}

function visibleItems(field) {
  const q = field.search.trim().toLowerCase();
  return field.labels
    .map((label, index) => ({
      index,
      label,
      key: `${field.key}-${index}`,
      match: label.toLowerCase().includes(q),
    }))
    .filter((item) => item.match || !q);
}

function isAllVisibleSelected(field) {
  const items = visibleItems(field);
  if (!items.length) return false;
  return items.every((item) => field.selectedValues.has(item.index));
}

function isIndeterminate(field) {
  const items = visibleItems(field);
  if (!items.length) return false;
  const selectedCount = items.filter((item) =>
    field.selectedValues.has(item.index)
  ).length;
  return selectedCount > 0 && selectedCount < items.length;
}

function isSelected(field, index) {
  return field.selectedValues.has(index);
}

function toggleValue(field, index, checked) {
  if (checked) {
    field.selectedValues.add(index);
  } else {
    field.selectedValues.delete(index);
  }
  emitChange();
}

function toggleSelectAll(field, checked) {
  const items = visibleItems(field);
  items.forEach((item) => {
    if (checked) {
      field.selectedValues.add(item.index);
    } else {
      field.selectedValues.delete(item.index);
    }
  });
  emitChange();
}

watch(
  () => props.meta,
  (next) => {
    buildFields(next);
  },
  { immediate: true }
);
</script>

const RATES_ENDPOINT = "/api/rates";
const RATES_META_ENDPOINT = "/api/rates/meta";

(function () {
  const scene = document.querySelector(".scene");
  const sidebar = document.querySelector(".sidebar");
  // const closeBtn = document.querySelector(".sidebar-close-button");
  const toggleBtn = document.getElementById("sidebarToggle");

  if (!sidebar) return;

  const setToggleState = (isOpen) => {
    if (!toggleBtn) return;
    toggleBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
    // toggleBtn.textContent = isOpen ? "Hide filters" : "Show filters";
  };

  const openProfile = () => {
    sidebar.classList.add("is-open");
    if (scene) {
      scene.classList.add("is-open");
    }
    setToggleState(true);
  };

  const closeSidebar = () => {
    sidebar.classList.remove("is-open");
    if (scene) {
      scene.classList.remove("is-open");
    }
    setToggleState(false);
  };

  // if (closeBtn) {
  //   closeBtn.addEventListener("click", closeSidebar);
  // }

  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const isOpen = sidebar.classList.contains("is-open");
      if (isOpen) {
        closeSidebar();
      } else {
        openProfile();
      }
    });
  }

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeSidebar();
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'F') {
      openProfile();
    }
  });

  openProfile();

  const resizer = document.getElementById("sidebarResizer");

  // Load saved width (if any)
  const saved = localStorage.getItem("sidebarWidth");
  if (saved) document.documentElement.style.setProperty("--sidebar-width", saved);

  function px(n) { return `${Math.round(n)}px`; }
  function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }
  function readPxVar(name, fallback) {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    const n = parseFloat(v);
    return Number.isFinite(n) ? n : fallback;
  }

  const MIN_W = readPxVar("--sidebar-min", 220);
  const MAX_W = readPxVar("--sidebar-max", 520);

  let dragging = false;

  resizer.addEventListener("pointerdown", (e) => {
    // Only allow resize when sidebar is open
    if (!scene.classList.contains("is-open")) return;

    dragging = true;
    resizer.setPointerCapture(e.pointerId);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  });

  resizer.addEventListener("pointermove", (e) => {
    if (!dragging) return;

    // Sidebar width should match mouse X (distance from left edge)
    const newWidth = clamp(e.clientX, MIN_W, MAX_W);

    document.documentElement.style.setProperty("--sidebar-width", px(newWidth));
    localStorage.setItem("sidebarWidth", px(newWidth));

    // If you have Plotly in main, this helps it reflow
    window.dispatchEvent(new Event("resize"));
  });

  function stopDrag() {
    if (!dragging) return;
    dragging = false;
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
  }

  resizer.addEventListener("pointerup", stopDrag);
  resizer.addEventListener("pointercancel", stopDrag);

})();

let rateMeta;
let rateData;

function normalizeFilterValues(values) {
  if (values === null || values === undefined) return [];
  if (Array.isArray(values)) return values;
  if (values instanceof Set) return Array.from(values);
  return [values];
}

document.addEventListener("DOMContentLoaded", async () => {
  try {
    rateMeta = await fetchRateMeta();
  } catch (error) {
    console.error("Failed to load rate meta data", error);
  }

  try {
    rateData = await fetchRateData();
  } catch (error) {
    console.error("Failed to load rate data", error);
  }
});

async function fetchRateMeta() {
  const response = await fetch(RATES_META_ENDPOINT);

  if (!response.ok) {
    throw new Error(`Metadata request failed with status ${response.status}`);
  }
  const payload = await response.json();
  rateMeta = payload;
  document.dispatchEvent(new CustomEvent("rate-meta-ready", { detail: rateMeta }));
  if (window.filterSidebar?.setMetadata) {
    window.filterSidebar.setMetadata(rateMeta);
  }

  return payload;
}

async function fetchRateData(selectedFilters = {}, aggSelections = {}) {
  const params = new URLSearchParams();

  const hasEmptyFilter = Object.entries(selectedFilters).some(([, values]) => {
    const normalized = normalizeFilterValues(values);
    return normalized.length === 0;
  });

  if (hasEmptyFilter) {
    const emptyPayload = { date: [] };
    Object.keys(aggSelections || {}).forEach((field) => {
      if (field) emptyPayload[field] = [];
    });
    rateData = emptyPayload;
    document.dispatchEvent(new CustomEvent("rate-data-ready", { detail: rateData }));
    return emptyPayload;
  }

  Object.entries(selectedFilters).forEach(([field, values]) => {
    normalizeFilterValues(values).forEach((val) => {
      params.append(field, val);
    });
  });

  Object.entries(aggSelections).forEach(([field, agg]) => {
    if (!field || !agg) return;
    params.append("agg", `${field}:${agg}`);
  });

  const query = params.toString();
  const url = query ? `${RATES_ENDPOINT}?${query}` : RATES_ENDPOINT;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Rates request failed with status ${response.status}`);
  }

  const payload = await response.json();
  rateData = payload;
  document.dispatchEvent(new CustomEvent("rate-data-ready", { detail: rateData }));

  return payload;
}

function waitForRateMeta() {
  return rateMeta ? Promise.resolve(rateMeta)
    : new Promise(resolve => document.addEventListener(
      "rate-meta-ready", e => resolve(e.detail), { once: true })
    );
}

const filterSidebar = createFilterSidebar({
  host: document.querySelector(".filter-container"),
  pillHost: document.querySelector(".filter-pill"),
  eventName: "filter-changed",
  legacyEventName: "rate-filter-changed",
});

const plotWrapper = createPlotWrapper({
  host: document.querySelector(".plot-wrapper"),
  filter: filterSidebar,
});

waitForRateMeta().then((meta) => {
  filterSidebar.setFields(meta)
  plotWrapper.setFields(meta.numeric_fields);
});

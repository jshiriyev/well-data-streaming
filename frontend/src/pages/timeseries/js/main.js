import { createFilterSidebar } from "./filter.sidebar.js";
import { createPlotWrapper } from "./plot.wrapper.js";
import { fetchRateData, fetchRateMeta } from "./api.js";

(function () {
  const scene = document.querySelector(".scene");
  const sidebar = document.querySelector(".sidebar");
  const toggleBtn = document.getElementById("sidebarToggle");

  if (!sidebar) return;

  const setToggleState = (isOpen) => {
    if (!toggleBtn) return;
    toggleBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
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
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === "F") {
      openProfile();
    }
  });

  openProfile();

  const resizer = document.getElementById("sidebarResizer");

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

  resizer?.addEventListener("pointerdown", (e) => {
    if (!scene?.classList.contains("is-open")) return;

    dragging = true;
    resizer.setPointerCapture(e.pointerId);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  });

  resizer?.addEventListener("pointermove", (e) => {
    if (!dragging) return;

    const newWidth = clamp(e.clientX, MIN_W, MAX_W);

    document.documentElement.style.setProperty("--sidebar-width", px(newWidth));
    localStorage.setItem("sidebarWidth", px(newWidth));

    window.dispatchEvent(new Event("resize"));
  });

  function stopDrag() {
    if (!dragging) return;
    dragging = false;
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
  }

  resizer?.addEventListener("pointerup", stopDrag);
  resizer?.addEventListener("pointercancel", stopDrag);
})();

let rateMeta;
let rateData;

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
  filterSidebar.setFields(meta);
  plotWrapper.setFields(meta.numeric_fields);
});

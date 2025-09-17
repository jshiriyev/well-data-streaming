from __future__ import annotations
import json
from pathlib import Path
from branca.element import MacroElement, Element
from jinja2 import Template

class CategoricalFilterSidebar(MacroElement):
    """
    One-stop sidebar + filters.

    Usage:
        CategoricalFilterSidebar(
            rows=rows,
            cols=cols,
            container_id="sidebar",
            position="left",
            visible=True,
            autopan=True,
        ).add_to(m)

    Notes:
      - Expects your Leaflet Sidebar assets:
          L.Control.Sidebar.css / L.Control.Sidebar.js
      - Renders a <div id="sidebar">... with #filters-container inside.
      - Builds Excel-style, multi-select listboxes with (available/total) counts.
      - Shows/hides map layers by options.__well_id (DivIcon labels supported).
    """

    DEFAULT_HTML = """
<div id="sidebar">
  <div class="leaflet-sidebar-content">
    <div class="leaflet-sidebar-pane" id="filter" aria-labelledby="filter">
      <h1 class="leaflet-sidebar-header">Filters</h1>
      <div id="filters-container"></div>
      <p style="margin-top:12px;color:#666;">
        Click values or use search. Lists update with AND logic; (available/total) shown live.
      </p>
    </div>
  </div>
</div>
""".strip()

    _template = Template(r"""
{% macro script(this, kwargs) %}
// --- Initialize Leaflet Sidebar control ---
var __sidebar = L.control.sidebar('{{ this.container_id }}', {
  position: '{{ this.position }}',
  autoPan: {{ 'true' if this.autopan else 'false' }},
  closeButton: true
}).addTo({{ this._parent.get_name() }});{% if this.visible %} __sidebar.show();{% endif %}

// Optional: Shift+F to toggle
document.addEventListener('keydown', function(e){
  if (e.shiftKey && (e.key === 'f' || e.key === 'F')) __sidebar.toggle();
});

// --- Multi-filter logic (IIFE) ---
(function(){
  // ====== Configuration injected from Python ======
  const ROWS = {{ this._rows_json | safe }};
  const COLS = {{ this._cols_json | safe }};
  const CONTAINER_ID = {{ this.container_id | tojson }};

  // ====== Mount point ======
  const sidebarRoot = document.getElementById(CONTAINER_ID);
  if (!sidebarRoot) { console.warn("CategoricalFilterSidebar: container not found:", CONTAINER_ID); return; }
  const host = sidebarRoot.querySelector("#filters-container");
  if (!host) { console.warn("CategoricalFilterSidebar: #filters-container missing"); return; }

  // ====== Build HTML ======
  host.innerHTML = "";
  const wrap = document.createElement("div");
  wrap.className = "efs-wrap";
  wrap.innerHTML = `
    <div class="efs-toolbar" style="display:flex;gap:8px;align-items:center;margin-bottom:10px;">
      <button id="efs-reset" class="efs-btn">Reset Filters</button>
      <span style="color:#666;font-size:12px;">Click to reset the filters.</span>
    </div>
    <div class="efs-columns"></div>
  `;
  host.appendChild(wrap);
  const colArea = wrap.querySelector(".efs-columns");

  // ====== Minimal styles (scoped) ======
  const style = document.createElement("style");
  style.textContent = `
    .efs-col { border:1px solid #e3e3e3; border-radius:8px; padding:8px 10px; margin-bottom:10px; background:#fff; }
    .efs-head { display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:6px; }
    .efs-title { font-weight:600; }
    .efs-search { width:100%; padding:6px 8px; border:1px solid #d0d0d0; border-radius:6px; font-size:12px; }
    .efs-list { margin-top:6px; border:1px solid #eee; border-radius:6px; max-height:220px; overflow:auto; }
    .efs-item { display:flex; align-items:center; gap:6px; padding:6px 8px; border-bottom:1px solid #f5f5f5; font-size:13px; }
    .efs-item:last-child { border-bottom:none; }
    .efs-count { color:#666; margin-left:auto; font-variant-numeric: tabular-nums; }
    .efs-btn { padding:6px 10px; border:1px solid #ccc; border-radius:6px; background:#f7f7f7; cursor:pointer; }
    .efs-btn:hover { background:#efefef; }
  `;
  document.head.appendChild(style);

  // Keep labels click-through
  const style2 = document.createElement("style");
  style2.textContent = `.well-label, .well-label * { pointer-events: none !important; }`;
  document.head.appendChild(style2);

  // ====== Data index ======
  const totalCounts = {}; const uniques = {};
  COLS.forEach(c => { totalCounts[c] = {}; uniques[c] = []; });
  const ALL_ROWS = Array.isArray(ROWS) ? ROWS : [];

  function norm(v){ return (v === null || v === undefined) ? "" : String(v).trim(); }

  const WELL_ROW = {};
  for (const r of ALL_ROWS) {
    if (!("well" in r)) continue;
    const wid = norm(r.well);
    if (!(wid in WELL_ROW)) WELL_ROW[wid] = r; // first-wins
    for (const c of COLS) {
      const val = norm(r[c]);
      totalCounts[c][val] = (totalCounts[c][val] || 0) + 1;
    }
  }
  for (const c of COLS) {
    uniques[c] = Object.keys(totalCounts[c]).sort((a,b)=>{
      if (a === "") return 1;
      if (b === "") return -1;
      return a.localeCompare(b, undefined, {numeric:true, sensitivity:"base"});
    });
  }
  const ALL_WELL_IDS = new Set(Object.keys(WELL_ROW));

  // ====== Selection state ======
  const selected = {}; COLS.forEach(c => selected[c] = new Set());

  // ====== Build listboxes ======
  const columnEls = {};
  for (const c of COLS) {
    const box = document.createElement("div");
    box.className = "efs-col";
    box.innerHTML = `
      <div class="efs-head"><div class="efs-title">${c}</div></div>
      <input class="efs-search" type="text" placeholder="Search ${c}..."/>
      <div class="efs-list"></div>
    `;
    colArea.appendChild(box);

    const listEl = box.querySelector(".efs-list");
    const searchEl = box.querySelector(".efs-search");
    const checkboxes = new Map();
    const countSpans = new Map();

    // Select all head
    const selAllId = `efs-${c}-all-${Math.random().toString(36).slice(2,8)}`;
    const selAll = document.createElement("label");
    selAll.className = "efs-item efs-all";
    selAll.setAttribute("data-role","select-all");
    const selAllChk = document.createElement("input");
    selAllChk.type = "checkbox";
    selAllChk.id = selAllId;
    selAllChk.dataset.col = c;
    selAllChk.dataset.role = "all";
    selAllChk.checked = true;
    const selAllTxt = document.createElement("span"); selAllTxt.textContent = "Select all";
    selAll.appendChild(selAllChk); selAll.appendChild(selAllTxt);
    listEl.appendChild(selAll);

    // Values
    for (const val of uniques[c]) {
      const id = `efs-${c}-${Math.random().toString(36).slice(2,8)}`;
      const row = document.createElement("label");
      row.className = "efs-item";
      row.setAttribute("data-value", val.toLowerCase());

      const chk = document.createElement("input");
      chk.type = "checkbox";
      chk.id = id;
      chk.dataset.col = c;
      chk.dataset.val = val;
      chk.checked = true;                 // start checked
      selected[c].add(val);               // seed all selected

      const txt = document.createElement("span");
      txt.textContent = (val === "") ? "(blank)" : val;

      const cnt = document.createElement("span");
      const tot = totalCounts[c][val] || 0;
      cnt.className = "efs-count";
      cnt.textContent = `(${tot}/${tot})`;

      row.appendChild(chk); row.appendChild(txt); row.appendChild(cnt);
      listEl.appendChild(row);

      checkboxes.set(val, chk);
      countSpans.set(val, cnt);
    }

    // Search filtering (keeps Select All visible)
    searchEl.addEventListener("input", () => {
      const q = searchEl.value.trim().toLowerCase();
      for (const item of listEl.children) {
        if (item.classList.contains("efs-all") || item.getAttribute("data-role")==="select-all") {
          item.style.display = ""; continue;
        }
        const v = item.getAttribute("data-value") || "";
        item.style.display = v.includes(q) ? "" : "none";
      }
    });

    columnEls[c] = { listEl, searchEl, checkboxes, countSpans, selectAll: selAllChk };
  }

  // ====== Matching & counts ======
  function computeMatchedWells(){
    const totalSelected = COLS.reduce((n,c)=> n + selected[c].size, 0);
    if (totalSelected === 0) return new Set(); // nothing selected anywhere → show none
    const matched = new Set();
    for (const wid of ALL_WELL_IDS) {
      const r = WELL_ROW[wid];
      let ok = true;
      for (const c of COLS) {
        const set = selected[c];
        if (set.size === 0) continue;
        const val = norm(r[c]);
        if (!set.has(val)) { ok = false; break; }
      }
      if (ok) matched.add(wid);
    }
    return matched;
  }

  function recomputeAvailableCounts(){
    const availCounts = {};
    for (const c of COLS) {
      availCounts[c] = {};
      const matchedOther = new Set();
      for (const wid of ALL_WELL_IDS) {
        const r = WELL_ROW[wid];
        let ok = true;
        for (const cc of COLS) {
          if (cc === c) continue;
          const set = selected[cc];
          if (set.size === 0) continue;
          const val = norm(r[cc]);
          if (!set.has(val)) { ok = false; break; }
        }
        if (ok) matchedOther.add(wid);
      }
      for (const wid of matchedOther) {
        const r = WELL_ROW[wid];
        const val = norm(r[c]);
        availCounts[c][val] = (availCounts[c][val] || 0) + 1;
      }
    }
    return availCounts;
  }

  function refreshCounts(){
    const availCounts = recomputeAvailableCounts();
    for (const c of COLS) {
      const { countSpans } = columnEls[c];
      for (const val of uniques[c]) {
        const tot = totalCounts[c][val] || 0;
        const ava = availCounts[c][val] || 0;
        const span = countSpans.get(val);
        if (span) span.textContent = `(${ava}/${tot})`;
      }
    }
    return availCounts;
  }

  function updateSelectAllState(col){
    const picked = selected[col].size;
    const total  = uniques[col].length;
    const head   = columnEls[col].selectAll;
    if (!head) return;
    if (picked === 0) { head.checked = false; head.indeterminate = false; }
    else if (picked === total) { head.checked = true; head.indeterminate = false; }
    else { head.checked = false; head.indeterminate = true; }
  }

  // ====== Reorder other lists (available ↑, filtered-out ↓; blank stays last in each group) ======
  function reorderOtherLists(changedCol, availCounts){
    if (!availCounts) availCounts = recomputeAvailableCounts();
    for (const c of COLS) {
      if (c === changedCol) continue;
      const { listEl, checkboxes } = columnEls[c];
      if (!listEl) continue;
      const prevScroll = listEl.scrollTop;

      const availNonBlank = []; let availBlank = null;
      const deadNonBlank = [];  let deadBlank  = null;

      for (const val of uniques[c]) {
        const chk = checkboxes.get(val); if (!chk) continue;
        const rowEl = chk.parentElement;
        const ava = (availCounts[c][val] || 0) > 0;
        const isBlank = (val === "");
        if (ava) { if (isBlank) availBlank = rowEl; else availNonBlank.push(rowEl); }
        else     { if (isBlank) deadBlank  = rowEl; else deadNonBlank.push(rowEl); }
      }

      const frag = document.createDocumentFragment();
      const selAllRow = listEl.querySelector(".efs-all");

      const children = Array.from(listEl.children);
      for (const el of children) if (el !== selAllRow) listEl.removeChild(el);

      for (const el of availNonBlank) frag.appendChild(el);
      if (availBlank) frag.appendChild(availBlank);
      for (const el of deadNonBlank) frag.appendChild(el);
      if (deadBlank) frag.appendChild(deadBlank);

      listEl.appendChild(frag);
      listEl.scrollTop = prevScroll;
    }
  }

  // ====== Map layer indexing & visibility ======
  const MAP = {{ this._parent.get_name() }};
  let LAYERS_BY_WELL = {};

  function classifyLayer(l){
    const p = l?.options?.pane;
    if (p === "wellLabelDisplayed") return "label";
    if (p === "wellHeadInteractive") return "head";
    if (p === "wellTailInteractive") return "tail";
    if (p === "wellSurveyDisplayed") return "survey";
    if (typeof l.getLatLng === "function") {
      const el = (l.getElement && l.getElement()) || l._icon || null;
      if (el && (el.matches?.(".well-label") || el.querySelector?.(".well-label"))) return "label";
      if (l?.options?.icon?.options && ("html" in l.options.icon.options)) return "label";
      return "marker";
    }
    if (typeof l.getLatLngs === "function") return "path";
    return "other";
  }

  function indexLayers(){
    LAYERS_BY_WELL = {};
    function visit(layer){
      if (!layer) return;
      let wid = layer?.options?.__well_id;
      const el = (layer.getElement && layer.getElement()) || layer._icon || null;
      if (!wid && el) {
        const tag = el.matches?.(".well-label") ? el : el.querySelector?.(".well-label");
        const domId = tag?.dataset?.wellId || el?.dataset?.wellId;
        if (domId) { wid = domId; if (layer.options) layer.options.__well_id = wid; }
      }
      if (wid) { (LAYERS_BY_WELL[wid] ||= []).push(layer); layer._efs_kind = classifyLayer(layer); }
      if (typeof layer.eachLayer === "function") layer.eachLayer(visit);
    }
    MAP.eachLayer(visit);
  }
  indexLayers();

  function setLayerVisible(layer, visible){
    try {
      if (typeof layer.eachLayer === "function" && !layer.getLatLng) {
        layer.eachLayer(ch => setLayerVisible(ch, visible)); return;
      }
      if (typeof layer.getLatLng === "function") {
        if (typeof layer.setOpacity === "function") layer.setOpacity(visible ? 1 : 0);
        const el = (layer.getElement && layer.getElement()) || layer._icon || null;
        if (el) {
          el.style.display = visible ? "" : "none";
          const isLabel = (layer._efs_kind === "label") || el.classList.contains("well-label-icon");
          el.style.pointerEvents = isLabel ? "none" : (visible ? "auto" : "none");
        }
        return;
      }
      if (typeof layer.setStyle === "function") {
        if (layer._efs_origOpacity == null) layer._efs_origOpacity = (layer.options.opacity ?? 0.9);
        if (layer._efs_origFillOpacity == null) layer._efs_origFillOpacity = (layer.options.fillOpacity ?? 0.8);
        layer.setStyle({ opacity: visible ? layer._efs_origOpacity : 0, fillOpacity: visible ? layer._efs_origFillOpacity : 0 });
        if (visible && layer.bringToFront) layer.bringToFront();
        const pathEl = layer._path; if (pathEl && pathEl.style) pathEl.style.pointerEvents = visible ? "auto" : "none";
        return;
      }
      if (visible) { if (!MAP.hasLayer(layer)) layer.addTo(MAP); }
      else { if (MAP.hasLayer(layer)) MAP.removeLayer(layer); }
    } catch(e){ console.warn("CategoricalFilterSidebar visibility error:", e); }
  }

  function applyVisibility(matchedSet){
    indexLayers(); // catch late-created icons
    if (matchedSet.size === 0) {
      for (const wid of Object.keys(LAYERS_BY_WELL)) for (const lyr of LAYERS_BY_WELL[wid]) setLayerVisible(lyr, false);
      return;
    }
    for (const wid of Object.keys(LAYERS_BY_WELL)) {
      const vis = matchedSet.has(wid);
      for (const lyr of LAYERS_BY_WELL[wid]) setLayerVisible(lyr, vis);
    }
  }

  // ====== Events ======
  function updateSelectAllState(col){
    const picked = selected[col].size;
    const total  = uniques[col].length;
    const head   = columnEls[col].selectAll;
    if (!head) return;
    if (picked === 0) { head.checked = false; head.indeterminate = false; }
    else if (picked === total) { head.checked = true; head.indeterminate = false; }
    else { head.checked = false; head.indeterminate = true; }
  }

  function onToggle(e){
    const input = e.target;
    if (!input || input.tagName !== "INPUT" || input.type !== "checkbox") return;

    const c = input.dataset.col;
    const val = input.dataset.val;
    const role = input.dataset.role || "";
    if (!c) return;

    if (role === "all") {
      selected[c].clear();
      if (input.checked) {
        for (const v of uniques[c]) selected[c].add(v);
        for (const [v, chk] of columnEls[c].checkboxes) chk.checked = true;
      } else {
        for (const [v, chk] of columnEls[c].checkboxes) chk.checked = false;
      }
      const matched = computeMatchedWells();
      applyVisibility(matched);
      const avail = refreshCounts();
      updateSelectAllState(c);
      reorderOtherLists(c, avail);
      return;
    }

    if (input.checked) selected[c].add(val);
    else selected[c].delete(val);

    const matched = computeMatchedWells();
    applyVisibility(matched);
    const avail = refreshCounts();
    updateSelectAllState(c);
    reorderOtherLists(c, avail);
  }

  for (const c of COLS) columnEls[c].listEl.addEventListener("change", onToggle);

  wrap.querySelector("#efs-reset").addEventListener("click", () => {
    for (const c of COLS) {
      selected[c].clear();
      for (const val of uniques[c]) selected[c].add(val);
      for (const [_, chk] of columnEls[c].checkboxes) chk.checked = true;
      const head = columnEls[c].selectAll; if (head) { head.checked = true; head.indeterminate = false; }
    }
    const matched = computeMatchedWells();
    applyVisibility(matched);
    const avail = refreshCounts();
    reorderOtherLists(null, avail);
  });

  // ====== Initial paint ======
  refreshCounts();
  applyVisibility(computeMatchedWells());
  for (const c of COLS) updateSelectAllState(c);
})();
{% endmacro %}
""")

    def __init__(
        self,
        rows: list[dict],
        cols: list[str],
        container_id: str = "sidebar",
        position: str = "left",
        visible: bool = True,
        autopan: bool = False,
        sidebar_html: str | None = None,
    ):
        super().__init__()
        self._name = "CategoricalFilterSidebar"
        self.container_id = container_id
        self.position = position.lower()
        self.autopan = autopan
        self.visible = visible
        self.sidebar_html = (sidebar_html or self.DEFAULT_HTML)

        # Data for JS
        self._rows_json = json.dumps(rows, ensure_ascii=False)
        self._cols_json = json.dumps(cols, ensure_ascii=False)

        # Sidebar DOM
        self._html_element = Element(self.sidebar_html)

        # Load Leaflet Sidebar assets that your previous FilterSidebar used
        css_text = Path("L.Control.Sidebar.css").read_text(encoding="utf-8")
        js_text  = Path("L.Control.Sidebar.js").read_text(encoding="utf-8")
        self._css_element = Element(f"<style>\n{css_text}\n</style>")
        self._js_element  = Element(f"<script>\n{js_text}\n</script>")

    def render(self, **kwargs):
        # Attach CSS & JS into the <head>, then the HTML container into the body
        fig = self.get_root()
        if hasattr(fig, "header"):
            fig.header.add_child(self._css_element, name="leaflet-sidebar-css")
            fig.header.add_child(self._js_element, name="leaflet-sidebar-js")
        else:
            fig.html.add_child(self._css_element, name="leaflet-sidebar-css")
            fig.html.add_child(self._js_element, name="leaflet-sidebar-js")

        target = getattr(fig, "html", fig)
        target.add_child(self._html_element, name=f"{self._name}-container-{self.container_id}")

        super().render(**kwargs)

    def add_to(self, m):
        m.add_child(self)
        return self

const ARCHIE_SETTINGS_ROOT_ATTR = "data-archie-settings-root";

const DEFAULT_GRID = {
    show: true,
    width: 0.05,
    color: "#20305f",
    alpha: 0.55,
    minor: {
        show: false,
        width: 0.03,
        color: "#20305f",
        alpha: 0.25
    }
};

const DEFAULT_SEPARATOR = {
    show: true,
    width: 1,
    color: "#20305f",
    alpha: 0.9
};

const DEFAULT_STATE = {
    fileName: "No file",
    las: null,
    nullValue: "",
    depthTop: "",
    depthBase: "",
    trailCount: 3,
    trailGap: 0.012,
    trails: [],
    grid: DEFAULT_GRID,
    separator: DEFAULT_SEPARATOR
};

function clamp(n, min, max) {
    return Math.max(min, Math.min(max, n));
}

function toNumber(value) {
    if (value === "" || value == null) return null;
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
}

function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, (m) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "\"": "&quot;",
        "'": "&#39;"
    }[m]));
}

function toRgba(hex, alpha) {
    if (!hex || typeof hex !== "string") return `rgba(32, 48, 95, ${alpha ?? 0.6})`;
    const raw = hex.replace("#", "").trim();
    if (raw.length !== 6) return `rgba(32, 48, 95, ${alpha ?? 0.6})`;
    const r = parseInt(raw.slice(0, 2), 16);
    const g = parseInt(raw.slice(2, 4), 16);
    const b = parseInt(raw.slice(4, 6), 16);
    if (![r, g, b].every(Number.isFinite)) {
        return `rgba(32, 48, 95, ${alpha ?? 0.6})`;
    }
    const a = Number.isFinite(alpha) ? alpha : 0.6;
    return `rgba(${r}, ${g}, ${b}, ${a})`;
}

function formatDepth(value) {
    const n = (typeof value === "number") ? value : Number(value);
    if (!Number.isFinite(n)) return "-";
    return Math.abs(n) >= 1000 ? n.toFixed(1) : n.toFixed(3);
}

function normalizeTrails(trails, count) {
    const target = Math.max(1, Number(count) || 1);
    const next = [];
    const existing = Array.isArray(trails) ? trails : [];

    for (let i = 0; i < target; i += 1) {
        const id = i + 1;
        const prev = existing.find((t) => t.id === id) || existing[i] || {};
        const curves = prev.curves instanceof Set
            ? new Set(prev.curves)
            : new Set(Array.isArray(prev.curves) ? prev.curves : []);
        next.push({
            id,
            xMin: prev.xMin ?? "",
            xMax: prev.xMax ?? "",
            curves
        });
    }

    return next;
}

function parseLAS(text, forcedNullValue = null) {
    const lines = text.split(/\r?\n/);

    const idxCurve = lines.findIndex((line) => /^\s*~\s*C/i.test(line));
    const idxAscii = lines.findIndex((line) => /^\s*~\s*A/i.test(line));
    if (idxAscii === -1) {
        throw new Error("LAS parser: '~A' (ASCII data) section not found.");
    }

    let nullVal = null;
    for (const line of lines) {
        const match = line.match(/^\s*NULL\s*\.\s*([+-]?\d+(\.\d+)?)/i);
        if (match) {
            nullVal = Number(match[1]);
            break;
        }
    }

    if (forcedNullValue != null && forcedNullValue !== "") {
        const n = Number(forcedNullValue);
        if (!Number.isNaN(n)) nullVal = n;
    }

    const curveNames = [];
    if (idxCurve !== -1 && idxCurve < idxAscii) {
        for (let i = idxCurve + 1; i < idxAscii; i += 1) {
            const raw = lines[i];
            if (!raw || /^\s*~/.test(raw)) break;
            if (/^\s*#/.test(raw)) continue;
            let match = raw.match(/^\s*([A-Za-z0-9_\/-]+)\s*\./);
            if (!match) match = raw.match(/^\s*([A-Za-z0-9_\/-]+)/);
            if (match) curveNames.push(match[1].trim());
        }
    }

    const dataRows = [];
    for (let i = idxAscii + 1; i < lines.length; i += 1) {
        const raw = lines[i];
        if (!raw) continue;
        if (/^\s*~/.test(raw)) break;
        if (/^\s*#/.test(raw)) continue;

        const parts = raw.trim().split(/\s+/);
        if (parts.length < 2) continue;

        const nums = parts.map((part) => {
            const v = Number(part);
            return Number.isFinite(v) ? v : null;
        });
        if (nums.some((v) => v !== null)) dataRows.push(nums);
    }

    if (!dataRows.length) {
        throw new Error("LAS parser: no numeric rows found under '~A'.");
    }

    const nCols = dataRows[0].length;
    let names = curveNames.slice(0, nCols);
    if (names.length !== nCols) {
        names = Array.from({ length: nCols }, (_, i) => (i === 0 ? "DEPT" : `CURVE_${i}`));
    }
    names[0] = names[0] || "DEPT";

    const cols = Object.fromEntries(names.map((name) => [name, []]));
    for (const row of dataRows) {
        for (let c = 0; c < nCols; c += 1) {
            const v = (c < row.length) ? row[c] : null;
            cols[names[c]].push(v);
        }
    }

    if (nullVal != null && Number.isFinite(nullVal)) {
        for (const key of Object.keys(cols)) {
            cols[key] = cols[key].map((v) => (v === nullVal ? null : v));
        }
    }

    const depthKey = names[0];
    const depth = cols[depthKey];

    const curves = {};
    for (const key of names.slice(1)) curves[key] = cols[key];

    const finiteDepth = depth.filter((v) => Number.isFinite(v));
    const dmin = Math.min(...finiteDepth);
    const dmax = Math.max(...finiteDepth);

    return {
        depthKey,
        depth,
        curves,
        nullValue: nullVal,
        depthMin: dmin,
        depthMax: dmax
    };
}

function buildLogFigure(state) {
    const trails = Array.isArray(state.trails) && state.trails.length
        ? state.trails
        : normalizeTrails([], state.trailCount);
    const gap = clamp(Number(state.trailGap) || 0, 0, 0.05);

    const layout = {
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        margin: { l: 68, r: 24, t: 28, b: 44 },
        showlegend: true,
        legend: {
            orientation: "h",
            x: 0,
            y: 1.08,
            font: { size: 11, color: "#1f2937" },
            bgcolor: "rgba(255,255,255,0.85)",
            bordercolor: "rgba(0,0,0,0.1)",
            borderwidth: 1
        },
        hovermode: "closest",
        uirevision: "archie",
        yaxis: {
            autorange: "reversed",
            showgrid: !!state.grid?.show,
            gridcolor: toRgba(state.grid?.color, state.grid?.alpha),
            gridwidth: Number(state.grid?.width) || 0.5,
            zeroline: false,
            ticks: "outside",
            tickfont: { size: 11 }
        },
        shapes: []
    };

    if (state.grid?.minor?.show) {
        layout.yaxis.minor = {
            showgrid: true,
            gridcolor: toRgba(state.grid.minor.color, state.grid.minor.alpha),
            gridwidth: Number(state.grid.minor.width) || 0.25
        };
    }

    const depthRange = (() => {
        const top = toNumber(state.depthTop);
        const base = toNumber(state.depthBase);
        if (top == null || base == null) return null;
        return [base, top];
    })();

    if (depthRange) {
        layout.yaxis.range = depthRange;
    }

    const totalGap = gap * (trails.length - 1);
    const width = (1 - totalGap) / trails.length;
    const data = [];

    const las = state.las;
    const curveNames = las ? Object.keys(las.curves) : [];

    trails.forEach((trail, index) => {
        const xref = index === 0 ? "x" : `x${index + 1}`;
        const axisKey = index === 0 ? "xaxis" : `xaxis${index + 1}`;

        const start = index * (width + gap);
        const end = start + width;

        if (index > 0 && state.separator?.show) {
            layout.shapes.push({
                type: "line",
                xref: "paper",
                yref: "paper",
                x0: start - gap / 2,
                x1: start - gap / 2,
                y0: 0,
                y1: 1,
                line: {
                    width: Number(state.separator?.width) || 1,
                    color: toRgba(state.separator?.color, state.separator?.alpha)
                }
            });
        }

        const xmin = toNumber(trail.xMin);
        const xmax = toNumber(trail.xMax);
        const hasRange = xmin != null && xmax != null && xmin !== xmax;

        layout[axisKey] = {
            domain: [start, end],
            showgrid: !!state.grid?.show,
            gridcolor: toRgba(state.grid?.color, state.grid?.alpha),
            gridwidth: Number(state.grid?.width) || 0.5,
            zeroline: false,
            ticks: "outside",
            tickfont: { size: 11 },
            range: hasRange ? [xmin, xmax] : undefined
        };

        if (!las) return;

        trail.curves.forEach((curveName) => {
            if (!curveNames.includes(curveName)) return;
            const x = las.curves[curveName];
            const y = las.depth;
            if (!x || !y) return;

            data.push({
                type: "scattergl",
                mode: "lines",
                name: `T${trail.id}: ${curveName}`,
                x,
                y,
                xaxis: xref,
                yaxis: "y",
                connectgaps: false,
                hovertemplate: `${escapeHtml(curveName)}<br>Depth: %{y:.3f}<br>Value: %{x:.6g}<extra></extra>`
            });
        });
    });

    const selectedCount = trails.reduce((acc, trail) => acc + trail.curves.size, 0);

    if (!las) {
        layout.annotations = [{
            xref: "paper",
            yref: "paper",
            x: 0.5,
            y: 0.5,
            text: "Load a LAS file to plot curves.",
            showarrow: false,
            font: { size: 14, color: "#5b6b8c" }
        }];
    } else if (!selectedCount) {
        layout.annotations = [{
            xref: "paper",
            yref: "paper",
            x: 0.5,
            y: 0.5,
            text: "Select curves in Trail Settings, then render.",
            showarrow: false,
            font: { size: 14, color: "#5b6b8c" }
        }];
    }

    const config = {
        responsive: true,
        displaylogo: false,
        scrollZoom: true,
        modeBarButtonsToRemove: ["lasso2d", "select2d"]
    };

    return { data, layout, config };
}

export function createArchieState(overrides = {}) {
    const state = {
        ...DEFAULT_STATE,
        ...overrides,
        grid: {
            ...DEFAULT_GRID,
            ...(overrides.grid || {}),
            minor: {
                ...DEFAULT_GRID.minor,
                ...((overrides.grid && overrides.grid.minor) || {})
            }
        },
        separator: {
            ...DEFAULT_SEPARATOR,
            ...(overrides.separator || {})
        }
    };

    state.trailCount = Math.max(1, Number(state.trailCount) || 1);
    state.trails = normalizeTrails(state.trails, state.trailCount);
    return state;
}

export function renderArchieSettings({ root } = {}) {
    if (!root) return;

    root.innerHTML = `
        <div class="settings-panel" ${ARCHIE_SETTINGS_ROOT_ATTR}="true">
            <div class="settings-heading">Suite Settings</div>
            <div class="settings-section">Depth Range</div>
            <div class="settings-row">
                <label class="settings-field">
                    <span class="settings-label">Top Depth</span>
                    <input class="settings-input" type="number" step="any" placeholder="e.g., 1000" data-role="top-depth" />
                </label>
                <label class="settings-field">
                    <span class="settings-label">Base Depth</span>
                    <input class="settings-input" type="number" step="any" placeholder="e.g., 2000" data-role="base-depth" />
                </label>
            </div>
            <div class="settings-actions">
                <button class="settings-button" type="button" data-action="apply-depths">Apply depths</button>
            </div>

            <div class="settings-section">Trail Controls</div>
            <div class="settings-row">
                <label class="settings-field">
                    <span class="settings-label">Trail Count</span>
                    <input class="settings-input" type="number" min="1" step="1" max="10" data-role="trail-count" />
                </label>
                <label class="settings-field">
                    <span class="settings-label">Trail gap</span>
                    <input class="settings-input" type="number" min="0" max="0.1" step="0.005" data-role="trail-gap" />
                </label>
            </div>

            <div class="settings-section">Grid Settings</div>
            <label class="settings-field settings-checkbox">
                <input type="checkbox" data-role="grid-show" />
                <span class="settings-label">Show grid</span>
            </label>
            <label class="settings-field">
                <span class="settings-label">Width</span>
                <input class="settings-input" type="number" min="0" step="0.05" data-role="grid-width" />
            </label>
            <label class="settings-field">
                <span class="settings-label">Color</span>
                <input class="settings-input" type="color" data-role="grid-color" />
            </label>
            <label class="settings-field">
                <span class="settings-label">Alpha</span>
                <input class="settings-input" type="number" min="0" max="1" step="0.05" data-role="grid-alpha" />
            </label>

            <div class="settings-section">Minor Grid</div>
            <label class="settings-field settings-checkbox">
                <input type="checkbox" data-role="grid-minor-show" />
                <span class="settings-label">Show minors</span>
            </label>
            <label class="settings-field">
                <span class="settings-label">Width</span>
                <input class="settings-input" type="number" min="0" step="0.05" data-role="grid-minor-width" />
            </label>
            <label class="settings-field">
                <span class="settings-label">Color</span>
                <input class="settings-input" type="color" data-role="grid-minor-color" />
            </label>
            <label class="settings-field">
                <span class="settings-label">Alpha</span>
                <input class="settings-input" type="number" min="0" max="1" step="0.05" data-role="grid-minor-alpha" />
            </label>

            <div class="settings-section">Separator</div>
            <label class="settings-field settings-checkbox">
                <input type="checkbox" data-role="separator-show" />
                <span class="settings-label">Show separator</span>
            </label>
            <label class="settings-field">
                <span class="settings-label">Width</span>
                <input class="settings-input" type="number" step="0.05" data-role="separator-width" />
            </label>
            <label class="settings-field">
                <span class="settings-label">Color</span>
                <input class="settings-input" type="color" data-role="separator-color" />
            </label>
            <label class="settings-field">
                <span class="settings-label">Alpha</span>
                <input class="settings-input" type="number" min="0" max="1" step="0.05" data-role="separator-alpha" />
            </label>

            <div class="settings-section">Trail</div>
            <label class="settings-field">
                <span class="settings-label">Choose trail</span>
                <select class="settings-input" data-role="trail-select"></select>
            </label>
            <div class="trail-panel" data-role="trail-panel"></div>
        </div>
    `;
}

export function createArchiePanel({
    root,
    trailTemplateId = "trailSettingsTemplate",
    state = createArchieState()
} = {}) {
    if (!root) {
        throw new Error("createArchiePanel requires a root element.");
    }

    let settingsRoot = null;
    let renderRaf = 0;
    let plotHost = null;
    let disposed = false;
    const disposers = [];

    function addListener(target, type, handler, options) {
        if (!target || !target.addEventListener) return;
        target.addEventListener(type, handler, options);
        disposers.push(() => target.removeEventListener(type, handler, options));
    }

    function clearDisposers() {
        while (disposers.length) {
            const dispose = disposers.pop();
            dispose();
        }
    }

    function setStatus(message) {
        if (!settingsRoot) return;
        const status = settingsRoot.querySelector('[data-role="load-status"]');
        if (!status) return;
        status.textContent = message;
    }

    function scheduleRender() {
        if (disposed) return;
        if (renderRaf) return;
        renderRaf = window.requestAnimationFrame(() => {
            renderRaf = 0;
            renderPlot();
        });
    }

    function renderPlot() {
        if (!plotHost) return;
        if (!window.Plotly) {
            plotHost.innerHTML = "<div class=\"status\">Plotly is not available.</div>";
            return;
        }
        const fig = buildLogFigure(state);
        window.Plotly.react(plotHost, fig.data, fig.layout, fig.config);
    }

    function renderTrailSettings(trailEl, trail) {
        const tpl = document.getElementById(trailTemplateId);
        if (!tpl) {
            trailEl.innerHTML = "<div class=\"status\">Trail template not found.</div>";
            return;
        }

        const fragment = tpl.content.cloneNode(true);
        const titleEl = fragment.querySelector('[data-role="trail-title"]');
        if (titleEl) titleEl.textContent = `Trail ${trail.id}`;

        const bindLabel = (labelRole, inputRole, suffix) => {
            const label = fragment.querySelector(`[data-role="${labelRole}"]`);
            const input = fragment.querySelector(`[data-role="${inputRole}"]`);
            if (!label || !input) return;
            const id = `trail-${trail.id}-${suffix}`;
            input.id = id;
            label.setAttribute("for", id);
        };

        bindLabel("xmin-label", "xmin-input", "xmin");
        bindLabel("xmax-label", "xmax-input", "xmax");

        const xminInput = fragment.querySelector('[data-field="xMin"]');
        const xmaxInput = fragment.querySelector('[data-field="xMax"]');
        if (xminInput) xminInput.value = trail.xMin ?? "";
        if (xmaxInput) xmaxInput.value = trail.xMax ?? "";

        const list = fragment.querySelector(".curve-list");
        if (list) {
            if (!state.las) {
                list.innerHTML = "<div class=\"status\">No curves loaded.</div>";
            } else {
                list.innerHTML = "";
                Object.keys(state.las.curves).forEach((curveName) => {
                    const item = document.createElement("label");
                    item.className = "curve-item";

                    const checkbox = document.createElement("input");
                    checkbox.type = "checkbox";
                    checkbox.dataset.curve = curveName;
                    checkbox.checked = trail.curves.has(curveName);

                    const text = document.createElement("span");
                    text.textContent = curveName;

                    const tag = document.createElement("small");
                    tag.textContent = checkbox.checked ? "selected" : "";

                    item.appendChild(checkbox);
                    item.appendChild(text);
                    item.appendChild(tag);
                    list.appendChild(item);
                });
            }
        }

        trailEl.innerHTML = "";
        trailEl.appendChild(fragment);

        trailEl.addEventListener("input", (event) => {
            const field = event.target?.dataset?.field;
            if (!field) return;
            if (field === "xMin") {
                trail.xMin = event.target.value;
            } else if (field === "xMax") {
                trail.xMax = event.target.value;
            }
            scheduleRender();
        });

        trailEl.addEventListener("change", (event) => {
            const input = event.target;
            if (!(input instanceof HTMLInputElement)) return;
            const curve = input.dataset.curve;
            if (!curve) return;

            if (input.checked) {
                trail.curves.add(curve);
            } else {
                trail.curves.delete(curve);
            }

            const small = input.closest(".curve-item")?.querySelector("small");
            if (small) small.textContent = input.checked ? "selected" : "";
            scheduleRender();
        });

        trailEl.querySelector('[data-action="clearTrail"]')?.addEventListener("click", () => {
            trail.curves.clear();
            scheduleRender();
            rebuildTrailsUI();
        });
    }

    function rebuildTrailsUI() {
        if (!settingsRoot) return;
        const select = settingsRoot.querySelector('[data-role="trail-select"]');
        const panel = settingsRoot.querySelector('[data-role="trail-panel"]');
        if (!select || !panel) return;

        const prevSelected = Number(select.value) || 1;
        const trails = normalizeTrails(state.trails, state.trailCount);
        state.trails = trails;

        const frag = document.createDocumentFragment();
        const trailEls = new Map();

        trails.forEach((trail) => {
            const option = document.createElement("option");
            option.value = String(trail.id);
            option.textContent = `Trail ${trail.id}`;
            frag.appendChild(option);

            const trailEl = document.createElement("div");
            trailEl.className = "trail";
            trailEl.dataset.trailId = String(trail.id);
            renderTrailSettings(trailEl, trail);
            trailEls.set(String(trail.id), trailEl);
        });

        select.replaceChildren(frag);

        const fallbackId = Number.isFinite(prevSelected) ? prevSelected : trails[0]?.id;
        const maxId = trails[trails.length - 1]?.id ?? 1;
        const selectedId = clamp(fallbackId, 1, maxId);

        const showTrail = (id) => {
            const el = trailEls.get(String(id));
            if (!el) {
                panel.innerHTML = "<div class=\"status\">Trail not found.</div>";
                return;
            }
            panel.replaceChildren(el);
        };

        select.value = String(selectedId);
        showTrail(selectedId);

        select.onchange = () => {
            showTrail(Number(select.value));
        };
    }

    function autoSelectCurves() {
        if (!state.las) return;
        const curveNames = Object.keys(state.las.curves);
        state.trails.forEach((trail) => trail.curves.clear());
        let idx = 0;
        state.trails.forEach((trail) => {
            const take = Math.max(1, Math.min(2, curveNames.length - idx));
            for (let i = 0; i < take && idx < curveNames.length; i += 1) {
                trail.curves.add(curveNames[idx]);
                idx += 1;
            }
        });
    }

    function applySettingsState() {
        if (!settingsRoot) return;
        const trailCount = settingsRoot.querySelector('[data-role="trail-count"]');
        const trailGap = settingsRoot.querySelector('[data-role="trail-gap"]');
        const topDepth = settingsRoot.querySelector('[data-role="top-depth"]');
        const baseDepth = settingsRoot.querySelector('[data-role="base-depth"]');
        const nullValue = settingsRoot.querySelector('[data-role="null-value"]');

        const gridShow = settingsRoot.querySelector('[data-role="grid-show"]');
        const gridWidth = settingsRoot.querySelector('[data-role="grid-width"]');
        const gridColor = settingsRoot.querySelector('[data-role="grid-color"]');
        const gridAlpha = settingsRoot.querySelector('[data-role="grid-alpha"]');

        const gridMinorShow = settingsRoot.querySelector('[data-role="grid-minor-show"]');
        const gridMinorWidth = settingsRoot.querySelector('[data-role="grid-minor-width"]');
        const gridMinorColor = settingsRoot.querySelector('[data-role="grid-minor-color"]');
        const gridMinorAlpha = settingsRoot.querySelector('[data-role="grid-minor-alpha"]');

        const separatorShow = settingsRoot.querySelector('[data-role="separator-show"]');
        const separatorWidth = settingsRoot.querySelector('[data-role="separator-width"]');
        const separatorColor = settingsRoot.querySelector('[data-role="separator-color"]');
        const separatorAlpha = settingsRoot.querySelector('[data-role="separator-alpha"]');

        if (trailCount) trailCount.value = String(state.trailCount || 1);
        if (trailGap) trailGap.value = String(state.trailGap ?? 0.01);
        if (topDepth) topDepth.value = state.depthTop ?? "";
        if (baseDepth) baseDepth.value = state.depthBase ?? "";
        if (nullValue) nullValue.value = state.nullValue ?? "";

        if (gridShow) gridShow.checked = !!state.grid?.show;
        if (gridWidth) gridWidth.value = String(state.grid?.width ?? 0.05);
        if (gridColor) gridColor.value = state.grid?.color ?? "#20305f";
        if (gridAlpha) gridAlpha.value = String(state.grid?.alpha ?? 0.55);

        if (gridMinorShow) gridMinorShow.checked = !!state.grid?.minor?.show;
        if (gridMinorWidth) gridMinorWidth.value = String(state.grid?.minor?.width ?? 0.03);
        if (gridMinorColor) gridMinorColor.value = state.grid?.minor?.color ?? "#20305f";
        if (gridMinorAlpha) gridMinorAlpha.value = String(state.grid?.minor?.alpha ?? 0.25);

        if (separatorShow) separatorShow.checked = !!state.separator?.show;
        if (separatorWidth) separatorWidth.value = String(state.separator?.width ?? 1);
        if (separatorColor) separatorColor.value = state.separator?.color ?? "#20305f";
        if (separatorAlpha) separatorAlpha.value = String(state.separator?.alpha ?? 0.9);
    }

    function bindSettings(rootEl) {
        clearDisposers();
        settingsRoot = rootEl;
        applySettingsState();
        rebuildTrailsUI();
        if (state.las) {
            setStatus(`Loaded: ${state.fileName || "LAS"} | Curves: ${Object.keys(state.las.curves).length}`);
        } else {
            setStatus("No LAS loaded.");
        }

        const lasFile = settingsRoot.querySelector('[data-role="las-file"]');
        const nullValue = settingsRoot.querySelector('[data-role="null-value"]');
        const topDepth = settingsRoot.querySelector('[data-role="top-depth"]');
        const baseDepth = settingsRoot.querySelector('[data-role="base-depth"]');
        const applyDepths = settingsRoot.querySelector('[data-action="apply-depths"]');
        const trailCount = settingsRoot.querySelector('[data-role="trail-count"]');
        const trailGap = settingsRoot.querySelector('[data-role="trail-gap"]');

        const gridShow = settingsRoot.querySelector('[data-role="grid-show"]');
        const gridWidth = settingsRoot.querySelector('[data-role="grid-width"]');
        const gridColor = settingsRoot.querySelector('[data-role="grid-color"]');
        const gridAlpha = settingsRoot.querySelector('[data-role="grid-alpha"]');

        const gridMinorShow = settingsRoot.querySelector('[data-role="grid-minor-show"]');
        const gridMinorWidth = settingsRoot.querySelector('[data-role="grid-minor-width"]');
        const gridMinorColor = settingsRoot.querySelector('[data-role="grid-minor-color"]');
        const gridMinorAlpha = settingsRoot.querySelector('[data-role="grid-minor-alpha"]');

        const separatorShow = settingsRoot.querySelector('[data-role="separator-show"]');
        const separatorWidth = settingsRoot.querySelector('[data-role="separator-width"]');
        const separatorColor = settingsRoot.querySelector('[data-role="separator-color"]');
        const separatorAlpha = settingsRoot.querySelector('[data-role="separator-alpha"]');

        addListener(lasFile, "change", async () => {
            const file = lasFile?.files?.[0];
            if (!file) return;
            state.fileName = file.name;
            try {
                const text = await file.text();
                state.las = parseLAS(text, nullValue?.value || null);
                state.depthTop = String(state.las.depthMin);
                state.depthBase = String(state.las.depthMax);
                setStatus(`Loaded: ${file.name} | Curves: ${Object.keys(state.las.curves).length}`);
                autoSelectCurves();
                applySettingsState();
                rebuildTrailsUI();
                scheduleRender();
            } catch (err) {
                state.las = null;
                setStatus(String(err?.message || err));
                rebuildTrailsUI();
                scheduleRender();
            }
        });

        addListener(nullValue, "input", () => {
            state.nullValue = nullValue.value;
        });

        addListener(topDepth, "input", () => {
            state.depthTop = topDepth.value;
        });

        addListener(baseDepth, "input", () => {
            state.depthBase = baseDepth.value;
        });

        addListener(applyDepths, "click", () => {
            state.depthTop = topDepth?.value ?? "";
            state.depthBase = baseDepth?.value ?? "";
            scheduleRender();
        });

        addListener(trailCount, "change", () => {
            state.trailCount = Math.max(1, Number(trailCount.value) || 1);
            state.trails = normalizeTrails(state.trails, state.trailCount);
            rebuildTrailsUI();
            scheduleRender();
        });

        addListener(trailGap, "input", () => {
            state.trailGap = Number(trailGap.value);
            scheduleRender();
        });

        addListener(gridShow, "change", () => {
            state.grid.show = gridShow.checked;
            scheduleRender();
        });

        addListener(gridWidth, "input", () => {
            state.grid.width = Number(gridWidth.value);
            scheduleRender();
        });

        addListener(gridColor, "input", () => {
            state.grid.color = gridColor.value;
            scheduleRender();
        });

        addListener(gridAlpha, "input", () => {
            state.grid.alpha = Number(gridAlpha.value);
            scheduleRender();
        });

        addListener(gridMinorShow, "change", () => {
            state.grid.minor.show = gridMinorShow.checked;
            scheduleRender();
        });

        addListener(gridMinorWidth, "input", () => {
            state.grid.minor.width = Number(gridMinorWidth.value);
            scheduleRender();
        });

        addListener(gridMinorColor, "input", () => {
            state.grid.minor.color = gridMinorColor.value;
            scheduleRender();
        });

        addListener(gridMinorAlpha, "input", () => {
            state.grid.minor.alpha = Number(gridMinorAlpha.value);
            scheduleRender();
        });

        addListener(separatorShow, "change", () => {
            state.separator.show = separatorShow.checked;
            scheduleRender();
        });

        addListener(separatorWidth, "input", () => {
            state.separator.width = Number(separatorWidth.value);
            scheduleRender();
        });

        addListener(separatorColor, "input", () => {
            state.separator.color = separatorColor.value;
            scheduleRender();
        });

        addListener(separatorAlpha, "input", () => {
            state.separator.alpha = Number(separatorAlpha.value);
            scheduleRender();
        });
    }

    function initPanel() {
        root.innerHTML = "";
        plotHost = root;

        renderPlot();
    }

    initPanel();

    return {
        state,
        bindSettings,
        render: scheduleRender,
        resize: () => {
            if (plotHost && window.Plotly?.Plots?.resize) {
                window.Plotly.Plots.resize(plotHost);
            }
        },
        destroy: () => {
            disposed = true;
            if (renderRaf) {
                window.cancelAnimationFrame(renderRaf);
                renderRaf = 0;
            }
            clearDisposers();
            if (plotHost && window.Plotly?.purge) {
                window.Plotly.purge(plotHost);
            }
            root.innerHTML = "";
        }
    };
}

export { ARCHIE_SETTINGS_ROOT_ATTR };

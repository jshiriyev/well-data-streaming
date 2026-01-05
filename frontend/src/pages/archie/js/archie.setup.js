import { SUITE, TRAIL } from "./session.state.js";

const widget = {
    trailCount: document.getElementById("trailCount"),
    trailGap: document.getElementById("trailGap"),

    topDepth: document.getElementById("topDepth"),
    baseDepth: document.getElementById("baseDepth"),

    fitUserDepthBtn: document.getElementById("fitUserDepthBtn"),

    gridShow: document.getElementById("gridShow"),
    gridWidth: document.getElementById("gridWidth"),
    gridColor: document.getElementById("gridColor"),
    gridAlpha: document.getElementById("gridAlpha"),

    gridMinorShow: document.getElementById("gridMinorShow"),
    gridMinorWidth: document.getElementById("gridMinorWidth"),
    gridMinorColor: document.getElementById("gridMinorColor"),
    gridMinorAlpha: document.getElementById("gridMinorAlpha"),

    separatorShow: document.getElementById("separatorShow"),
    separatorWidth: document.getElementById("separatorWidth"),
    separatorColor: document.getElementById("separatorColor"),
    separatorAlpha: document.getElementById("separatorAlpha"),

    trailSelect: document.getElementById("trailSelect"),

    logHead: document.getElementById("logHead"),
    logBody: document.getElementById("logBody"),
    logDivider: document.querySelector(".log-divider"),
};

function initLogDividerResize() {
    const logSuite = document.querySelector(".log-suite");
    if (!widget.logHead || !widget.logBody || !widget.logDivider || !logSuite) return;

    const minHeadHeight = 60;
    const minBodyHeight = 160;
    let isResizing = false;
    let startY = 0;
    let startHeadHeight = 0;
    let resizeRaf = null;

    const clampHeadHeight = (nextHeight) => {
        const total = logSuite.clientHeight - widget.logDivider.offsetHeight;
        const maxHead = Math.max(0, total - minBodyHeight);
        const minHead = Math.min(minHeadHeight, maxHead);
        return Math.max(minHead, Math.min(maxHead, nextHeight));
    };

    const applyHeadHeight = (nextHeight) => {
        const clamped = clampHeadHeight(nextHeight);
        widget.logHead.style.height = `${Math.round(clamped)}px`;
        widget.logHead.style.flex = "0 0 auto";
        widget.logBody.style.flex = "1 1 auto";
    };

    const schedulePlotResize = () => {
        if (!window.Plotly?.Plots?.resize) return;
        if (resizeRaf) return;
        resizeRaf = requestAnimationFrame(() => {
            resizeRaf = null;
            if (widget.logHead) Plotly.Plots.resize(widget.logHead);
            if (widget.logBody) Plotly.Plots.resize(widget.logBody);
        });
    };

    const onPointerMove = (event) => {
        if (!isResizing) return;
        const delta = event.clientY - startY;
        applyHeadHeight(startHeadHeight + delta);
        schedulePlotResize();
    };

    const onPointerUp = (event) => {
        if (!isResizing) return;
        isResizing = false;
        document.body.style.cursor = "";
        widget.logDivider.releasePointerCapture?.(event.pointerId);
        document.removeEventListener("pointermove", onPointerMove);
        document.removeEventListener("pointerup", onPointerUp);
        schedulePlotResize();
    };

    widget.logDivider.addEventListener("pointerdown", (event) => {
        if (event.button !== 0) return;
        event.preventDefault();
        const rect = widget.logHead.getBoundingClientRect();
        isResizing = true;
        startY = event.clientY;
        startHeadHeight = rect.height;
        document.body.style.cursor = "row-resize";
        widget.logDivider.setPointerCapture?.(event.pointerId);
        document.addEventListener("pointermove", onPointerMove);
        document.addEventListener("pointerup", onPointerUp);
    });
}

function syncTrailSettings() {
    const v = SUITE.trail.count;
    const n = Math.max(1, Math.floor(v || 1));
    const next = [];
    for (let i = 0; i < n; i++) {
        const id = i + 1;
        const existing = (SUITE.trail.array ?? []).find(t => t.id === id);
        next.push(existing ?? { ...TRAIL, id });
    }
    SUITE.trail.array = next;
}

widget.trailCount.addEventListener("change", (e) => {
    SUITE.trail.count = Number(e.target.value);
    syncTrailSettings();
    renderSuiteSettings();
    renderSuite();
});

widget.trailGap.addEventListener("change", (e) => {
    SUITE.trail.gap = Number(e.target.value);
    renderSuite();
});

widget.fitUserDepthBtn.addEventListener("click", () => {
    SUITE.topDepth = Number.isFinite(Number(widget.topDepth.value)) ? Number(widget.topDepth.value) : null;
    SUITE.baseDepth = Number.isFinite(Number(widget.baseDepth.value)) ? Number(widget.baseDepth.value) : null;
    if (SUITE.topDepth >= SUITE.baseDepth) {
        alert("Invalid depth range, top depth must be less than base depth.");
        return;
    }
    renderSuite();
});

widget.gridShow.addEventListener("change", () => {
    if (!widget.gridShow) return;

    const isOn = widget.gridShow.checked;
    SUITE.grid.show = isOn;

    const minorFieldset = document.querySelector(
        ".grid-settings-minor"
    );

    // 🔽 dependency: turn off minor grid if grid is off
    if (!isOn && widget.gridMinorShow) {
        widget.gridWidth.disabled = true;
        widget.gridColor.disabled = true;
        widget.gridAlpha.disabled = true;
        widget.gridMinorShow.checked = false;
        SUITE.grid.minor.show = false;
        minorFieldset.disabled = true;
    } else {
        widget.gridWidth.disabled = false;
        widget.gridColor.disabled = false;
        widget.gridAlpha.disabled = false;
        minorFieldset.disabled = false;
    }

    renderSuite();
});

widget.gridWidth.addEventListener("input", () => {
    const width = Number(widget.gridWidth.value);
    if (Number.isFinite(width)) SUITE.grid.width = Math.max(0, width);
    renderSuite();
});

widget.gridColor.addEventListener("input", () => {
    if (widget.gridColor.value) SUITE.grid.color = widget.gridColor.value;
    renderSuite();
});

widget.gridAlpha.addEventListener("input", () => {
    const alpha = Number(widget.gridAlpha.value);
    if (Number.isFinite(alpha)) SUITE.grid.alpha = clamp(alpha, 0, 1);
    renderSuite();
});

widget.gridMinorShow.addEventListener("change", () => {
    if (widget.gridMinorShow) SUITE.grid.minor.show = !!widget.gridMinorShow.checked;
    renderSuite();
});

widget.gridMinorWidth.addEventListener("input", () => {
    const width = Number(widget.gridMinorWidth.value);
    if (Number.isFinite(width)) SUITE.grid.minor.width = Math.max(0, width);
    renderSuite();
});

widget.gridMinorColor.addEventListener("input", () => {
    if (widget.gridMinorColor.value) SUITE.grid.minor.color = widget.gridMinorColor.value;
    renderSuite();
});

widget.gridMinorAlpha.addEventListener("input", () => {
    const alpha = Number(widget.gridMinorAlpha.value);
    if (Number.isFinite(alpha)) SUITE.grid.minor.alpha = clamp(alpha, 0, 1);
    renderSuite();
});

widget.separatorShow.addEventListener("change", () => {
    if (widget.separatorShow) SUITE.separator.show = !!widget.separatorShow.checked;
    renderSuite();
});

widget.separatorWidth.addEventListener("input", () => {
    const width = Number(widget.separatorWidth.value);
    if (Number.isFinite(width)) SUITE.separator.width = Math.max(0, width);
    renderSuite();
});

widget.separatorColor.addEventListener("input", () => {
    if (widget.separatorColor.value) SUITE.separator.color = widget.separatorColor.value;
    renderSuite();
});

widget.separatorAlpha.addEventListener("input", () => {
    const alpha = Number(widget.separatorAlpha.value);
    if (Number.isFinite(alpha)) SUITE.separator.alpha = clamp(alpha, 0, 1);
    renderSuite();
});

function renderTrailSettings(trailEl, t) {
    const tpl = document.getElementById("trailSettingsTemplate");
    if (!tpl) throw new Error("trailSettingsTemplate not found");

    // Clone template
    const fragment = tpl.content.cloneNode(true);

    // Title
    const titleEl = fragment.querySelector('[data-role="trail-title"]');
    if (titleEl) {
        titleEl.textContent = `Trail ${t.id}`;
    }

    const bindLabel = (labelRole, inputRole, idSuffix) => {
        const label = fragment.querySelector(`[data-role="${labelRole}"]`);
        const input = fragment.querySelector(`[data-role="${inputRole}"]`);
        if (!label || !input) return;
        const id = `trail-${t.id}-${idSuffix}`;
        input.id = id;
        label.setAttribute("for", id);
    };

    bindLabel("xmin-label", "xmin-input", "xmin");
    bindLabel("xmax-label", "xmax-input", "xmax");

    fragment.querySelector('[data-field="xMin"]').value =
        t.xMin ?? "";

    fragment.querySelector('[data-field="xMax"]').value =
        t.xMax ?? "";

    // ---- Inject ----
    trailEl.innerHTML = "";
    trailEl.appendChild(fragment);
}

function renderSuiteSettings() {
    const prevSelectedId = Number(
        widget.trailSelect?.value
    );

    widget.trailCount.value = String(SUITE.trail.count);
    widget.trailGap.value = String(Number.isFinite(SUITE.trail.gap) ? SUITE.trail.gap : 0.05);

    widget.gridShow.checked = SUITE.grid.show;
    widget.gridWidth.value = String(SUITE.grid.width);
    widget.gridColor.value = SUITE.grid.color;
    widget.gridAlpha.value = String(SUITE.grid.alpha);

    widget.gridMinorShow.checked = SUITE.grid.minor.show;
    widget.gridMinorWidth.value = String(SUITE.grid.minor.width);
    widget.gridMinorColor.value = SUITE.grid.minor.color;
    widget.gridMinorAlpha.value = String(SUITE.grid.minor.alpha);

    widget.separatorShow.checked = SUITE.separator.show;
    widget.separatorWidth.value = String(SUITE.separator.width);
    widget.separatorColor.value = SUITE.separator.color;
    widget.separatorAlpha.value = String(SUITE.separator.alpha);

    // const curveNames = las ? Object.keys(las.curves) : [];
    const curveNames = ["GR", "RHOB", "NPHI", "DT", "CALI", "SP"]; // Placeholder
    const panel = document.querySelector('[data-role="trail-panel"]');
    const trailEls = new Map();

    const frag = document.createDocumentFragment();
    for (const t of SUITE.trail.array) {
        const option = document.createElement("option");
        option.value = String(t.id);
        option.textContent = `Trail ${t.id}`;
        frag.appendChild(option);

        const trailEl = document.createElement("div");
        trailEl.className = "trail";
        trailEl.dataset.trailId = String(t.id);

        renderTrailSettings(trailEl, t);

        const list = trailEl.querySelector(".curve-list");
        for (const name of curveNames) {
            const item = document.createElement("label");
            item.className = "curve-item";

            const checked = t.curves.has(name);
            item.innerHTML = `
    <input type="checkbox" ${checked ? "checked" : ""} data-curve="${escapeHtml(name)}" />
    <span>${escapeHtml(name)}</span>
    <small>${checked ? "selected" : ""}</small>
`;
            list.appendChild(item);
        }
        // }

        // Event wiring
        trailEl.addEventListener("input", (e) => {
            const field = e.target?.dataset?.field;
            if (!field) return;
            if (field === "xMin") {
                t.xMin = e.target.value;
            } else if (field === "xMax") {
                t.xMax = e.target.value;
            }
        });

        trailEl.addEventListener("change", (e) => {
            const cb = e.target;
            if (!(cb instanceof HTMLInputElement)) return;
            const curve = cb.dataset.curve;
            if (!curve) return;

            if (cb.checked) {
                t.curves.add(curve);
            } else {
                t.curves.delete(curve);
            }
            // Update small label
            const small = cb.closest(".curve-item")?.querySelector("small");
            if (small) small.textContent = cb.checked ? "selected" : "";
        });

        trailEl.querySelector('[data-action="clearTrail"]')?.addEventListener("click", () => {
            t.curves.clear();
            renderSuiteSettings();
        });

        trailEls.set(String(t.id), trailEl);
    }

    widget.trailSelect.replaceChildren(frag);

    const fallbackId = Number.isFinite(prevSelectedId) ? prevSelectedId : SUITE.trail.array[0].id;
    const maxId = SUITE.trail.array[SUITE.trail.array.length - 1].id;
    const selectedId = Math.min(Math.max(1, fallbackId), maxId);

    const showTrail = (id) => {
        const el = trailEls.get(String(id));
        if (!el) {
            panel.innerHTML = `<div class="status">Trail not found.</div>`;
            return;
        }
        panel.replaceChildren(el);
    };

    widget.trailSelect.value = String(selectedId);
    showTrail(selectedId);

    widget.trailSelect.addEventListener("change", () => {
        showTrail(Number(widget.trailSelect.value));
    });
}

function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    }[c]));
}

function clamp(n, min, max) {
    return Math.min(max, Math.max(min, n));
}

function hexToRgb(hex) {
    const raw = String(hex || "").trim().replace(/^#/, "");
    if (raw.length === 3) {
        const r = parseInt(raw[0] + raw[0], 16);
        const g = parseInt(raw[1] + raw[1], 16);
        const b = parseInt(raw[2] + raw[2], 16);
        return Number.isFinite(r) && Number.isFinite(g) && Number.isFinite(b) ? { r, g, b } : null;
    }
    if (raw.length === 6) {
        const r = parseInt(raw.slice(0, 2), 16);
        const g = parseInt(raw.slice(2, 4), 16);
        const b = parseInt(raw.slice(4, 6), 16);
        return Number.isFinite(r) && Number.isFinite(g) && Number.isFinite(b) ? { r, g, b } : null;
    }
    return null;
}

function buildBodyFigure() {

    const layout = {
        margin: { l: 68, r: 24, t: 0, b: 44 },
        showlegend: false,
        legend: {
            orientation: "h",
            x: 0, y: 1.08,
            font: { size: 11, color: "#e8eefc" },
            bgcolor: "rgba(7,10,20,0.35)",
            bordercolor: "rgba(32,48,95,0.7)",
            borderwidth: 1
        },
        hovermode: "closest",
        yaxis: {
            title: { text: "DEPTH", font: { size: 12 } },
            autorange: "reversed",
            range: SUITE.range,
            showgrid: SUITE.grid.show,
            gridwidth: SUITE.grid.width,
            gridcolor: SUITE.grid.gridcolor,
            minor: {
                showgrid: SUITE.grid.minor.show,
                gridwidth: SUITE.grid.minor.width,
                gridcolor: SUITE.grid.minor.gridcolor,
            },
            zeroline: false,
            ticks: "outside",
            tickfont: { size: 11 },
        },
        // subtle vertical separators using shapes
        shapes: [],
    };

    const data = [];

    for (let i = 0; i < SUITE.trail.count; i++) {
        const t = SUITE.trail.array[i];
        const xref = (i === 0) ? "x" : `x${i + 1}`;
        const axisKey = (i === 0) ? "xaxis" : `xaxis${i + 1}`;

        const d0 = i * (SUITE.trail.width + SUITE.trail.gap);
        const d1 = d0 + SUITE.trail.width;

        // Add vertical separator lines between trails (paper coords)
        if (i > 0 && SUITE.separator.show) {
            layout.shapes.push({
                type: "line",
                xref: "paper", yref: "paper",
                x0: d0 - SUITE.trail.gap / 2, x1: d0 - SUITE.trail.gap / 2,
                y0: 0, y1: 1,
                line: {
                    width: SUITE.separator.width,
                    color: SUITE.separator.sepcolor,
                },
            });
        }

        // X limits per trail (optional)
        const xmin = Number(t.xMin);
        const xmax = Number(t.xMax);
        const hasX = Number.isFinite(xmin) && Number.isFinite(xmax);

        layout[axisKey] = {
            domain: [d0, d1],
            // title: { text: `Trail ${t.id}`, font: { size: 12 } },
            anchor: "y",
            showgrid: t.grid.show,
            gridwidth: t.grid.width,
            gridcolor: t.grid.gridcolor,
            minor: {
                showgrid: t.grid.minor.show,
                gridwidth: t.grid.minor.width,
                gridcolor: t.grid.minor.gridcolor,
            },
            zeroline: false,
            ticks: "outside",
            tickfont: { size: 11 },
            // If user sets x-range
            range: hasX ? [xmin, xmax] : undefined,
        };

        if (!t?.curves?.size) {
            data.push({
                type: "scatter",
                mode: "lines",
                x: [null],
                y: [null],
                xaxis: xref,
                yaxis: "y",
                showlegend: false,
                hoverinfo: "skip",
                line: { width: 0 },
                opacity: 0,
            });
        }
    }

    const config = {
        responsive: true,
        displaylogo: false,
        scrollZoom: true,
        modeBarButtonsToRemove: ["lasso2d", "select2d"],
    };

    return { data, layout, config };
}

function buildHeadFigure(body) {
    const data = [];
    const layout = structuredClone(body.layout);

    layout.margin.b = 0;
    layout.yaxis = {
        zeroline: false,
        showgrid: true,
        ticks: "",
        showticklabels: false,
    }

    for (let i = 0; i < SUITE.trail.count; i++) {
        const xref = (i === 0) ? "x" : `x${i + 1}`;
        const axisKey = (i === 0) ? "xaxis" : `xaxis${i + 1}`;

        data.push({
            type: "scatter",
            mode: "lines",
            x: [null],
            y: [null],
            xaxis: xref,
            yaxis: "y",
            showlegend: false,
            hoverinfo: "skip",
            line: { width: 0 },
            opacity: 0,
        });

        layout[axisKey].showgrid = false;
        layout[axisKey].minor.showgrid = false;
    }

    const config = {
        responsive: true,
        displaylogo: false,
        displayModeBar: false,
        staticPlot: true,
    };

    return { data, layout, config };
}

function renderSuite() {
    const body = buildBodyFigure();
    Plotly.react(widget.logBody, body.data, body.layout, body.config);
    const head = buildHeadFigure(body);
    Plotly.react(widget.logHead, head.data, head.layout, head.config);
}

(function () {
    syncTrailSettings();
    renderSuiteSettings();
    renderSuite();
    initLogDividerResize();
})();

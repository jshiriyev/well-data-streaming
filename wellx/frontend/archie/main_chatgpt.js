let las = null;           // {depth, curves, depthMin, depthMax...}
let fileName = "No file";

function parseLAS(text, forcedNullValue = null) {
    const lines = text.split(/\r?\n/);

    // Find sections
    const idxCurve = lines.findIndex(l => /^\s*~\s*C/i.test(l));
    const idxAscii = lines.findIndex(l => /^\s*~\s*A/i.test(l));
    if (idxAscii === -1) {
        throw new Error("LAS parser: '~A' (ASCII data) section not found.");
    }

    // Attempt to infer NULL value from ~W section
    let nullVal = null;
    for (const l of lines) {
        // Common patterns: NULL.  -999.25 : ...
        const m = l.match(/^\s*NULL\s*\.\s*([+-]?\d+(\.\d+)?)/i);
        if (m) { nullVal = Number(m[1]); break; }
    }
    if (forcedNullValue != null && forcedNullValue !== "") {
        const n = Number(forcedNullValue);
        if (!Number.isNaN(n)) nullVal = n;
    }

    // Parse curve mnemonics from ~C section (best-effort)
    // Typical curve line: GR.API : Gamma Ray
    // We'll collect tokens before '.' or whitespace.
    const curveNames = [];
    if (idxCurve !== -1 && idxCurve < idxAscii) {
        for (let i = idxCurve + 1; i < idxAscii; i++) {
            const raw = lines[i];
            if (!raw || /^\s*~/.test(raw)) break;
            if (/^\s*#/.test(raw)) continue;
            // Try mnemonic before '.' first
            let m = raw.match(/^\s*([A-Za-z0-9_\/-]+)\s*\./);
            if (!m) m = raw.match(/^\s*([A-Za-z0-9_\/-]+)/);
            if (m) curveNames.push(m[1].trim());
        }
    }

    // Parse ASCII data
    const dataRows = [];
    for (let i = idxAscii + 1; i < lines.length; i++) {
        const raw = lines[i];
        if (!raw) continue;
        if (/^\s*~/.test(raw)) break;
        if (/^\s*#/.test(raw)) continue;

        const parts = raw.trim().split(/\s+/);
        // Guard against junk lines
        if (parts.length < 2) continue;

        const nums = parts.map(p => {
            const v = Number(p);
            return Number.isFinite(v) ? v : null;
        });
        if (nums.some(v => v !== null)) dataRows.push(nums);
    }

    if (!dataRows.length) {
        throw new Error("LAS parser: no numeric rows found under '~A'.");
    }

    // Determine number of columns from the first good row
    const nCols = dataRows[0].length;

    // If curveNames count matches columns, use them; else synthesize
    // LAS usually includes depth + curves in ~C. If mismatch, generate.
    let names = curveNames.slice(0, nCols);
    if (names.length !== nCols) {
        names = Array.from({ length: nCols }, (_, i) => i === 0 ? "DEPT" : `CURVE_${i}`);
    }
    // Ensure first is depth
    names[0] = names[0] || "DEPT";

    // Build columns
    const cols = Object.fromEntries(names.map(n => [n, []]));
    for (const row of dataRows) {
        // Pad short rows
        for (let c = 0; c < nCols; c++) {
            const v = (c < row.length) ? row[c] : null;
            cols[names[c]].push(v);
        }
    }

    // Normalize null values -> null
    if (nullVal != null && Number.isFinite(nullVal)) {
        for (const k of Object.keys(cols)) {
            cols[k] = cols[k].map(v => (v === nullVal ? null : v));
        }
    }

    // Pick depth key (first column)
    const depthKey = names[0];
    const depth = cols[depthKey];

    // Curves dict (exclude depth column)
    const curves = {};
    for (const k of names.slice(1)) curves[k] = cols[k];

    // Basic depth min/max
    const finiteDepth = depth.filter(v => Number.isFinite(v));
    const dmin = Math.min(...finiteDepth);
    const dmax = Math.max(...finiteDepth);

    return { depthKey, depth, curves, nullValue: nullVal, depthMin: dmin, depthMax: dmax };
}

const control = {
    lasFile: document.getElementById("lasFile"),
    nullValue: document.getElementById("nullValue"),
    loadStatus: document.getElementById("loadStatus"),

    topDepth: document.getElementById("topDepth"),
    baseDepth: document.getElementById("baseDepth"),
    fitDepthBtn: document.getElementById("fitDepthBtn"),

    trailCount: document.getElementById("trailCount"),
    trailGap: document.getElementById("trailGap"),
    trailSelect: document.getElementById("trailSelect"),
    trails: [], // [{id, xMin, xMax, curveCount, curves:Set}]

    wnameTag: document.getElementById("wnameTag"),
    depthTag: document.getElementById("depthTag"),
    trailTag: document.getElementById("trailTag"),
    cycleTag: document.getElementById("cycleTag"),

    plot: document.getElementById("plot"),
};

function setStatus(text, ok = null) {
    control.loadStatus.textContent = text;
    control.loadStatus.classList.remove("ok", "bad");
    if (ok === true) control.loadStatus.classList.add("ok");
    if (ok === false) control.loadStatus.classList.add("bad");
}

function updateTopTags() {
    const fmt = (v) => {
        const n = (typeof v === "number") ? v : Number(v);
        if (!Number.isFinite(n)) return String(v ?? "-");
        return (Math.abs(n) >= 1000) ? n.toFixed(1) : n.toFixed(3);
    };

    // Guard: required DOM
    if (!control?.wnameTag || !control?.trailTag || !control?.cycleTag || !control?.depthTag) return;

    const trails = Array.isArray(control.trails) ? control.trails : [];

    control.wnameTag.textContent = (typeof fileName === "string" && fileName.trim()) ? fileName : "No file";
    control.trailTag.textContent = `Trails: ${trails.length}`;

    const allSelected = trails.reduce((acc, t) => {
        const size = t?.curves?.size;
        return acc + (Number.isFinite(size) ? size : 0);
    }, 0);

    control.cycleTag.textContent = `Curves: ${allSelected}`;

    const dMin = las?.depthMin;
    const dMax = las?.depthMax;

    control.depthTag.textContent =
        (dMin != null || dMax != null)
            ? `Depth: ${fmt(dMin)} – ${fmt(dMax)}`
            : "Depth: -";
}

function setTrailCount(n) {
    n = Math.max(1, Math.floor(n || 1));
    const next = [];
    for (let i = 0; i < n; i++) {
        const id = i + 1;
        const existing = control.trails.find(t => t.id === id);
        next.push(existing ?? { id, xMin: 0, xMax: 20, curveCount: 3, curves: new Set() });
    }
    control.trails = next;
}

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

    bindLabel("maxcurves-label", "maxcurves-input", "maxcurves");
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

function rebuildTrailsUI() {
    const prevSelectedId = Number(
        document.querySelector('[data-role="trail-select"]')?.value
    );

    if (!control.trails.length) return;

    const curveNames = las ? Object.keys(las.curves) : [];
    const select = document.querySelector('[data-role="trail-select"]');
    const panel = document.querySelector('[data-role="trail-panel"]');
    const trailEls = new Map();

    const frag = document.createDocumentFragment();
    for (const t of control.trails) {
        const option = document.createElement("option");
        option.value = String(t.id);
        option.textContent = `Trail ${t.id}`;
        frag.appendChild(option);

        const trailEl = document.createElement("div");
        trailEl.className = "trail";
        trailEl.dataset.trailId = String(t.id);

        renderTrailSettings(trailEl, t);

        const list = trailEl.querySelector(".curve-list");
        if (!las) {
            list.innerHTML = `<div class="status">No curves loaded.</div>`;
        } else {
            // Build curve checkboxes
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
        }

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

            // Toggle with curveCount limit
            if (cb.checked) {
                t.curves.add(curve);
            } else {
                t.curves.delete(curve);
            }
            // Update small label
            const small = cb.closest(".curve-item")?.querySelector("small");
            if (small) small.textContent = cb.checked ? "selected" : "";
            updateTopTags();
        });

        trailEl.querySelector('[data-action="clearTrail"]')?.addEventListener("click", () => {
            t.curves.clear();
            rebuildTrailsUI();
            updateTopTags();
        });

        trailEls.set(String(t.id), trailEl);
    }

    control.trailSelect.replaceChildren(frag);

    const fallbackId = Number.isFinite(prevSelectedId) ? prevSelectedId : control.trails[0].id;
    const maxId = control.trails[control.trails.length - 1].id;
    const selectedId = Math.min(Math.max(1, fallbackId), maxId);

    const showTrail = (id) => {
        const el = trailEls.get(String(id));
        if (!el) {
            panel.innerHTML = `<div class="status">Trail not found.</div>`;
            return;
        }
        panel.replaceChildren(el);
    };

    select.value = String(selectedId);
    showTrail(selectedId);

    select.addEventListener("change", () => {
        showTrail(Number(select.value));
    });
}

function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
}

function buildLogFigure() {

    // const depth = las.depth;
    const nTrails = Number(control.trailCount.value)

    const top = Number(control.topDepth.value);
    const base = Number(control.baseDepth.value);
    const yRange = [base, top];

    // Build domains evenly with small gaps
    const gap = 0.012;
    const totalGap = gap * (nTrails - 1);
    const w = (1 - totalGap) / nTrails;

    const layout = {
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        margin: { l: 68, r: 24, t: 24, b: 44 },
        showlegend: true,
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
            // title: { text: las.depthKey || "DEPT", font: { size: 12 } },
            autorange: "reversed",
            range: yRange,
            showgrid: true,
            gridcolor: "rgba(32,48,95,0.55)",
            zeroline: false,
            ticks: "outside",
            tickfont: { size: 11 },
        },
        // subtle vertical separators using shapes
        shapes: [],
    };

    const data = [];
    let xAxisCount = 0;

    for (let i = 0; i < nTrails; i++) {
        const xref = (i === 0) ? "x" : `x${i + 1}`;
        const axisKey = (i === 0) ? "xaxis" : `xaxis${i + 1}`;

        const d0 = i * (w + gap);
        const d1 = d0 + w;

        // Add vertical separator lines between trails (paper coords)
        if (i > 0) {
            layout.shapes.push({
                type: "line",
                xref: "paper", yref: "paper",
                x0: d0 - gap / 2, x1: d0 - gap / 2,
                y0: 0, y1: 1,
                line: { width: 1, color: "rgba(32,48,95,0.9)" },
            });
        }

        // X limits per trail (optional)
        const xmin = 0; //Number(t.xMin);
        const xmax = 20; //Number(t.xMax);
        const hasX = Number.isFinite(xmin) && Number.isFinite(xmax);

        layout[axisKey] = {
            domain: [d0, d1],
            // title: { text: `Trail ${t.id}`, font: { size: 12 } },
            showgrid: true,
            gridcolor: "rgba(32,48,95,0.55)",
            zeroline: false,
            ticks: "outside",
            tickfont: { size: 11 },
            // If user sets x-range
            range: hasX ? [xmin, xmax] : undefined,
        };

        // Add traces for selected curves
        // for (const curveName of t.curves) {
        //     const y = depth;
        //     const x = Array(0,20); //las.curves[curveName];
        //     if (!x) continue;

        //     data.push({
        //         type: "scattergl",
        //         mode: "lines",
        //         name: `T${t.id}: ${curveName}`,
        //         x,
        //         y,
        //         xaxis: xref,
        //         yaxis: "y",
        //         connectgaps: false,
        //         hovertemplate: `${curveName}<br>Depth: %{y:.3f}<br>Value: %{x:.6g}<extra></extra>`,
        //     });
        // }

        xAxisCount++;
    }

    // Add top headers per trail (optional nicer feel)
    // Using annotations at trail centers
    layout.annotations = [];
    for (let i = 0; i < nTrails; i++) {
        const d0 = i * (w + gap);
        const d1 = d0 + w;
        const t = control.trails[i];
        const selected = [...t.curves].slice(0, 3).join(", ");
        layout.annotations.push({
            xref: "paper", yref: "paper",
            x: (d0 + d1) / 2,
            y: 1.02,
            text: selected ? `Trail ${t.id}: ${escapeHtml(selected)}${t.curves.size > 3 ? "…" : ""}` : `Trail ${t.id}: (empty)`,
            showarrow: false,
            font: { size: 11, color: "#a7b3d6" },
            bgcolor: "rgba(7,10,20,0.25)",
            bordercolor: "rgba(32,48,95,0.7)",
            borderwidth: 1,
            borderpad: 4,
        });
    }

    // If no curves selected anywhere, show a hint
    const selectedCount = control.trails.reduce((acc, t) => acc + t.curves.size, 0);
    if (!selectedCount) {
        layout.annotations.push({
            xref: "paper", yref: "paper",
            x: 0.5, y: 0.5,
            text: "Select curves in Trail Settings, then click Render",
            showarrow: false,
            font: { size: 16, color: "#a7b3d6" },
        });
    }

    const config = {
        responsive: true,
        displaylogo: false,
        scrollZoom: true,
        modeBarButtonsToRemove: ["lasso2d", "select2d"],
    };

    return { data, layout, config };
}

function render() {
    const fig = buildLogFigure();
    Plotly.react(control.plot, fig.data, fig.layout, fig.config);
    updateTopTags();
}

control.trailCount.addEventListener("change", () => {
    setTrailCount(Number(control.trailCount.value || 1));
    rebuildTrailsUI();
    updateTopTags();
    render();
});

control.fitDepthBtn.addEventListener("click", () => {
    if (!las) return;
    control.topDepth.value = String(las.depthMin);
    control.baseDepth.value = String(las.depthMax);
    render();
});

control.lasFile.addEventListener("change", async () => {
    const f = control.lasFile.files?.[0];
    if (!f) return;

    fileName = f.name;
    try {
        const text = await f.text();
        las = parseLAS(text, control.nullValue.value);

        // Auto-select a few curves per trail (best effort) so user sees something immediately
        // Strategy: pick first N curves and spread across trails.
        const curveNames = Object.keys(las.curves);
        for (const t of control.trails) t.curves.clear();
        let idx = 0;
        for (const t of control.trails) {
            const take = Math.max(1, Math.min(2, curveNames.length - idx));
            t.curveCount = Math.max(t.curveCount, take);
            for (let k = 0; k < take && idx < curveNames.length; k++, idx++) {
                t.curves.add(curveNames[idx]);
            }
            if (idx >= curveNames.length) break;
        }

        // Fit depth window by default
        control.topDepth.value = String(las.depthMin);
        control.baseDepth.value = String(las.depthMax);

        setStatus(`Loaded: ${f.name} | Curves: ${Object.keys(las.curves).length} | NULL: ${las.nullValue ?? "n/a"}`, true);

        rebuildTrailsUI();
        render();
    } catch (err) {
        las = null;
        setStatus(String(err?.message || err), false);
        rebuildTrailsUI();
        render();
    }
});

setTrailCount(Number(control.trailCount.value));

rebuildTrailsUI();

render();

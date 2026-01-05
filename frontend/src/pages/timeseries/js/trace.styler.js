const LINE_DASH_OPTIONS = [
    "solid",
    "dash",
    "dot",
    "dashdot",
    "longdash",
    "longdashdot"
];

const MARKER_SYMBOL_OPTIONS = [
    "circle",
    "square",
    "diamond",
    "cross",
    "triangle-up",
    "triangle-down"
];

const DEFAULT_TRACE_STYLE = {
    lineDash: "solid",
    lineColor: "#1f77b4",
    lineWidth: 2,
    opacity: 1.0,
    markerEnabled: false,
    markerSize: 6,
    markerSymbol: "circle",
};

const traceStylerRegistry = new Set();
let globalTraceStylerListenersAttached = false;

function registerTraceStyler(instance) {
    traceStylerRegistry.add(instance);
    if (globalTraceStylerListenersAttached) return;

    document.addEventListener("pointerdown", (event) => {
        if (event.target.closest(".settings-circle")) return;
        traceStylerRegistry.forEach((styler) => {
            if (!styler.isOpen()) return;
            if (styler.contains(event.target)) return;
            styler.hide();
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") return;
        traceStylerRegistry.forEach((styler) => {
            if (styler.isOpen()) {
                styler.hide();
            }
        });
    });

    globalTraceStylerListenersAttached = true;
}

function createRangeControl({ id, label, min, max, step, value, onInput }) {
    const tpl = document.getElementById("range-control");
    if (!tpl) return null;

    const node = tpl.content.cloneNode(true);

    const labelEl = node.querySelector("label");
    const inputEl = node.querySelector("input");
    const valueEl = node.querySelector(".range-value");
    if (!labelEl || !inputEl || !valueEl) return null;

    labelEl.textContent = label;
    labelEl.htmlFor = id;

    inputEl.id = id;
    inputEl.min = min;
    inputEl.max = max;
    inputEl.step = step;
    inputEl.value = value;

    valueEl.textContent = String(value);
    valueEl.id = `${id}-value`;

    inputEl.addEventListener("input", (e) => {
        const v = e.target.value;
        valueEl.textContent = v;
        onInput?.(Number(v));
    });

    return node.firstElementChild;
}

function fillSelect(selectEl, options, { placeholder } = {}) {
    selectEl.innerHTML = "";
    if (placeholder) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = placeholder;
        opt.disabled = true;
        opt.selected = true;
        selectEl.appendChild(opt);
    }
    options.forEach(({ value, label }) => {
        const opt = document.createElement("option");
        opt.value = value;
        opt.textContent = label ?? value;
        selectEl.appendChild(opt);
    });
}

function createTraceSelectSetter(selectEl, config = {}) {
    return function setTraces(traces) {
        fillSelect(
            selectEl,
            traces.map((t, i) => ({
                value: String(i),
                label: t.name ?? `Trace ${i + 1}`,
            })),
            {
                placeholder: traces.length ? "Select..." : "No traces",
                ...config,
            }
        );
    };
}

function pickFirstTraceValue(selectEl) {
    const option = Array.from(selectEl.options).find((opt) => opt.value !== "");
    selectEl.value = option ? option.value : "";
    return selectEl.value;
}

function extractTraceStyle(trace, defaults) {
    const line = trace?.line || {};
    const marker = trace?.marker || {};
    const hasMarkers = (trace?.mode || "").includes("markers") || (marker.size ?? 0) > 0;

    return {
        line: {
            dash: line.dash ?? defaults.lineDash,
            color: line.color ?? defaults.lineColor,
            width: line.width ?? defaults.lineWidth,
        },
        opacity: trace?.opacity ?? defaults.opacity,
        marker: {
            enabled: hasMarkers,
            size: marker.size ?? defaults.markerSize,
            symbol: marker.symbol ?? defaults.markerSymbol,
        },
    };
}

export function createTraceStyler(
    box,
    {
        onChangeTrace,
        onApply,
        onReset,
        lineDashOptions = LINE_DASH_OPTIONS,
        markerSymbolOptions = MARKER_SYMBOL_OPTIONS,
        defaultTraceStyle = DEFAULT_TRACE_STYLE,
        getPlotDiv,
        getFigure,
    } = {}
) {
    if (!box) return null;
    if (box.traceStyler) return box.traceStyler;

    const match = box.id?.match(/\d+$/);
    const instanceId = match ? match[0] : Math.random().toString(36).slice(2, 8);

    const styler = box.querySelector(".trace-styler");
    if (!styler) return null;
    styler.id = `trace-styler-${instanceId}`;

    const template = document.getElementById("trace-styler");
    if (!template) return null;

    const root = template.content.cloneNode(true);

    const header = root.querySelector(".board-title");

    if (header) {
        header.textContent = `Box #${instanceId}: Style Settings`;
    }

    const traceSelect = root.querySelector(".trace-select");
    const traceLabel = root.querySelector(".trace-label");
    const lineDashSelect = root.querySelector(".line-dash-select");
    const lineDashLabel = root.querySelector(".line-dash-label");
    const lineColorInput = root.querySelector(".line-color-input");
    const lineColorLabel = root.querySelector(".line-color-label");
    const toggleInput = root.querySelector(".marker-toggle-input");
    const toggleLabel = root.querySelector(".marker-toggle-label");
    const markerSettings = root.querySelector(".marker-settings");
    const markerSymbolSelect = root.querySelector(".marker-symbol-select");
    const markerSymbolLabel = root.querySelector(".marker-symbol-label");
    const applyBtn = root.querySelector(".apply-style");
    const resetBtn = root.querySelector(".reset-style");

    if (!traceSelect || !traceLabel || !lineDashSelect || !lineDashLabel) return null;
    if (!lineColorInput || !lineColorLabel || !toggleInput || !toggleLabel) return null;
    if (!markerSettings || !markerSymbolSelect || !markerSymbolLabel) return null;
    if (!applyBtn || !resetBtn) return null;

    traceSelect.id = `trace-styler-${instanceId}-trace-select`;
    traceLabel.setAttribute("for", traceSelect.id);

    lineDashSelect.id = `trace-styler-${instanceId}-line-dash`;
    lineDashLabel.setAttribute("for", lineDashSelect.id);

    lineColorInput.id = `trace-styler-${instanceId}-line-color`;
    lineColorLabel.setAttribute("for", lineColorInput.id);

    toggleInput.id = `trace-styler-${instanceId}-marker-toggle`;
    toggleLabel.setAttribute("for", toggleInput.id);

    markerSymbolSelect.id = `trace-styler-${instanceId}-marker-symbol`;
    markerSymbolLabel.setAttribute("for", markerSymbolSelect.id);

    const setTracesSelect = createTraceSelectSetter(traceSelect);

    fillSelect(
        lineDashSelect,
        lineDashOptions.map((v) => ({ value: v, label: v }))
    );
    fillSelect(
        markerSymbolSelect,
        markerSymbolOptions.map((v) => ({ value: v, label: v }))
    );

    lineDashSelect.value = defaultTraceStyle.lineDash;
    markerSymbolSelect.value = defaultTraceStyle.markerSymbol;
    lineColorInput.value = defaultTraceStyle.lineColor;
    toggleInput.checked = !!defaultTraceStyle.markerEnabled;
    markerSettings.style.display = toggleInput.checked ? "" : "none";

    const lineWidthMount = root.querySelector(".line-width-mount");
    const lineOpacityMount = root.querySelector(".line-opacity-mount");
    const markerSizeMount = root.querySelector(".marker-size-mount");

    const lineWidthId = `trace-styler-${instanceId}-line-width`;
    const lineOpacityId = `trace-styler-${instanceId}-line-opacity`;
    const markerSizeId = `trace-styler-${instanceId}-marker-size`;

    const lineWidthControl = createRangeControl({
        id: lineWidthId,
        label: "Line Width (px)",
        min: 0,
        max: 10,
        step: 0.5,
        value: defaultTraceStyle.lineWidth,
    });
    if (lineWidthControl) {
        lineWidthMount?.appendChild(lineWidthControl);
    }

    const lineOpacityControl = createRangeControl({
        id: lineOpacityId,
        label: "Opacity",
        min: 0,
        max: 1,
        step: 0.1,
        value: defaultTraceStyle.opacity,
    });
    if (lineOpacityControl) {
        lineOpacityMount?.appendChild(lineOpacityControl);
    }

    const markerSizeControl = createRangeControl({
        id: markerSizeId,
        label: "Marker Size",
        min: 0,
        max: 20,
        step: 1,
        value: defaultTraceStyle.markerSize,
    });
    if (markerSizeControl) {
        markerSizeMount?.appendChild(markerSizeControl);
    }

    const lineWidthInput = root.querySelector(`#${lineWidthId}`);
    const opacityInput = root.querySelector(`#${lineOpacityId}`);
    const markerSizeInput = root.querySelector(`#${markerSizeId}`);

    const resolvePlotDiv = () =>
        getPlotDiv?.() || box.querySelector(".plot-display");
    const resolveFigure = () => getFigure?.() || box.fig;

    const setRangeValue = (inputEl, value) => {
        if (!inputEl) return;
        inputEl.value = value;
        const label = inputEl.parentElement?.querySelector(".range-value");
        if (label) label.textContent = String(value);
    };

    const getTraceSource = (traceIndex) => {
        const plotDiv = resolvePlotDiv();
        const plotTrace = plotDiv?.data?.[traceIndex];
        if (plotTrace) return plotTrace;
        return resolveFigure()?.traces?.[traceIndex];
    };

    const updateButtonState = () => {
        const fig = resolveFigure();
        const hasSelection = traceSelect.value !== "";
        const ready = !!fig && Array.isArray(fig.traces) && fig.traces.length > 0;
        applyBtn.disabled = !(hasSelection && ready);
        resetBtn.disabled = !(hasSelection && ready);
    };

    const syncControlsFromTrace = () => {
        const traceIndex = traceSelect.value === "" ? null : Number(traceSelect.value);
        if (traceIndex === null || !Number.isFinite(traceIndex)) return;
        const trace = getTraceSource(traceIndex);
        if (!trace) return;

        const style = extractTraceStyle(trace, defaultTraceStyle);
        lineDashSelect.value = style.line.dash;
        lineColorInput.value = style.line.color;
        setRangeValue(lineWidthInput, style.line.width);
        setRangeValue(opacityInput, style.opacity);

        toggleInput.checked = style.marker.enabled;
        markerSettings.style.display = toggleInput.checked ? "" : "none";
        setRangeValue(markerSizeInput, style.marker.size);
        markerSymbolSelect.value = style.marker.symbol;
    };

    const persistStyleToFigure = (traceIndex, style) => {
        const fig = resolveFigure();
        const trace = fig?.traces?.[traceIndex];
        if (!trace) return;

        trace.line = {
            ...(trace.line || {}),
            dash: style.line.dash,
            color: style.line.color,
            width: style.line.width,
        };
        trace.opacity = style.opacity;
        if (style.marker.enabled) {
            trace.mode = "lines+markers";
            trace.marker = {
                ...(trace.marker || {}),
                size: style.marker.size,
                symbol: style.marker.symbol,
            };
        } else {
            trace.mode = "lines";
            if (trace.marker) {
                trace.marker.size = 0;
            }
        }
    };

    const applyStyleToTrace = (traceIndex, style) => {
        const plotDiv = resolvePlotDiv();
        if (!plotDiv) return;

        const restyle = {
            "line.color": style.line.color,
            "line.dash": style.line.dash,
            "line.width": style.line.width,
            opacity: style.opacity,
            mode: style.marker.enabled ? "lines+markers" : "lines",
            "marker.size": style.marker.enabled ? style.marker.size : 0,
            "marker.symbol": style.marker.enabled ? style.marker.symbol : undefined,
        };

        Plotly.restyle(plotDiv, restyle, [traceIndex]);
        persistStyleToFigure(traceIndex, style);
    };

    const syncTraceSelect = (traces) => {
        const figTraces = traces || resolveFigure()?.traces || [];
        const current = traceSelect.value;
        setTracesSelect(figTraces);
        traceSelect.disabled = figTraces.length === 0;
        if (current && Array.from(traceSelect.options).some((o) => o.value === current)) {
            traceSelect.value = current;
        } else {
            pickFirstTraceValue(traceSelect);
        }
        updateButtonState();
    };

    traceSelect.addEventListener("change", () => {
        const idx = traceSelect.value === "" ? null : Number(traceSelect.value);
        onChangeTrace?.(Number.isFinite(idx) ? idx : null);
        syncControlsFromTrace();
        updateButtonState();
    });

    toggleInput.addEventListener("change", () => {
        markerSettings.style.display = toggleInput.checked ? "" : "none";
    });

    applyBtn.addEventListener("click", () => {
        const traceIndex = traceSelect.value === "" ? null : Number(traceSelect.value);
        const fig = resolveFigure();
        const plotDiv = resolvePlotDiv();
        if (traceIndex === null || !Number.isFinite(traceIndex) || !fig || !plotDiv) return;

        const style = {
            line: {
                dash: lineDashSelect.value,
                color: lineColorInput.value,
                width: Number(lineWidthInput?.value ?? defaultTraceStyle.lineWidth),
            },
            opacity: Number(opacityInput?.value ?? defaultTraceStyle.opacity),
            marker: toggleInput.checked
                ? {
                    enabled: true,
                    size: Number(markerSizeInput?.value ?? defaultTraceStyle.markerSize),
                    symbol: markerSymbolSelect.value,
                }
                : { enabled: false },
        };

        onApply?.(style, traceIndex);
        applyStyleToTrace(traceIndex, style);
    });

    resetBtn.addEventListener("click", () => {
        const traceIndex = traceSelect.value === "" ? null : Number(traceSelect.value);
        const fig = resolveFigure();
        const plotDiv = resolvePlotDiv();
        if (traceIndex === null || !Number.isFinite(traceIndex) || !fig || !plotDiv) return;

        onReset?.(traceIndex);

        lineColorInput.value = defaultTraceStyle.lineColor;
        lineDashSelect.value = defaultTraceStyle.lineDash;
        setRangeValue(lineWidthInput, defaultTraceStyle.lineWidth);
        setRangeValue(opacityInput, defaultTraceStyle.opacity);
        toggleInput.checked = !!defaultTraceStyle.markerEnabled;
        markerSettings.style.display = toggleInput.checked ? "" : "none";
        setRangeValue(markerSizeInput, defaultTraceStyle.markerSize);
        markerSymbolSelect.value = defaultTraceStyle.markerSymbol;

        applyStyleToTrace(traceIndex, {
            line: {
                dash: defaultTraceStyle.lineDash,
                color: defaultTraceStyle.lineColor,
                width: defaultTraceStyle.lineWidth,
            },
            opacity: defaultTraceStyle.opacity,
            marker: {
                enabled: !!defaultTraceStyle.markerEnabled,
                size: defaultTraceStyle.markerSize,
                symbol: defaultTraceStyle.markerSymbol,
            },
        });
    });

    const traceStylerButton = box.querySelector(".settings-circle");

    const openPanel = () => {
        syncTraceSelect();
        if (traceSelect.value === "") {
            pickFirstTraceValue(traceSelect);
        }
        syncControlsFromTrace();
        updateButtonState();
        styler.style.display = "flex";
        styler.style.position = "absolute";
        if (box._traceStylerPos) {
            const { x, y } = box._traceStylerPos;
            applyPosition(x, y);
        }
        (traceSelect.value ? lineDashSelect : traceSelect).focus();
    };

    const handleOpenClick = (event) => {
        event.stopPropagation();
        openPanel();
    };

    traceStylerButton?.addEventListener("click", handleOpenClick);

    let isDragging = false;
    let offsetX = 0;
    let offsetY = 0;
    let lastPos = null;

    const getViewportRect = () => ({
        width: document.documentElement.clientWidth,
        height: document.documentElement.clientHeight,
    });

    const getFixedContainingBlock = (el) => {
        let node = el?.parentElement;
        while (node && node !== document.body && node !== document.documentElement) {
            const style = window.getComputedStyle(node);
            const willChange = style.willChange || "";
            if (
                style.transform !== "none" ||
                style.filter !== "none" ||
                style.perspective !== "none" ||
                willChange.includes("transform") ||
                willChange.includes("filter") ||
                willChange.includes("perspective")
            ) {
                return node;
            }
            node = node.parentElement;
        }
        return document.documentElement;
    };

    const applyPosition = (x, y) => {
        const viewportRect = getViewportRect();
        const bounds = styler.getBoundingClientRect();
        const container = getFixedContainingBlock(styler);
        const containerRect = container === document.documentElement
            ? { left: 0, top: 0 }
            : container.getBoundingClientRect();
        const maxX = viewportRect.width - bounds.width;
        const maxY = viewportRect.height - bounds.height;
        const clampedX = Math.min(Math.max(x, 0), maxX);
        const clampedY = Math.min(Math.max(y, 0), maxY);
        styler.style.left = `${clampedX - containerRect.left}px`;
        styler.style.top = `${clampedY - containerRect.top}px`;
        styler.style.position = "fixed";
        lastPos = { x: clampedX, y: clampedY };
    };

    const handleDragStart = (e) => {
        if (e.button !== 0) return;
        if (e.target.closest("input, select, textarea, button, label")) return;
        isDragging = true;
        const rect = styler.getBoundingClientRect();
        offsetX = e.clientX - rect.left;
        offsetY = e.clientY - rect.top;
        styler.style.transition = "none";

        const onMouseMove = (evt) => {
            if (!isDragging) return;
            const x = evt.clientX - offsetX;
            const y = evt.clientY - offsetY;
            applyPosition(x, y);
        };

        const onMouseUp = () => {
            isDragging = false;
            styler.style.transition = "";
            document.removeEventListener("mousemove", onMouseMove);
            document.removeEventListener("mouseup", onMouseUp);
            if (lastPos) {
                box._traceStylerPos = { ...lastPos };
            }
        };

        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
    };

    styler.addEventListener("mousedown", handleDragStart);
    styler.appendChild(root);

    const api = {
        root: styler,
        isOpen: () => styler.style.display === "flex",
        contains: (node) => styler.contains(node),
        show: openPanel,
        hide: () => {
            styler.style.display = "none";
        },
        destroy: () => {
            styler.removeEventListener("mousedown", handleDragStart);
            traceStylerButton?.removeEventListener("click", handleOpenClick);
            traceStylerRegistry.delete(api);
        },
        getSelectedTraceIndex: () =>
            traceSelect.value === "" ? null : Number(traceSelect.value),
        getStyle: () => ({
            line: {
                dash: lineDashSelect.value,
                color: lineColorInput.value,
                width: Number(lineWidthInput?.value ?? defaultTraceStyle.lineWidth),
            },
            opacity: Number(opacityInput?.value ?? defaultTraceStyle.opacity),
            marker: toggleInput.checked
                ? {
                    enabled: true,
                    size: Number(markerSizeInput?.value ?? defaultTraceStyle.markerSize),
                    symbol: markerSymbolSelect.value,
                }
                : { enabled: false },
        }),
        setTraces: (newTraces) => {
            syncTraceSelect(newTraces);
            syncControlsFromTrace();
        },
    };

    registerTraceStyler(api);

    return api;
}

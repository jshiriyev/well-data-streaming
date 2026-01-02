const DEFAULT_ANNOTATION = {
    text: "Select a series to display",
    x: 0.5, y: 0.5,
    xref: "paper", yref: "paper",
    showarrow: false,
    font: { size: 14, color: "rgba(0,0,0,0.55)" }
}

function toSeriesArray(series) {
    if (Array.isArray(series)) return series;
    if (series && typeof series === "object") return Object.values(series);
    return [];
}

function createBoxEmpty(host) {
    if (!host) return null;
    // don't create duplicates
    const existing = host.querySelector(":scope > .box-bottom");
    if (existing) return existing;

    const placeholder = document.createElement("button");
    placeholder.type = "button";
    placeholder.className = "box-bottom";
    placeholder.textContent = "+";
    placeholder.setAttribute("aria-label", "Add box");

    host.appendChild(placeholder);

    return placeholder;
}

function createBoxTemplate(index) {
    const parcelTmp = document.getElementById("parcel-box");
    const parcel = parcelTmp.content.cloneNode(true);

    const box = parcel.querySelector(".box");
    box.id = `box-${index}`;

    const boxHeader = box.querySelector(".box-header");

    const addTmp = document.getElementById("add-button");
    const add = addTmp.content.cloneNode(true);
    boxHeader.appendChild(add.querySelector('.add-button'));

    const setTmp = document.getElementById("settings-button");
    const set = setTmp.content.cloneNode(true);
    boxHeader.appendChild(set.querySelector('.settings-circle'));

    return box;
}

function createPlotSchema() {
    let traces = [];

    let layout = {
        // margin: { l: 60, r: 50, t: 40, b: 30 },
        autosize: true,
        height: undefined,
        width: undefined,
        // margin: { l: 0, r: 0, t: 0, b: 0 },
        margin: { l: 52, r: 18, t: 18, b: 44 },

        xaxis: {
            type: "date",
            title: { text: "" },
            zeroline: true,
            zerolinecolor: "rgba(0,0,0,0.08)", // Match grid color
            // zerolinewidth: 1,                         // Match grid width
            showgrid: true,
            gridcolor: "rgba(0,0,0,0.08)",
            ticks: "outside",
            tickcolor: "rgba(0,0,0,0.08)",
            tickfont: { size: 12 },
            linecolor: "rgba(0,0,0,0.08)",
            mirror: false,
            showline: true,
        },

        yaxis: {
            type: "linear",
            title: { text: "" },
            zeroline: true,
            zerolinecolor: "rgba(0,0,0,0.08)", // Match grid color
            gridwidth: 1,
            // zerolinewidth: 1,                         // Match grid width
            showgrid: true,
            gridcolor: "rgba(0,0,0,0.08)",
            ticks: "outside",
            tickcolor: "rgba(0,0,0,0.08)",
            tickfont: { size: 12 },
            linecolor: "rgba(0,0,0,0.08)",
            mirror: false,
            showline: true,
        },

        // xaxis: { title: "", domain: [0, 1], zeroline: false },
        // yaxis: { visible: false },
        // spikedistance: -1,
        showlegend: false,
        // legend: { x: 1, y: 0.95, xanchor: "right", yanchor: "top", bgcolor: "rgba(255,255,255,0.5)" },
        paper_bgcolor: "white",   // outside plot
        plot_bgcolor: "white",
        // plot_bgcolor: "#f9f9f9",  // inside plot area
        annotations: [DEFAULT_ANNOTATION]
    };

    const config = {
        responsive: true,
        displaylogo: false,
        // displayModeBar: false,
        modeBarButtonsToRemove: [
            "select2d",
            "lasso2d",
            "autoScale2d",
            "hoverClosestCartesian",
            "hoverCompareCartesian"
        ],
        // modeBarButtonsToAdd: [
        //     'v1hovermode',
        //     'hoverclosest',
        //     'hovercompare',
        //     'togglespikelines',
        //     'drawline',
        //     'eraseshape'
        // ],
        toImageButtonOptions: {
            format: 'png',
            filename: 'plot',
            // height: 600,
            // width: 800
        }
    };

    return { traces, layout, config };
}

function createBox(host, { fields, onAggSelectionsChange } = {}) {
    if (!host) return null;

    const box = createBoxTemplate(boxes.length);
    host.insertBefore(box, host.lastElementChild);
    box.fig = createPlotSchema();

    box.plotDiv = box.querySelector(".plot-display");

    const ro = new ResizeObserver(() => {
        Plotly.Plots.resize(box.plotDiv);
    });

    ro.observe(box.plotDiv.parentElement);
    box.fig.resizeObserver = ro;

    box.fields = fields ?? {};

    box.fig.left = [];
    box.fig.right = [];
    box.fig.axes = { left: [], right: [] };

    box.seriesPicker = createSeriesPicker(box, {
        getFigure: () => box.fig,
        getTraceData: (key) => getTraceData(box.traces, key),
        setTrace,
        removeTrace,
        fields: box.fields,
        onAggSelectionsChange: (selections) =>
            onAggSelectionsChange?.(box, selections),
    });

    box.traceStyler = createTraceStyler(box, { getFigure: () => box.fig });

    refreshPlot(box);
    return box;
}

function createNamePill(box, name) {
    const maxLen = 15;
    const truncated =
        name.length > maxLen ? name.slice(0, maxLen) + "…" : name;

    const pill = document.createElement("div");
    pill.className = "name-pill";
    pill.dataset.name = name;

    const label = document.createElement("span");
    label.className = "label";
    label.textContent = truncated;
    label.title = name; // show full name on hover

    const closeBtn = document.createElement("button");
    closeBtn.className = "close-btn";
    closeBtn.type = "button"
    closeBtn.textContent = "×";
    closeBtn.addEventListener("click", () => {
        removeTrace(box, name);
    });

    pill.appendChild(label);
    pill.appendChild(closeBtn);

    return pill;
}

function getTraceData(data, key) {
    const payload = data && typeof data === "object" ? data : {};
    return {
        name: key,
        x: toSeriesArray(payload.date),
        y: toSeriesArray(payload[key]),
        mode: "lines",
        type: "scatter",
    };
}

function setTrace(box, data) {

    const series = [...new Set(box.fig.traces.map(t => t.name))];

    if (series.includes(data.name)) {
        updateTrace(box, data);
        return; // breaks out of the function
    }

    if (series.length === 0) {
        box.fig.layout.annotations = []
    }

    const ref = box.fig.traces.length === 0 ? "y" : `y${box.fig.traces.length + 1}`;
    if (!box.fig.left.includes(ref)) {
        box.fig.left.push(ref);
    }
    const newTrace = {
        name: data.name,
        x: data.x,
        y: data.y,
        mode: data.mode,
        yaxis: ref,
    };
    const key = ref === "y" ? "yaxis" : `yaxis${ref.slice(1)}`;
    box.fig.layout[key] = {
        title: data.name,
        overlaying: box.fig.traces.length === 0 ? undefined : "y",
        automargin: true,
    };
    box.fig.traces.push(newTrace);
    refreshPlot(box);
    box.traceStyler?.setTraces(box.fig.traces);

    const tabs = box.querySelector(".box-header");
    const settings = box.querySelector(".settings-circle");
    tabs.insertBefore(createNamePill(box, data.name), settings);
}

function updateTrace(box, data) {
    const traceIndex = box.fig.traces.findIndex((t) => t.name === data.name);
    if (traceIndex === -1) {
        return;
    }
    box.fig.traces[traceIndex].x = data.x
    box.fig.traces[traceIndex].y = data.y

    refreshPlot(box);
}

function removeTrace(box, traceName) {
    if (!box.fig) return;
    const series = [...new Set(box.fig.traces.map(t => t.name))];

    const traceIdx = box.fig.traces.findIndex((trace) => trace.name === traceName);
    if (traceIdx === -1) {
        return;
    }

    if (series.length === 1) {
        box.fig.layout.annotations = [DEFAULT_ANNOTATION]
    }

    const [removedTrace] = box.fig.traces.splice(traceIdx, 1);
    const axisRef = removedTrace.yaxis;

    box.fig.left = box.fig.left.filter((ref) => ref !== axisRef);
    box.fig.right = box.fig.right.filter((ref) => ref !== axisRef);
    const axisKey = axisRef === "y" ? "yaxis" : `yaxis${axisRef.slice(1)}`;
    delete box.fig.layout[axisKey];

    reindexAxes(box);
    refreshPlot(box);
    box.traceStyler?.setTraces(box.fig.traces);

    const tabs = box?.querySelector(".box-header");
    const pill = tabs?.querySelector(`.name-pill[data-name="${traceName}"]`);
    if (pill) {
        pill.remove();
    }

    const picker = box?.querySelector(".series-picker");

    const checkbox = picker?.querySelector(
        `.series-picker-choices input[name="choice"][value="${traceName}"]`
    );

    if (checkbox) {
        checkbox.checked = false;
        const select = checkbox.closest("label")?.querySelector('select[name="agg-select"]');
        if (select) {
            select.disabled = true;
        }
    }

    const aggSelections = box?.lastAggs;
    if (aggSelections && Object.prototype.hasOwnProperty.call(aggSelections, traceName)) {
        delete aggSelections[traceName];
    }
}

function reindexAxes(box) {
    const axisSide = new Map();
    box.fig.left.forEach((ref) => axisSide.set(ref, "left"));
    box.fig.right.forEach((ref) => axisSide.set(ref, "right"));

    const layoutByRef = {};
    Object.keys(box.fig.layout).forEach((key) => {
        if (!key.startsWith("yaxis")) return;
        const ref = key === "yaxis" ? "y" : `y${key.slice(5)}`;
        layoutByRef[ref] = box.fig.layout[key];
        delete box.fig.layout[key];
    });

    box.fig.left = [];
    box.fig.right = [];

    box.fig.traces.forEach((trace, idx) => {
        const oldRef = trace.yaxis;
        const newRef = idx === 0 ? "y" : `y${idx + 1}`;
        const side = axisSide.get(oldRef) || "left";
        trace.yaxis = newRef;

        const layoutKey = newRef === "y" ? "yaxis" : `yaxis${newRef.slice(1)}`;
        const layoutTemplate = { ...(layoutByRef[oldRef] || {}) };
        if (idx === 0) {
            delete layoutTemplate.overlaying;
        } else {
            layoutTemplate.overlaying = "y";
        }
        layoutTemplate.title = layoutTemplate.title || trace.name;
        layoutTemplate.automargin = layoutTemplate.automargin ?? true;

        box.fig.layout[layoutKey] = layoutTemplate;

        if (side === "right") {
            box.fig.right.push(newRef);
        } else {
            box.fig.left.push(newRef);
        }
    });
}

function setAxisLimits(box, ref, cfg = {}) {
    if (!box?.plotDiv || !ref) return;
    const key = ref === "y" ? "yaxis" : `yaxis${ref.slice(1)}`;
    const gd = box.plotDiv;

    // Prefer computed range from _fullLayout (more reliable than layout)
    const axisFull = gd._fullLayout?.[key];
    const axisLay = gd.layout?.[key];
    const currentRange = axisFull?.range || axisLay?.range || null;

    const preserve = cfg.preserve !== false; // default true

    const updates = {};

    // --- RESET ---
    if (cfg.reset) {
        updates[`${key}.autorange`] = true;
        updates[`${key}.range`] = null;
        updates[`${key}.rangemode`] = null;
        Plotly.relayout(box.plotDiv, updates);
        return;
    }

    if (Array.isArray(cfg.range)) {
        updates[`${key}.autorange`] = false;
        updates[`${key}.range`] = cfg.range;
    } else if ("min" in cfg || "max" in cfg) {
        const min = ("min" in cfg) ? cfg.min : (preserve ? currentRange?.[0] : null);
        const max = ("max" in cfg) ? cfg.max : (preserve ? currentRange?.[1] : null);
        const minVal = min ?? null;
        const maxVal = max ?? null;
        updates[`${key}.range`] = [minVal, maxVal];
        if (!("autorange" in cfg)) {
            if (minVal != null && maxVal != null) {
                updates[`${key}.autorange`] = false;
            } else if (minVal != null) {
                updates[`${key}.autorange`] = "max";
            } else if (maxVal != null) {
                updates[`${key}.autorange`] = "min";
            }
        }
    }

    // --- AUTORANGE ---
    if ("autorange" in cfg) {
        updates[`${key}.autorange`] = cfg.autorange;
        if (cfg.autorange) {
            updates[`${key}.range`] = null;
        }
    }

    // --- RANGE MODE ---
    if ("rangemode" in cfg) {
        updates[`${key}.rangemode`] = cfg.rangemode;
    }

    Plotly.relayout(box.plotDiv, updates);
}

function moveAxisRight(box, ref) {
    box.fig.left = box.fig.left.filter((r) => r !== ref);
    if (!box.fig.right.includes(ref)) {
        box.fig.right.push(ref);
    }
    refreshPlot(box);
}

function moveAxisLeft(box, ref) {
    box.fig.right = box.fig.right.filter((r) => r !== ref);
    if (!box.fig.left.includes(ref)) {
        box.fig.left.push(ref);
    }
    refreshPlot(box);
}

function makeAxisBuilder(box) {
    return function ({ side, base, step }) {
        // left goes inward (−), right goes outward (+)
        const dir = side === "left" ? -1 : 1;

        return (ref, idx) => {
            const key = ref === "y" ? "yaxis" : `yaxis${ref.slice(1)}`;
            const existing = box.fig.layout[key] || {};
            const position = base + dir * idx * step;
            const axisDef = {
                ...existing,
                side,
                anchor: idx === 0 ? "x" : "free",
            };

            if (idx === 0) {
                delete axisDef.position;
            } else {
                axisDef.position = position;
            }

            box.fig.layout[key] = axisDef;
            box.fig.axes[side].push({ ref, paperX: position });
            box.fig.layout.shapes.push({
                type: "rect",
                xref: "paper",
                yref: "paper",
                x0: position,
                x1: position,
                y0: 0,
                y1: 1,
                line: {
                    width: 1,
                    color: "rgba(120,120,120,0.6)",
                },
            });
        };
    };
}

function rebuildLayout(box) {

    const leftCount = box.fig.left.length;
    const rightCount = box.fig.right.length;

    const leftStep = 0.05;
    const rightStep = 0.05;

    const domainStart = Math.max(0, (leftCount - 1) * leftStep);
    const domainEnd = 1 - Math.max(0, (rightCount - 1) * rightStep);

    box.fig.layout.xaxis = {
        ...(box.fig.layout.xaxis || {}),
        domain: [domainStart, domainEnd],
    };

    box.fig.layout.shapes = [];
    box.fig.axes.left = [];
    box.fig.axes.right = [];

    box.fig.left.forEach(
        makeAxisBuilder(box)({
            side: "left",
            base: domainStart,
            step: leftStep,
        })
    );

    box.fig.right.forEach(
        makeAxisBuilder(box)({
            side: "right",
            base: domainEnd,
            step: rightStep,
        })
    );

    // Clean up unused axis layout entries
    Object.keys(box.fig.layout).forEach((key) => {
        if (!key.startsWith("yaxis")) return;
        const ref = key === "yaxis" ? "y" : `y${key.replace("yaxis", "")}`;
        if (!box.fig.left.includes(ref) && !box.fig.right.includes(ref)) {
            delete box.fig.layout[key];
        }
    });
}

function getPlotBox(plotDiv) {
    const full = plotDiv._fullLayout;
    if (full?._plots?.xy?.plotbox) return full._plots.xy.plotbox;
    if (full?._size) {
        const { l, t, w, h } = full._size;
        return { x0: l, x1: l + w, y0: t, y1: t + h };
    }
    return null;
}

function rebuildMarkers(box) {
    const axisControl = box?.querySelector(".axis-control");
    if (!axisControl) return;
    if (!box.plotDiv) return;

    axisControl.innerHTML = "";
    const plotBox = getPlotBox(box.plotDiv);
    if (!plotBox) {
        requestAnimationFrame(() => rebuildMarkers(box));
        return;
    }

    const plotRect = box.plotDiv.getBoundingClientRect();
    const axisRect = axisControl.getBoundingClientRect();
    const span = plotBox.x1 - plotBox.x0;
    if (!Number.isFinite(span) || span <= 0) return;
    const plotLeft = plotRect.left + plotBox.x0;

    const addColumn = (item, side) => {
        const column = document.createElement("div");
        column.className = "axis-control-column";
        const xPx = plotLeft + item.paperX * span;
        column.style.left = `${xPx - axisRect.left}px`;
        column.appendChild(addArrow(item, side));
        column.appendChild(addToZero(item));
        column.appendChild(addReset(item));
        axisControl.appendChild(column);
        return column;
    };

    const addArrow = (item, side) => {
        const arrow = document.createElement("div");
        arrow.className = "icon arrow";
        arrow.dataset.axisRef = item.ref;
        arrow.dataset.side = side;
        arrow.textContent = side === "left" ? "→" : "←";
        arrow.title = side === "left" ? "Move axis to right" : "Move axis to left";
        arrow.addEventListener("click", (e) => {
            e.stopPropagation();
            if (side === "left") {
                moveAxisRight(box, item.ref);
            } else {
                moveAxisLeft(box, item.ref);
            }
        });
        return arrow;
    };

    const addToZero = (item) => {
        const tozero = document.createElement("div");
        tozero.className = "icon tozero";
        tozero.dataset.axisRef = item.ref;
        tozero.textContent = "↓";
        tozero.title = "Set range mode to 'tozero'";
        tozero.addEventListener("click", (e) => {
            e.stopPropagation();
            setAxisLimits(box, item.ref, { rangemode: "tozero"});
        });
        return tozero;
    };

    const addReset = (item) => {
        const reset = document.createElement("div");
        reset.className = "icon reset";
        reset.dataset.axisRef = item.ref;
        reset.textContent = "↺";
        reset.title = "Reset axis limits";
        reset.addEventListener("click", (e) => {
            e.stopPropagation();
            setAxisLimits(box, item.ref, { reset: true });
        });
        return reset;
    }

    box.fig.axes.left.forEach((item) => addColumn(item, "left"));
    box.fig.axes.right.forEach((item) => addColumn(item, "right"));
}

function refreshPlot(box) {
    rebuildLayout(box);
    Plotly.react(
        box.plotDiv,
        box.fig.traces,
        box.fig.layout,
        box.fig.config
    ).then(() => {
        rebuildMarkers(box);
    });
}

function setBoxTitle(box, title) {
    const titleDiv = box.querySelector(".box-title");
    titleDiv.textContent = title;
}

function clearBox(box) {
    if (!box.fig) return;
    box.fig.traces = [];
    box.fig.left = [];
    box.fig.right = [];
    box.fig.layout.annotations = [DEFAULT_ANNOTATION];
    refreshPlot(box);
    box.traceStyler?.setTraces(box.fig.traces);
    const tabs = box.querySelector(".box-header");
    const pills = tabs.querySelectorAll(".name-pill");
    pills.forEach((pill) => pill.remove());
}

function destroyBox(box) {
    if (!box) return;
    box.fig.resizeObserver?.disconnect();
    Plotly.purge(box.plotDiv);
    box.remove();
}


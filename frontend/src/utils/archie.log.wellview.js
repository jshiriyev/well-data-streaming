const LOG_WELLVIEW_STATE = {
    depth: Object.freeze({
        top: 1000.,
        base: 2000.,
    }),
    grid: Object.freeze({
        show: true,
        color: "#20305f",
        minor: Object.freeze({
            show: false,
            color: "#20305f",
        }),
    }),
    box: Object.freeze({
        show: true,
        color: "#20305f",
        trailGap: 0.01,
        cycleGap: 0.08,
    }),
}

function createLogState(overrides = {}) {
    const state = Object.create(LOG_WELLVIEW_STATE);

    const baseCurves = overrides.curves ?? [];
    state.curves = baseCurves.map(curve => ({ ...curve }));

    state.depth = {
        ...LOG_WELLVIEW_STATE.depth,
        ...(overrides.depth ?? {}),
    };

    const gridOverride = overrides.grid ?? {};
    state.grid = {
        ...LOG_WELLVIEW_STATE.grid,
        ...gridOverride,
        minor: {
            ...LOG_WELLVIEW_STATE.grid.minor,
            ...(gridOverride.minor ?? {}),
        },
    };

    state.box = {
        ...LOG_WELLVIEW_STATE.box,
        ...(overrides.box ?? {}),
    };

    Object.defineProperties(state, {
        trails: {
            enumerable: false,
            get() {
                if (!Array.isArray(this.curves) || this.curves.length === 0) return 1;

                let maxTrail = -1;

                for (const c of this.curves) {
                    if (Number.isFinite(c.trail) && c.trail > maxTrail) maxTrail = c.trail;
                }
                if (maxTrail === -1) maxTrail = 0;

                return maxTrail + 1;
            },
        },
        cycles: {
            enumerable: false,
            get() {
                if (!Array.isArray(this.curves) || this.curves.length === 0) return 1;
                const maxByTrail = new Map();

                for (const curve of this.curves) {
                    if (!Number.isFinite(curve.trail) || !Number.isFinite(curve.cycle)) continue;
                    const next = curve.cycle + 1;
                    const prev = (maxByTrail.get(curve.trail) ?? 0);
                    if (next > prev) maxByTrail.set(curve.trail, next);
                }

                let max = 1;
                for (const v of maxByTrail.values()) if (v > max) max = v;
                return max;
            },
        },
        depthRange: {
            enumerable: false,
            get() {
                const toNumber = ((value) => {
                    if (value === "" || value == null) return null;
                    const n = Number(value);
                    return Number.isFinite(n) ? n : null;
                });

                const top = toNumber(this.depth?.top);
                const base = toNumber(this.depth?.base);
                if (top == null || base == null) return null;
                return [base, top];
            },
        }
    });

    function getFirstCurveByTrail(trail) {
        let lowestCurve = null;

        for (const curve of this.curves) {
            if (curve.trail !== trail) continue;
            if (!Number.isFinite(curve.cycle)) continue;
            if (!lowestCurve || curve.cycle < lowestCurve.cycle) lowestCurve = curve;
        }
        return lowestCurve;
    }

    function getFirstCurveByMnemo(mnemo) {
        if (!Array.isArray(this.curves)) return null;
        const curve = this.curves.find(c => c.mnemo === mnemo);
        return curve ?? null;
    }

    state.getFirstCurveByTrail = getFirstCurveByTrail;
    state.getFirstCurveByMnemo = getFirstCurveByMnemo;

    return state;
}

function buildLogFigure(state) {
    const traces = [];
    const layout = {
        showlegend: false,
        dragmode: 'pan',
        margin: { l: 68, r: 24, t: 28, b: 14 },
        hovermode: "closest",
        uirevision: "archie",
        yaxis: {
            autorange: "reversed",
            zeroline: false,
            domain: [0, 1 - (state.cycles - 1) * state.box.cycleGap],
            showline: !!state.box?.show,
            showgrid: !!state.grid?.show,
            minor: {
                showgrid: !!state.grid?.minor?.show
            },
            ticks: "outside",
            ticklen: 4,
            tickfont: { size: 11 }
        },
        plot_bgcolor: "rgba(0,0,0,0)",
        paper_bgcolor: "rgba(0,0,0,0)",
        shapes: [],
    };

    if (state.depthRange) {
        layout.yaxis.range = state.depthRange;
    }

    (() => {
        const counters = new Map();
        for (const curve of state.curves) {
            if (Object.hasOwn(curve, "cycle") && !Number.isFinite(curve.cycle)) continue;
            if (!Number.isFinite(curve.trail)) continue;
            const nextCycle = counters.get(curve.trail) ?? 0;
            curve.cycle = nextCycle;
            counters.set(curve.trail, nextCycle + 1);
        }
    })();

    const gap = Math.max(0, Number(state.box.trailGap) || 0);
    const totalGap = gap * (state.trails - 1);
    const trailWidth = (1 - totalGap) / state.trails;

    for (let i = 0; i < Math.max(state.curves.length, 1); i += 1) {
        const curve = state.curves.length === 0 ? {
            mnemo: "",
            trail: 0,
            cycle: 0,
            range: null,
        } : state.curves[i];

        if (!Object.hasOwn(curve, "xaxis")) {
            curve.xaxis = i === 0 ? "xaxis" : `xaxis${i + 1}`;
        }

        const start = curve.trail * (trailWidth + gap);
        const end = start + trailWidth;

        layout[curve.xaxis] = {
            side: 'top',
            title: { standoff: 0, text: curve.mnemo },
            zeroline: false,
            domain: [start, end],
            showline: !!state.box?.show,
            showgrid: curve.cycle === 0 && !!state.grid?.show,
            minor: {
                showgrid: curve.cycle === 0 && !!state.grid?.minor?.show
            },
            ticks: "outside",
            ticklen: 4,      // Shortens the physical tick marks
            tickfont: { size: 11 },
            automargin: true,
            anchor: 'free',     // Anchors to the main x-axis
            position: 1 - (state.cycles - 1 - curve.cycle) * state.box.cycleGap,
            range: curve.range,
        };
    }

    for (let i = 0; i < state.curves.length; i += 1) {
        const curve = state.curves[i];
        if (!Object.hasOwn(curve, "x")) {
            curve.x = i === 0 ? "x" : `x${i + 1}`;
        }
        const firstCurve = state.getFirstCurveByTrail(curve.trail);

        const trace = {
            x: curve.array,
            y: state.depth.array,
            hoverinfo: "skip",
            showlegend: false,
            line: { width: curve.line.width },
            xaxis: curve.x,
            yaxis: 'y',
            overlaying: firstCurve.x,
        }

        if ("fill" in curve) {
            trace.fill = curve.fill
        }

        if ("fillcolor" in curve) {
            trace.fillcolor = curve.fillcolor
        }

        traces.push(trace);
    };

    const addShapeLine = (x0, x1, y0, y1, width = 1) => {
        layout.shapes.push({
            type: "line",
            xref: "paper",
            yref: "paper",
            x0, x1, y0, y1,
            line: { width }
        });
    };

    if (state.box.show) {
        for (let i = 0; i < state.trails; i += 1) {
            const start = i * (trailWidth + gap);
            const end = start + trailWidth;
            // vertical separators: draw start only for i>0 to avoid duplicates at shared borders
            if (i > 0) addShapeLine(start, start, 0, 1 - (state.cycles - 1) * state.box.cycleGap, width = 0.5);
            // right border always
            addShapeLine(end, end, 0, 1 - (state.cycles - 1) * state.box.cycleGap, width = 0.5);
            // bottom border
            addShapeLine(start, end, 0, 0, width = 0.5);
        }
    }

    const config = {
        responsive: true,
        displaylogo: false,
        scrollZoom: true,
        displayModeBar: false,
        // modeBarButtonsToRemove: ["lasso2d", "select2d"]
    };

    return { traces, layout, config };
}

function createLogPlot(
    root,
    data = undefined,
    state = createLogState(),
) {
    const getXData = ((mnemo) => {
        if (!data || data[mnemo] === undefined) {
            return [];
        }
        return data[mnemo];
    });

    (() => {
        state.depth.array = data.depth
        for (curve of state.curves) {
            curve.array = getXData(curve.mnemo)
        }
        render();
    })();

    function addCurve(
        mnemo,
        {
            trail = null,
            line = { width: 1 },
            ...kwargs
        } = {}
    ) {
        if (trail == null) {
            trail = state.trails;
        }
        state.curves.push({
            mnemo,
            array: getXData(mnemo),
            trail,
            line,
            ...kwargs
        });
        render();
    }

    function removeCurve(mnemo) {
        state.curves = state.curves.filter(curve => curve.mnemo !== mnemo);
        render()
    }

    function addTops() {
        render();
    }

    function removeTops() {
        render();
    }

    function addPerfs() {
        render();
    }

    function removePerfs() {
        render();
    }

    function addCut(mnemo, value, left = false, fillcolor = "rgba(0,150,255,0.35)") {
        const curve = state.getFirstCurveByMnemo(mnemo)

        const defaults = {
            trail: curve.trail,
            cycle: Infinity,
            line: { width: 0 },
            showlegend: false,
            xaxis: curve.x,
            x: curve.x,
        }

        state.curves.push({
            mnemo: "Cut Line",
            array: Array(state.depth.array.length).fill(value),
            ...defaults
        });

        const array = curve.array.map(v =>
            left
                ? (v >= value ? null : v)
                : (v <= value ? null : v)
        );

        state.curves.push({
            mnemo: "Cut Fill",
            array: array,
            fill: "tonextx",
            fillcolor: fillcolor,
            ...defaults
        });

        render();
    }

    function removeCut() {
        render();
    }

    function render() {
        if (!root) return;
        if (!Plotly) {
            return
        }
        figure = buildLogFigure(state);
        // console.log(figure.traces);
        // console.log(figure.layout);
        // console.log(figure.config);
        Plotly.react(
            root,
            figure.traces,
            figure.layout,
            figure.config
        );
    }

    return {
        state,
        addCurve,
        removeCurve,
        addTops,
        removeTops,
        addPerfs,
        removePerfs,
        addCut,
        removeCut,
        render,
    }
}

const state = createLogState({
    curves: [
        {
            mnemo: 'NPHI',
            trail: 0,
            line: {
                width: 1,
            },
            range: [0, 0.6]
        }
    ],
    box: {
        trailGap: 0.05,
        // cycleGap: 0.08,
    }
})

const a = createLogPlot('logView', logData, state)
a.addCurve('RHOB', { trail: 1, range: [1.95, 2.95] })
a.addCurve('GR', { trail: 0 })
a.addCut('GR', 60, left = false)

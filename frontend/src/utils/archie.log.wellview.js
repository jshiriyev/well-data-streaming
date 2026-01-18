const DEFAULT_LOG_WELLVIEW_STATE = {
    curves: [
        {
            mnemo: 'undefined',
            trail: 0,
            cycle: 0,
            line: {
                width: 1,
            },
        }
    ],
    get trails() {
        if (!this.curves.length) return null;
        return Math.max(...this.curves.map(curve => curve.trail ?? -Infinity)) + 1;
    },
    get cycles() {
        if (!this.curves.length) return null;
        return Math.max(...this.curves.map(curve => curve.cycle ?? -Infinity)) + 1;
    },
    depth: {
        array: [],
        top: 1000.,
        base: 2000.,
    },
    grid: {
        show: true,
        color: "#20305f",
        minor: {
            show: false,
            color: "#20305f",
        }
    },
    box: {
        show: true,
        color: "#20305f",
        gap: 0.01,
    }
}

function createLogState(overrides = {}) {
    const state = Object.create(DEFAULT_LOG_WELLVIEW_STATE);

    const baseCurves = overrides.curves ?? DEFAULT_LOG_WELLVIEW_STATE.curves;
    state.curves = baseCurves.map(curve => ({ ...curve }));

    state.depth = {
        ...DEFAULT_LOG_WELLVIEW_STATE.depth,
        ...(overrides.depth ?? {}),
    };

    const gridOverride = overrides.grid ?? {};
    state.grid = {
        ...DEFAULT_LOG_WELLVIEW_STATE.grid,
        ...gridOverride,
        minor: {
            ...DEFAULT_LOG_WELLVIEW_STATE.grid.minor,
            ...(gridOverride.minor ?? {}),
        },
    };

    state.box = {
        ...DEFAULT_LOG_WELLVIEW_STATE.box,
        ...(overrides.box ?? {}),
    };

    const otherOverrides = { ...overrides };
    delete otherOverrides.curves;
    delete otherOverrides.depth;
    delete otherOverrides.grid;
    delete otherOverrides.box;
    Object.assign(state, otherOverrides);

    return state;
}

function buildLogFigure(state) {

    function getFirstCurveOnTrail(trail) {
        let best = null;

        for (const curve of state.curves) {
            if (curve.trail !== trail) continue;
            if (!best || curve.cycle < best.cycle) {
                best = curve;
            }
        }
        return best;
    }

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

    const toNumber = ((value) => {
        if (value === "" || value == null) return null;
        const n = Number(value);
        return Number.isFinite(n) ? n : null;
    });

    const depthRange = (() => {
        const top = toNumber(state.depth.top);
        const base = toNumber(state.depth.base);
        if (top == null || base == null) return null;
        return [base, top];
    })();

    if (depthRange) {
        layout.yaxis.range = depthRange;
    }

    const addShapeLine = (x0, x1, y0, y1, width = 1) => {
        layout.shapes.push({
            type: "line",
            xref: "paper",
            yref: "paper",
            x0, x1, y0, y1,
            line: { width }
        });
    };

    const gap = Math.max(0, Number(state.box.gap) || 0);
    const totalGap = gap * (state.trails - 1);
    const trailWidth = (1 - totalGap) / state.trails;

    for (let i = 0; i < state.curves.length; i += 1) {
        const curve = state.curves[i];

        curve.x = i === 0 ? "x" : `x${i + 1}`;
        curve.xaxis = i === 0 ? "xaxis" : `xaxis${i + 1}`;

        curve.xstart = curve.trail * (trailWidth + gap);
        curve.xend = curve.xstart + trailWidth;

        const firstCurve = getFirstCurveOnTrail(curve.trail);

        const overlaying = curve.cycle > 0 ? firstCurve.x : 'free';

        layout[curve.xaxis] = {
            side: 'top',
            title: { standoff: 0, text: curve.mnemo },
            zeroline: false,
            domain: [curve.xstart, curve.xend],
            showline: !!state.box?.show,
            showgrid: !!state.grid?.show,
            minor: {
                showgrid: !!state.grid?.minor?.show
            },
            ticks: "outside",
            ticklen: 4,      // Shortens the physical tick marks
            tickfont: { size: 11 },
            automargin: true,
            anchor: 'free',     // Anchors to the main x-axis
            position: 1,
        };

        traces.push({
            x: curve.array,
            y: state.depth.array,
            hoverinfo: "skip",
            showlegend: false,
            line: { width: curve.line.width },
            xaxis: curve.x,
            yaxis: 'y',
            overlaying: overlaying,
        });
    };

    for (let i = 0; i < state.trails; i += 1) {

        const start = i * (trailWidth + gap);
        const end = start + trailWidth;

        if (!state.box.show) continue;

        // vertical separators: draw start only for i>0 to avoid duplicates at shared borders
        if (i > 0) addShapeLine(start, start, 0, 1, width = 0.5);
        // right border always
        addShapeLine(end, end, 0, 1, width = 0.5);
        // bottom border
        addShapeLine(start, end, 0, 0, width = 0.5);
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
    plotHost,
    logData,
    state = createLogState(),
) {
    let figure = buildLogFigure(state);

    function getLastCurveOnTrail(trail) {
        let best = null;

        for (const curve of state.curves) {
            if (curve.trail !== trail) continue;
            if (!best || curve.cycle > best.cycle) {
                best = curve;
            }
        }
        return best;
    }

    function addTrace(mnemo, trail = undefined, cycle = undefined, overlay = false) {

        if (logData?.[mnemo] === undefined) {
            x = [];
            y = [];
        } else {
            x = logData[mnemo];
            y = logData.depth;
        }

        if ( trail === undefined ) {
            trail = 0;
        }

        if ( cycle === undefined ) {
            cycle = getLastCurveOnTrail(trail) + 1
        }
        console.log(state.trails)
        state.curves.push({
            mnemo: mnemo,
            array: x,
            trail: trail,
            cycle: cycle,
            line: {
                width: 1,
            },
            overlaying: 'free',
        })
        console.log(state.trails)
        state.depth.array = y;
        render();
    }

    function removeTrace(index, mnemo) {
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

    function addCut(mnemo, cutValue, fill = "right") {

        const cutTrace = {
            name: "Cut Trace",
            x: logData.NPHI,
            y: logData.depth,
            type: "scatter",
            mode: "lines",
            line: { color: "blue", width: 2 },
            xaxis: "x3"
        }
        const trace = structuredClone(state.traces[2])
        trace.x = Array(trace.y.length).fill(value)
        trace.line.width = 0
        trace.showlegend = false

        const leftFillTrace = structuredClone(traces[2])
        leftFillTrace.x = leftFillTrace.x.map(v => (v <= value ? v : null));
        leftFillTrace.fill = "tonextx"
        leftFillTrace.fillcolor = "rgba(0,150,255,0.35)"
        leftFillTrace.showlegend = false

        // const leftFillTrace = {
        //     x: fillx,
        //     y: trace.y,
        //     mode: "lines",
        //     line: { width: 0 },
        //     fill: "tonextx",
        //     fillcolor: "rgba(0,150,255,0.35)",
        //     name: "Left Fill",
        //     showlegend: false,
        //     xaxis: "x3"
        // };
        return [leftFillTrace]
    }

    function removeCut() {
        render();
    }

    function render() {
        if (!plotHost) return;
        if (!Plotly) {
            return
        }
        figure = buildLogFigure(state);
        Plotly.react(
            plotHost,
            figure.traces,
            figure.layout,
            figure.config
        );
    }

    return {
        state,
        figure,
        addTrace,
        removeTrace,
        addTops,
        removeTops,
        addPerfs,
        removePerfs,
        addCut,
        removeCut,
        render,
    }
}

const a = createLogPlot('logView', logData,)
a.render()
// a.addTrace(1, 'GR')
// a.addTrace(1, 'NPHI')

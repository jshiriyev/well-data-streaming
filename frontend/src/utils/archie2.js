const DEFAULT_LOG_PLOT_SETTINGS = {
    trail: {
        count: 1,
        gap: 0.,
    },
    depth: {
        top: 1000.,
        base: 2000.,
    },
    grid: {
        show: true,
        minor: {
            show: false,
        }
    },
    box: {
        show: true,
    }
}

function createLogState(overrides = {}) {
    const state = {
        ...DEFAULT_LOG_PLOT_SETTINGS,
        ...overrides,
    };
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
            showline: !!state.box?.show,
            showgrid: !!state.grid?.show,
            minor: {
                showgrid: !!state.grid?.minor?.show
            },
            ticks: "outside",
            ticklen: 4,
            tickfont: { size: 11 }
        },
        shapes: [],
        plot_bgcolor: "rgba(0,0,0,0)",
        paper_bgcolor: "rgba(0,0,0,0)",
    };

    const clamp = ((n, min, max) => {
        return Math.max(min, Math.min(max, n));
    });

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

    const gap = clamp(Number(state.trail.gap) || 0, 0, 0.05);
    const totalGap = gap * (state.trail.count - 1);
    const width = (1 - totalGap) / state.trail.count;

    for (let i = 0; i < state.trail.count; i++) {
        const xKey = i === 0 ? "x" : `x${i + 1}`;
        const xAxisKey = i === 0 ? "xaxis" : `xaxis${i + 1}`;

        traces.push({
            x: [],
            y: [],
            hoverinfo: "skip",
            showlegend: false,
            xaxis: xKey,
            yaxis: "y",
        });

        const start = i * (width + gap);
        const end = start + width;

        layout[xAxisKey] = {
            side: 'top',
            title: { standoff: 0, },
            zeroline: false,
            domain: [start, end],
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

        if (!state.box.show) continue;

        // vertical separators: draw start only for i>0 to avoid duplicates at shared borders
        if (i > 0) addShapeLine(start, start, 0, 1);
        // right border always
        addShapeLine(end, end, 0, 1);
        // bottom border
        addShapeLine(start, end, 0, 0);
    };

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
    logState = createLogState(),
) {
    const figure = buildLogFigure(logState);

    function addTrace( index, mnemo ) {
        const xKey = index === 0 ? "x" : `x${index + 1}`;
        const xAxisKey = index === 0 ? "xaxis" : `xaxis${index + 1}`;

        const trace = {
            name: mnemo,
            x: logData[mnemo],
            y: logData['depth'],
            mode: "lines",
            line: { 
                width: 1,
                // color: undefined
            },
            showlegend: false,
            xaxis: xKey,
        };
        figure.traces.push(trace)

        figure.layout[xAxisKey].title.text = mnemo;

        render();
    }

    function addTops() {
        render();
    }

    function addPerfs() {
        render()
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
        leftFillTrace.fillcolor = "rgba(0,150,255,0.35)",
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

    function render() {
        if (!plotHost) return;
        if (!Plotly) {
            return
        }
        Plotly.react(
            plotHost,
            figure.traces,
            figure.layout,
            figure.config
        );
    }

    return {
        figure,
        addTrace,
        addTops,
        addPerfs,
        addCut,
        render,
    }
}

const state = createLogState()
state.trail.count = 2;
state.trail.gap = 0.05;
const a = createLogPlot('logView',logData,state)
a.render()
a.addTrace(1,'GR')
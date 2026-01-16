const traces = [
    {
        name: "GR",
        x: logData.GR,
        y: logData.depth,
        type: "scatter",
        mode: "lines",
        line: { color: "green", width: 2 },
        xaxis: "x1"
    },
    {
        name: "RHOB",
        x: logData.RHOB,
        y: logData.depth,
        type: "scatter",
        mode: "lines",
        line: { color: "red", width: 2 },
        xaxis: "x2"
    },
    {
        name: "NPHI",
        x: logData.NPHI,
        y: logData.depth,
        type: "scatter",
        mode: "lines",
        line: { color: "blue", width: 2 },
        xaxis: "x3"
    }
];

function vLine(x, y0 = 0.0, y1 = 1.0) {
    return {
        type: "line",
        xref: "paper",
        yref: "paper",
        x0: x,
        x1: x,
        y0: y0,
        y1: y1,
        line: {
            width: 1,
        }
    };
}

function hLine(y, x0 = 0.0, x1 = 1.0) {
    return {
        type: "line",
        xref: "paper",
        yref: "paper",
        x0: x0,
        x1: x1,
        y0: y,
        y1: y,
        line: {
            width: 1,
        }
    };
}

const layout = {
    showlegend: false,
    dragmode: 'pan',

    // DEPTH AXIS
    yaxis: {
        title: "Depth (m)",
        showline: true,
        autorange: "reversed",
        showgrid: true,
        zeroline: false,
        domain: [0, 0.92]
    },

    // TRACK 1 – GR
    xaxis: {
        title: {
            text: "GR (API)",
            standoff: 0
        },
        showline: true,
        ticklen: 4,      // Shortens the physical tick marks
        ticks: 'outside', // Or 'inside' to flip them
        automargin: true,
        domain: [0.0, 0.48],
        range: [0, 150],
        showgrid: true,
        side: 'top',
        zeroline: false,
        position: 0.92,

    },

    // TRACK 2 – RHOB
    xaxis2: {
        title: {
            text: "RHOB (g/cc)",
            standoff: 0
        },
        showline: true,
        ticklen: 4,      // Shortens the physical tick marks
        ticks: 'outside', // Or 'inside' to flip them
        automargin: true,
        domain: [0.34, 0.66],
        range: [1.95, 2.75],
        showgrid: false,
        overlaying: 'x', // Overlays the first x-axis
        side: 'top',     // Positions it at the top
        anchor: 'free',     // Anchors to the main x-axis

        position: 1,    // Positioned at the very top (relative to chart),
        zeroline: false,
    },

    // TRACK 3 – NPHI
    xaxis3: {
        title: {
            text: "NPHI (v/v)",
            standoff: 0 // Decreases distance (in pixels) from tick labels
        },
        showline: true,
        automargin: true, // Ensures the title doesn't get cut off
        domain: [0.52, 1.0],
        range: [0.0, 0.45],
        showgrid: true,
        side: 'top',
        zeroline: false,
        position: 0.92,
        ticklen: 4,      // Shortens the physical tick marks
        ticks: 'outside', // Or 'inside' to flip them
    },

    margin: {
        l: 80,
        r: 20,
        t: 40,
        b: 40
    },

    hovermode: "closest",

    shapes: [
        vLine(0.48, 0, 0.92),
        vLine(0.52, 0, 0.92),
        vLine(1.00, 0, 0.92),
        hLine(0.00, 0, 0.48),
        hLine(0.00, 0.52, 1.0)
    ],
};

const config = {
    responsive: true,
    displaylogo: false,
    scrollZoom: true,
    // displayModeBar: false,
    modeBarButtonsToRemove: ["lasso2d", "select2d"]
};

function addCut(value) {
    const trace = structuredClone(traces[2])
    trace.x =  Array(trace.y.length).fill(value)
    trace.fill = 'tonextx' // Fills down to the x-axis (or the trace below if available)
    trace.line.width = 0
    return trace
}

traces.push(addCut(0.22))

Plotly.react("logView", traces, layout, config)
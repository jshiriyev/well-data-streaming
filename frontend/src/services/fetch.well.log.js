const USE_MOCK_LOG_DATA = String(import.meta.env.VITE_USE_MOCK_DATA || "").toLowerCase() === "true";

function mockFetchWellLog() {
    const depth = Array.from({ length: 2000 }, (_, i) => i + 1000); // 1000..2999
    // Example curves
    const gr = depth.map((d) => 40 + 20 * Math.sin(d / 80));
    const res = depth.map((d) => 10 + 5 * Math.cos(d / 120));
    return {
        DEPT: depth,
        gr: {
            mnemo: "GR (API)",
            unit: "API",
            value: gr,
            descr: "",
        },
        res: {
            mnemo: "Resistivity (ohm·m)",
            unit: "(ohm·m)",
            value: res,
            descr: "",
        }
    }
}

export async function fetchWellLog(well) {
    if (USE_MOCK_LOG_DATA) {
        return Promise.resolve(mockFetchWellLog())
    }
    const errorMsg = "Well log lookup is not yet implemented outside of mock mode.";
    throw new Error(errorMsg);
}

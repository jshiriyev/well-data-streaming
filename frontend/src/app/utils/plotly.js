let loadPromise = null;

export async function loadPlotly() {
  if (typeof globalThis !== "undefined" && globalThis.Plotly) {
    return globalThis.Plotly;
  }
  if (!loadPromise) {
    loadPromise = import("plotly.js-dist-min").then((module) => {
      const plotly = module.default ?? module;
      if (typeof globalThis !== "undefined") {
        globalThis.Plotly = plotly;
      }
      return plotly;
    });
  }
  return loadPromise;
}

import { defineStore } from "pinia";

const WORKSPACE_TYPES = [{ id: "golden", label: "Golden Layout" }];

const PLOT_TYPES = [
  {
    id: "archie-log",
    label: "Archie Log (Plotly)",
    componentName: "archie-log",
    getState: () => ({ archie: {} }),
  },
  {
    id: "timeseries",
    label: "Timeseries (Plotly)",
    componentName: "timeseries-plot",
    getState: () => ({ timeseries: {} }),
  },
];

export const useWorkspaceStore = defineStore("workspaces", {
  state: () => ({
    workspaceTypes: WORKSPACE_TYPES,
    plotTypes: PLOT_TYPES,
    workspaceType: WORKSPACE_TYPES[0]?.id || "golden",
    plotType: PLOT_TYPES[0]?.id || "archie-log",
    status: "Ready.",
  }),
  getters: {
    activePlotType: (state) =>
      state.plotTypes.find((plot) => plot.id === state.plotType) || state.plotTypes[0],
  },
  actions: {
    setStatus(text) {
      this.status = text;
    },
  },
});

const DEFAULT_STATE = {
  sidebarOpen: true,
  sidebarWidth: "",
};

function renderTimeseriesSettings({ root } = {}) {
  if (!root) return;
  root.innerHTML = `
    <div class="settings-panel">
      <div class="settings-heading">Timeseries Panel</div>
      <p class="sidebar-note">Use the filters inside the panel to update the data and traces.</p>
    </div>
  `;
}

export const timeseriesSettingsRegistry = {
  "timeseries-plot": renderTimeseriesSettings,
};

export function createTimeseriesState(overrides = {}) {
  return {
    ...DEFAULT_STATE,
    ...overrides,
  };
}

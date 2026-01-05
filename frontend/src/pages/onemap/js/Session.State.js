const SessionState = {
  horizon: "FLD",
  time: "2025-01-01",
  categoricalFilters: {},
  numericFilters: {}, // {porosity: {min: 0.1, max: 0.25}, ...}
};

// Expose a shared mutable state that other scripts (e.g., Marker.Update) can read.
if (typeof window !== "undefined") {
  window.SessionState = window.SessionState || SessionState;
}

// export default SessionState;
export { SessionState };

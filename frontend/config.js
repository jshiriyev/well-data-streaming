(function (global) {
  "use strict";

  function resolveApiBaseUrl() {
    var globalValue = "";
    if (global && (global.API_BASE_URL || global.WELLX_API_BASE_URL)) {
      globalValue = global.API_BASE_URL || global.WELLX_API_BASE_URL || "";
    }

    var metaValue = "";
    if (typeof document !== "undefined") {
      var meta = document.querySelector('meta[name="api-base-url"]');
      if (meta) {
        metaValue = meta.getAttribute("content") || "";
      }
    }

    var raw = String(globalValue || metaValue || "").trim();
    return raw.replace(/\/+$/, "");
  }

  var apiBaseUrl = resolveApiBaseUrl();

  function buildApiUrl(path) {
    if (!apiBaseUrl) return path;
    var normalizedPath = path.charAt(0) === "/" ? path : "/" + path;
    if (apiBaseUrl.endsWith("/api") && normalizedPath.indexOf("/api/") === 0) {
      return apiBaseUrl + normalizedPath.slice(4);
    }
    return apiBaseUrl + normalizedPath;
  }

  var existing = global.WellxConfig || {};
  existing.resolveApiBaseUrl = resolveApiBaseUrl;
  existing.buildApiUrl = buildApiUrl;
  existing.apiBaseUrl = apiBaseUrl;
  global.WellxConfig = existing;
})(typeof window !== "undefined" ? window : globalThis);

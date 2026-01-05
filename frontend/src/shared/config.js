const globalScope = typeof window !== "undefined" ? window : globalThis;

function resolveApiBaseUrl() {
  let globalValue = "";
  if (globalScope && (globalScope.API_BASE_URL || globalScope.WELLX_API_BASE_URL)) {
    globalValue = globalScope.API_BASE_URL || globalScope.WELLX_API_BASE_URL || "";
  }

  let metaValue = "";
  if (typeof document !== "undefined") {
    const meta = document.querySelector('meta[name="api-base-url"]');
    if (meta) {
      metaValue = meta.getAttribute("content") || "";
    }
  }

  const raw = String(globalValue || metaValue || "").trim();
  return raw.replace(/\/+$/, "");
}

const apiBaseUrl = resolveApiBaseUrl();

function buildApiUrl(path) {
  if (!apiBaseUrl) return path;
  const normalizedPath = path.charAt(0) === "/" ? path : `/${path}`;
  if (apiBaseUrl.endsWith("/api") && normalizedPath.startsWith("/api/")) {
    return apiBaseUrl + normalizedPath.slice(4);
  }
  return apiBaseUrl + normalizedPath;
}

const existing = globalScope.WellxConfig || {};
existing.resolveApiBaseUrl = resolveApiBaseUrl;
existing.buildApiUrl = buildApiUrl;
existing.apiBaseUrl = apiBaseUrl;
globalScope.WellxConfig = existing;

export { apiBaseUrl, buildApiUrl, resolveApiBaseUrl };
